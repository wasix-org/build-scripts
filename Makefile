ifndef WASIX_SYSROOT
$(error You need to define WASIX_SYSROOT)
endif

CROSSFILE=$(shell pwd)/wasi.meson.cross
SHELL:=/usr/bin/bash

PWD:=$(shell pwd)

all: numpy-wasix_wasm32.whl

# Wheels build a .whl file
WHEELS=
WHEELS+=numpy
WHEELS+=pytz
WHEELS+=markupsafe
# Not a native package at all
WHEELS+=dateutil
# Technically not a native package, but it uses a native build process to prepare some files.
WHEELS+=tzdata
# WHEELS+=pandas
WHEELS+=six
WHEELS+=msgpack-python
WHEELS+=pycryptodome
WHEELS+=pycryptodomex
WHEELS+=pyzbar
WHEELS+=cython

# Libs build a .tar.xz file with a sysroot
LIBS=
LIBS+=zbar
LIBS+=libffi

SUBMODULES=$(WHEELS) $(LIBS)

BUILT_WHEELS=$(addsuffix _wasm32.whl,$(WHEELS))
UNPACKED_LIBS=$(addsuffix .build,$(LIBS))
BUILT_LIBS=$(addsuffix .tar.xz,$(LIBS))

define reset_submodule =
rm -rf $@
git restore $@
git submodule update --init --recursive $@
cd $@ && make clean >/dev/null 2>&1 || true
cd $@ && git am --abort >/dev/null 2>&1 || true
cd $@ && find ../patches -name '$@*.patch'  -exec git am {} \;
endef

