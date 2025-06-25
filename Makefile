ifndef WASIX_SYSROOT
$(error You need to define WASIX_SYSROOT)
endif

CROSSFILE=$(shell pwd)/wasi.meson.cross
SHELL:=/usr/bin/bash

PWD:=$(shell pwd)

all: numpy-wasix_wasm32.whl

markupsafe: Makefile
	rm -rf markupsafe
	git restore markupsafe
	git submodule update --init --recursive

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

msgpack-python: Makefile
	rm -rf msgpack-python
	git restore msgpack-python
	git submodule update --init --recursive

pycryptodome: Makefile
	rm -rf pycryptodome
	git restore pycryptodome
	git submodule update --init --recursive

pycryptodomex: Makefile
	rm -rf pycryptodomex
	git restore pycryptodomex
	git submodule update --init --recursive
	# If that file exists, pycryptodome will be built with a separate namespace
	touch pycryptodomex/.separate_namespace

zbar: Makefile
	rm -rf zbar
	git restore zbar
	git submodule update --init --recursive zbar

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

pycryptodome_wasm32.whl: pycryptodome cross-venv
	source ./cross-venv/bin/activate && cd pycryptodome && CC=$$(pwd)/../clang.sh CXX=$$(pwd)/../clang.sh python3 -m build --wheel
	cp pycryptodome/dist/*.whl pycryptodome_wasm32.whl

pycryptodomex_wasm32.whl: pycryptodomex cross-venv
	source ./cross-venv/bin/activate && cd pycryptodomex && CC=$$(pwd)/../clang.sh CXX=$$(pwd)/../clang.sh python3 -m build --wheel
	cp pycryptodomex/dist/*.whl pycryptodomex_wasm32.whl

msgpack-python_wasm32.whl: msgpack-python cross-venv
	source ./cross-venv/bin/activate && cd msgpack-python && make cython && python3 -m build --wheel
	cp msgpack-python/dist/*.whl msgpack-python_wasm32.whl

# TODO: Add libjpeg support
libzbar.tar.xz: zbar
	cd zbar && autoreconf -vfi
	cd zbar && ./configure --prefix=/ --libdir=/lib/wasm32-wasi --enable-static --disable-shared --disable-video --disable-rpath --without-imagemagick --without-java --without-qt --without-gtk --without-xv --without-xshm --without-python
	cd zbar && make
	cd zbar && make install DESTDIR=${PWD}/zbar.build
	cd zbar.build && tar cvfJ ../libzbar.tar.xz *

install:
	unzip numpy-wasix_wasm32.whl -d ${INSTALL_DIR}
	unzip markupsafe_wasm32.whl -d ${INSTALL_DIR}
	unzip pytz_wasm32.whl -d ${INSTALL_DIR}
	unzip dateutil_wasm32.whl -d ${INSTALL_DIR}
	unzip pandas_wasm32.whl -d ${INSTALL_DIR}
	unzip six_wasm32.whl -d ${INSTALL_DIR}
	unzip tzdata_wasm32.whl -d ${INSTALL_DIR}
	unzip msgpack-python_wasm32.whl -d ${INSTALL_DIR}
	unzip pycryptodome_wasm32.whl -d ${INSTALL_DIR}
	unzip pycryptodomex_wasm32.whl -d ${INSTALL_DIR}

install-libs: libzbar.tar.xz
	tar xJf libzbar.tar.xz -C ${WASIX_SYSROOT}

clean:
	rm -rf python numpy markupsafe python.webc python cross-venv native-venv *.build
	git restore numpy
	git restore markupsafe
	git restore dateutil
	git restore pandas
	git restore pytz
	git restore six
	git restore tzdata
	git restore msgpack-python
	git restore pycryptodome
	git restore pycryptodomex
	git restore zbar
	git submodule update --init --recursive