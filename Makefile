ifndef WASIX_SYSROOT
	$(error You need to define WASIX_SYSROOT)
endif

CROSSFILE=$(shell pwd)/wasi.meson.cross
SHELL:=/usr/bin/bash

all: numpy-wasix_wasm32.whl

numpy: $(wildcard patches/*.patch) wasi.meson.cross Makefile
	rm -rf numpy
	git restore numpy
	git submodule update --init --recursive
	cd numpy && git am ../patches/*.patch

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
	source ./native-venv/bin/activate && python3 -m crossenv python/tmp/wasix-install/cpython/bin/python3.wasm ./cross-venv --cc 'clang-19 --sysroot='"${WASIX_SYSROOT}"' --target=wasm32-wasix' --cxx 'clang-19 --sysroot='"${WASIX_SYSROOT}"' --target=wasm32-wasix -fPIC'
	source ./cross-venv/bin/activate && python3 -m pip install cython build

numpy-wasix_wasm32.whl: numpy cross-venv wasi.meson.cross
	source ./cross-venv/bin/activate && cd numpy && python3 -m build --wheel -Csetup-args="--cross-file=${CROSSFILE}" -Cbuild-dir=build_np
	cp numpy/dist/*.whl numpy-wasix_wasm32.whl

clean:
	rm -rf python numpy numpy-wasix_wasm32.whl python.webc python.tmp cross-venv native-venv
	git restore numpy
	git submodule update --init --recursive