# Customizable build script
# PYPROJECT_PATH is the path to the pyproject.toml relative to the submodule. Defaults to the submodule which is usually correct
# BUILD_ENV_VARS is a space separated list of environment variables to pass to the build script. Defaults to empty
# BUILD_EXTRA_FLAGS is a space separated list of extra flags to pass to the build script. Defaults to empty
# PREPARE is a command to run before building the wheel. Defaults to empty. Runs inside the submodule directory
define build_wheel =
if test -n "${PREPARE}" ; then source ./cross-venv/bin/activate && cd $(word 1, $(subst _, ,$@)) && _= ${PREPARE} ; fi
source ./cross-venv/bin/activate && cd $(word 1, $(subst _, ,$@))/${PYPROJECT_PATH} && ${BUILD_ENV_VARS} python3 -m build --wheel ${BUILD_EXTRA_FLAGS}
cp $(word 1, $(subst _, ,$@))/${PYPROJECT_PATH}/dist/*.whl $@
endef

define package_lib =
cd $(word 1, $(subst ., ,$@)).build && tar cfJ ../$@ *
endef

all: $(BUILT_WHEELS)

# Targets for preparing a wasm crossenv
python.webc:
	wasmer package download zebreus/numpython -o python.webc
	touch python.webc
python: python.webc
	wasmer package unpack python.webc --out-dir python
	cp python/modules/python python/artifacts/wasix-install/cpython/bin/python3.wasm
	touch python
native-venv:
	python3 -m venv ./native-venv
	source ./native-venv/bin/activate && pip install crossenv
cross-venv: native-venv python
	rm -rf ./cross-venv
	source ./native-venv/bin/activate && python3 -m crossenv python/artifacts/wasix-install/cpython/bin/python3.wasm ./cross-venv --cc wasix-clang --cxx wasix-clang++
	source ./cross-venv/bin/activate && python3 -m pip install cython build

#####     Preparing submodules     #####

# A target for making sure a submodule is clean
# To override the reset behaviour, add a target for your submodule
$(SUBMODULES): %: #Makefile
%: %/.git
	$(reset_submodule)

numpy: $(shell find patches -name 'numpy*.patch')

pycryptodomex:
	$(reset_submodule)
	# If that file exists, pycryptodome will be built with a separate namespace
	touch pycryptodomex/.separate_namespace

#####     Building wheels     #####

# A target to build a wheel from a python submodule
# To override the build behaviour, add a target for your submodule
$(BUILT_WHEELS): %_wasm32.whl: % cross-venv
%_wasm32.whl: %
	$(build_wheel)

# Depends on zbar headers being installed
pyzbar_wasm32.whl: ${WASIX_SYSROOT}/lib/wasm32-wasi/libzbar.a

# setup.py is not in the root directory
pytz_wasm32.whl: PYPROJECT_PATH = src

# Build the tzdb locally
pytz_wasm32.whl: PREPARE = CCC_OVERRIDE_OPTIONS='^--target=x86_64-unknown-linux' CC=clang CXX=clang++ make build

# Needs to run a cython command before building the wheel	
msgpack-python_wasm32.whl: PREPARE = make cython

# Depends on a meson crossfile
numpy_wasm32.whl: EXTRA_BUILD_FLAGS = -Csetup-args="--cross-file=${CROSSFILE}"
numpy_wasm32.whl: ${CROSSFILE}

# Currently broken, because numpy is missing. The binary in the repo is build manually.
# Build pandas manually by compiling a native numpy and extracting the wheel into the cross env
pandas_wasm32.whl: pandas cross-venv
	source ./cross-venv/bin/activate && cd pandas && CC=$$(pwd)/../clang.sh CXX=$$(pwd)/../clang++.sh python3 -m build --wheel -Csetup-args="--cross-file=${CROSSFILE}" -Cbuild-dir=build_np
	cp pandas/dist/*.whl pandas_wasm32.whl

#####     Building libraries     #####

$(UNPACKED_LIBS): %.build: %
$(BUILT_LIBS): %.tar.xz: %.build
%.build: %
	echo "Missing build script for $@" >&2 && exit 1
%.tar.xz: %.build
	$(package_lib)
	touch $@

# TODO: Add libjpeg support
zbar.build: zbar
	cd zbar && autoreconf -vfi
	# Force configure to build shared libraries. This is a hack, but it works.
	cd zbar && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd zbar && ./configure --prefix=/ --libdir=/lib/wasm32-wasi --enable-static --enable-shared --disable-video --disable-rpath --without-imagemagick --without-java --without-qt --without-gtk --without-xv --without-xshm --without-python
	cd zbar && make
	cd zbar && make install DESTDIR=${PWD}/zbar.build
	touch $@

libffi.build: libffi
	cd libffi && autoreconf -vfi
	cd libffi && ./configure --prefix=/ --libdir=/lib/wasm32-wasi --host="wasm32-wasi" --enable-static --disable-shared --disable-dependency-tracking --disable-builddir --disable-multi-os-directory --disable-raw-api --disable-docs
	cd libffi && make
	cd libffi && make install DESTDIR=${PWD}/libffi.build
	touch $@

INSTALLED_WHEELS=$(addprefix ${INSTALL_DIR}/.,$(addsuffix .installed,$(WHEELS)))
INSTALLED_LIBS=$(addprefix ${WASIX_SYSROOT}/.,$(addsuffix .installed,$(LIBS)))

${WASIX_SYSROOT}/.%.installed: %.tar.xz
	test -n "${WASIX_SYSROOT}" || (echo "You must set WASIX_SYSROOT to your wasix sysroot" && exit 1)
	tar mxJf $< -C ${WASIX_SYSROOT}
	touch $@

${INSTALL_DIR}/.%.installed: %_wasm32.whl
	test -n "${INSTALL_DIR}" || (echo "You must set INSTALL_DIR to the python library path" && exit 1)
	unzip -oq $< -d ${INSTALL_DIR}
	touch $@

install: install-wheels install-libs
install-wheels: $(INSTALLED_WHEELS)
install-libs: $(INSTALLED_LIBS)

INSTALL_WHEELS_TARGETS=$(addprefix install-,$(WHEELS))
INSTALL_LIBS_TARGETS=$(addprefix install-,$(LIBS))
$(INSTALL_WHEELS_TARGETS): install-%: ${INSTALL_DIR}/.%.installed
$(INSTALL_LIBS_TARGETS): install-%: ${WASIX_SYSROOT}/.%.installed

clean: $(SUBMODULES)
	rm -rf python python.webc
	rm -rf cross-venv native-venv
	rm -rf *.build

.PRECIOUS: $(WHEELS) $(LIBS) $(UNPACKED_LIBS) $(BUILT_LIBS) $(BUILT_WHEELS)
.PHONY: install install-wheels install-libs $(INSTALL_WHEELS_TARGETS) $(INSTALL_LIBS_TARGETS) clean 