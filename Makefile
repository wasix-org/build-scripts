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
# WHEELS+=pytz
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
cd $@ && git am --abort >/dev/null 2>&1 || true
cd $@ && find ../patches -name '$@*.patch'  -exec git am {} \;
endef

define build_wheel =
source ./cross-venv/bin/activate && cd $(word 1, $(subst _, ,$@)) && python3 -m build --wheel
cp $(word 1, $(subst _, ,$@))/dist/*.whl $@
endef

define package_lib =
cd $(word 1, $(subst ., ,$@)).build && tar cfJ ../$@ *
endef

all: $(BUILT_WHEELS)

# Targets for preparing a wasm crossenv
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

pyzbar_wasm32.whl: ${WASIX_SYSROOT}/lib/wasm32-wasi/libzbar.a

pytz_wasm32.whl:
	source ./cross-venv/bin/activate && cd pytz && make build
	$(build_wheel)

msgpack-python_wasm32.whl: msgpack-python cross-venv
	source ./cross-venv/bin/activate && cd msgpack-python && make cython
	$(build_wheel)

numpy_wasm32.whl: wasi.meson.cross
	source ./cross-venv/bin/activate && cd numpy && python3 -m build --wheel -Csetup-args="--cross-file=${CROSSFILE}" -Cbuild-dir=build_np
	cp numpy/dist/*.whl numpy_wasm32.whl

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