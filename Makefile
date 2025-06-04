ifndef WASIX_SYSROOT
$(error You need to define WASIX_SYSROOT)
endif

CROSSFILE=$(shell pwd)/wasi.meson.cross
SHELL:=/usr/bin/bash

all: numpy-wasix_wasm32.whl

markupsafe: Makefile
	rm -rf markupsafe
	git restore markupsafe
	git submodule update --init --recursive
# cd numpy && git am ../patches/*.patch

numpy: $(wildcard patches/*.patch) wasi.meson.cross Makefile
	rm -rf numpy
	git restore numpy
	git submodule update --init --recursive
	cd numpy && git am ../patches/*.patch

pytz: Makefile
	rm -rf pytz
	git restore pytz
	git submodule update --init --recursive

dateutil: Makefile
	rm -rf dateutil
	git restore dateutil
	git submodule update --init --recursive

tzdata: Makefile
	rm -rf tzdata
	git restore tzdata
	git submodule update --init --recursive

pandas: Makefile wasi.meson.cross
	rm -rf pandas
	git restore pandas
	git submodule update --init --recursive

six: Makefile wasi.meson.cross
	rm -rf six
	git restore six
	git submodule update --init --recursive

python.webc:
	wasmer package download wasmer/python-ehpic -o python.webc
	touch python.webc

python: python.webc
	wasmer package unpack python.webc --out-dir python
	touch python

native-venv:
	python3 -m venv ./native-venv
	source ./native-venv/bin/activate && pip install crossenv

cross-venv: native-venv python
	rm -rf ./cross-venv
	source ./native-venv/bin/activate && python3 -m crossenv python/tmp/wasix-install/cpython/bin/python3.wasm ./cross-venv --cc $$(pwd)'/clang.sh' --cxx $$(pwd)'/clang++.sh'
	source ./cross-venv/bin/activate && python3 -m pip install cython build

numpy-wasix_wasm32.whl: numpy cross-venv wasi.meson.cross
	source ./cross-venv/bin/activate && cd numpy && python3 -m build --wheel -Csetup-args="--cross-file=${CROSSFILE}" -Cbuild-dir=build_np
	cp numpy/dist/*.whl numpy-wasix_wasm32.whl

markupsafe_wasm32.whl: markupsafe cross-venv
	source ./cross-venv/bin/activate && cd markupsafe && python3 -m build --wheel
	cp markupsafe/dist/*.whl markupsafe_wasm32.whl

# Technically not a native package, but it uses a native build process to prepare some files.
pytz_wasm32.whl: pytz cross-venv
	source ./cross-venv/bin/activate && cd pytz && make build
	source ./cross-venv/bin/activate && cd pytz/src && python3 -m build --wheel
	cp pytz/src/dist/*.whl pytz_wasm32.whl

# Not a native package at all
dateutil_wasm32.whl: dateutil cross-venv
	source ./cross-venv/bin/activate && cd dateutil && python3 -m build --wheel
	cp dateutil/dist/*.whl dateutil_wasm32.whl

tzdata_wasm32.whl: tzdata cross-venv
	source ./cross-venv/bin/activate && cd tzdata && python3 -m build --wheel
	cp tzdata/dist/*.whl tzdata_wasm32.whl

# Currently broken, because numpy is missing. The binary in the repo is build manually.
# Build pandas manually by compiling a native numpy and extracting the wheel into the cross env
pandas_wasm32.whl: pandas cross-venv
	source ./cross-venv/bin/activate && cd pandas && CC=$$(pwd)/../clang.sh CXX=$$(pwd)/../clang++.sh python3 -m build --wheel -Csetup-args="--cross-file=${CROSSFILE}" -Cbuild-dir=build_np
	cp pandas/dist/*.whl pandas_wasm32.whl

six_wasm32.whl: six cross-venv
	source ./cross-venv/bin/activate && cd six && python3 -m build --wheel
	cp six/dist/*.whl six_wasm32.whl

clean:
	rm -rf python numpy markupsafe numpy-wasix_wasm32.whl markupsafe_wasm32.whl python.webc python cross-venv native-venv
	git restore numpy
	git restore markupsafe
	git submodule update --init --recursive