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
WHEELS+=pypandoc
WHEELS+=pypandoc_binary
WHEELS+=psycopg
WHEELS+=psycopg-pool
WHEELS+=psycopg-binary
WHEELS+=brotlicffi
WHEELS+=cffi
WHEELS+=pillow

# Libs build a .tar.xz file with a sysroot
LIBS=
LIBS+=zbar
LIBS+=libffi
LIBS+=pandoc
LIBS+=postgresql
LIBS+=brotli
LIBS+=zlib
LIBS+=libjpeg-turbo

DONT_INSTALL=
# Dont install pypandoc because it uses the same name as pypandoc_binary
DONT_INSTALL+=pypandoc

SUBMODULES=$(WHEELS) $(LIBS)

BUILT_WHEELS=$(addsuffix _wasm32.whl,$(WHEELS))
UNPACKED_LIBS=$(addsuffix .build,$(LIBS))
BUILT_LIBS=$(addsuffix .tar.xz,$(LIBS))

# mkdir but resets the timestamp if it didnt exist before
define reset_builddir
bash -c 'rm -rf $$1 ; mkdir $$1 && touch -t 197001010000.00 $$1 || true' .
endef

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
if test -n "${PREPARE}" ; then source ./cross-venv/bin/activate && cd $(word 1, $(subst _wasm32, ,$@)) && _= ${PREPARE} ; fi
source ./cross-venv/bin/activate && cd $(word 1, $(subst _wasm32, ,$@))/${PYPROJECT_PATH} && ${BUILD_ENV_VARS} python3 -m build --wheel ${BUILD_EXTRA_FLAGS}
cp $(word 1, $(subst _wasm32, ,$@))/${PYPROJECT_PATH}/dist/*.whl $@
endef

define package_lib =
cd $(word 1, $(subst ., ,$@)).build && tar cfJ ../$@ *
endef

# Command to run something in an environment with a haskell compiler targeting wasi
# Uses an older hash, because the latest version requires tail call support
RUN_WITH_HASKELL=nix shell 'gitlab:haskell-wasm/ghc-wasm-meta/6a8b8457df83025bed2a8759f5502725a827104b?host=gitlab.haskell.org' --command

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
	source ./cross-venv/bin/activate && build-pip install cffi
	source ./cross-venv/bin/activate && pip install cython build

#####     Preparing submodules     #####

# A target for making sure a submodule is clean
# To override the reset behaviour, add a target for your submodule
$(SUBMODULES): %: #Makefile
$(SUBMODULES): %: %.prepared
%.prepared:
	touch $@
%: %/.git
	$(reset_submodule)

numpy: $(shell find patches -name 'numpy*.patch')

pycryptodomex:
	$(reset_submodule)
	# If that file exists, pycryptodome will be built with a separate namespace
	touch pycryptodomex/.separate_namespace

pypandoc_binary:
	$(reset_submodule)
	# pyproject.toml only works for the non-binary wheel, because they are still moving to pyproject.toml
	mv $@/setup_binary.py $@/setup.py
	rm $@/pyproject.toml
	# The pandoc binary also needs to be copied, but we do that in the build step

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

psycopg_wasm32.whl: PYPROJECT_PATH = psycopg
psycopg-pool_wasm32.whl: PYPROJECT_PATH = psycopg_pool

psycopg-binary_wasm32.whl: PYPROJECT_PATH = psycopg_binary
psycopg-binary_wasm32.whl: PREPARE = rm -rf psycopg_binary && python3 tools/build/copy_to_binary.py
# Inject a mock pg_config to the PATH, so the build process can find it
psycopg-binary_wasm32.whl: BUILD_ENV_VARS = PATH="${PWD}/resources:$$PATH"
# Pretend we are a normal posix-like target, so we automatically include <endian.h>
psycopg-binary_wasm32.whl: export CCC_OVERRIDE_OPTIONS = ^-D__linux__=1

pillow_wasm32.whl: BUILD_ENV_VARS = PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig
pillow_wasm32.whl: BUILD_EXTRA_FLAGS = -Cplatform-guessing=disable

# Build the tzdb locally
pytz_wasm32.whl: PREPARE = CCC_OVERRIDE_OPTIONS='^--target=x86_64-unknown-linux' CC=clang CXX=clang++ make build

# Needs to run a cython command before building the wheel	
msgpack-python_wasm32.whl: PREPARE = make cython

# Depends on a meson crossfile
numpy_wasm32.whl: BUILD_EXTRA_FLAGS = -Csetup-args="--cross-file=${CROSSFILE}"
numpy_wasm32.whl: ${CROSSFILE}

# Needs to have the pypandoc executable in the repo
pypandoc_binary_wasm32.whl: pypandoc_binary/pypandoc/files/pandoc
pypandoc_binary/pypandoc/files/pandoc: pypandoc_binary pandoc.tar.xz
	mkdir -p pypandoc_binary/pypandoc/files
	tar xfJ pandoc.tar.xz -C pypandoc_binary/pypandoc/files --strip-components=1 bin/pandoc
	touch $@

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
	cd zbar && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --enable-static --enable-shared --disable-video --disable-rpath --without-imagemagick --without-java --without-qt --without-gtk --without-xv --without-xshm --without-python
	cd zbar && make
	$(reset_builddir) $@
	cd zbar && make install DESTDIR=${PWD}/zbar.build
	touch $@

libffi.build: libffi
	cd libffi && autoreconf -vfi
	cd libffi && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --host="wasm32-wasi" --enable-static --disable-shared --disable-dependency-tracking --disable-builddir --disable-multi-os-directory --disable-raw-api --disable-docs
	cd libffi && make
	$(reset_builddir) $@
	cd libffi && make install DESTDIR=${PWD}/libffi.build
	touch $@

zlib.build: zlib
	cd zlib && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd zlib && make
	$(reset_builddir) $@
	cd zlib && make install DESTDIR=${PWD}/zlib.build
	touch $@

pandoc.build: pandoc
	cd pandoc && ${RUN_WITH_HASKELL} wasm32-wasi-cabal update
	cd pandoc && ${RUN_WITH_HASKELL} wasm32-wasi-cabal build pandoc-cli
	# Most of these options are copied from https://github.com/tweag/pandoc-wasm/blob/master/.github/workflows/build.yml
	wasm-opt --experimental-new-eh --low-memory-unused --converge --gufa --flatten --rereloop -Oz $$(find pandoc -type f -name pandoc.wasm) -o pandoc/pandoc.opt.wasm
	$(reset_builddir) $@
	mkdir -p $@/bin
	install -m 755 pandoc/pandoc.opt.wasm $@/bin/pandoc
	touch $@

postgresql.build: postgresql
	cd postgresql && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --without-icu --without-zlib --without-readline
	cd postgresql && make MAKELEVEL=0 -C src/interfaces
	cd postgresql && make MAKELEVEL=0 -C src/include
	$(reset_builddir) $@
	cd postgresql && make MAKELEVEL=0 -C src/interfaces install DESTDIR=${PWD}/$@
	cd postgresql && make MAKELEVEL=0 -C src/include install DESTDIR=${PWD}/$@
	touch $@

brotli.build: brotli
	cd brotli && rm -rf out
	cd brotli && cmake -DCMAKE_BUILD_TYPE=Release -B out -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
# Brotli always tries to build the executable (which we dont need), which imports `chown` and `clock`, which we don't provide.
# This workaround makes that work during linking, but it is not a proper solution.
# CCC_OVERRIDE_OPTIONS should not be set during cmake setup, because it will erroneously detect emscripten otherwise.
# TODO: Implement chown in wasix and unset CCC_OVERRIDE_OPTIONS
	cd brotli && CCC_OVERRIDE_OPTIONS='^-Wl,--unresolved-symbols=import-dynamic' make -C out
	$(reset_builddir) $@
	cd brotli && CCC_OVERRIDE_OPTIONS='^-Wl,--unresolved-symbols=import-dynamic' make -C out install DESTDIR=${PWD}/$@
	touch $@

libjpeg-turbo.build: libjpeg-turbo
	cd libjpeg-turbo && rm -rf out
	# They use a custom version of GNUInstallDirs.cmake does not support libdir starting with prefix.
	# TODO: Add a sed command to fix that
	cd libjpeg-turbo && cmake -DCMAKE_BUILD_TYPE=Release -B out -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd libjpeg-turbo && make -C out
	$(reset_builddir) $@
	cd libjpeg-turbo && make -C out install DESTDIR=${PWD}/$@
	touch $@

#####     Installing wheels and libs     #####

# Use `install` to install everything
# Use `install-SUBMODULE` to install a specific submodule
# Use `install-wheels` to install all wheels
# Use `install-libs` to install all libs

ALL_INSTALLED_WHEELS=$(addprefix ${INSTALL_DIR}/.,$(addsuffix .installed,$(filter-out $(DONT_INSTALL),$(WHEELS))))
ALL_INSTALLED_LIBS=$(addprefix ${WASIX_SYSROOT}/.,$(addsuffix .installed,$(filter-out $(DONT_INSTALL),$(LIBS))))

${WASIX_SYSROOT}/.%.installed: %.tar.xz
	test -n "${WASIX_SYSROOT}" || (echo "You must set WASIX_SYSROOT to your wasix sysroot" && exit 1)
	tar mxJf $< -C ${WASIX_SYSROOT}
	touch $@

${INSTALL_DIR}/.%.installed: %_wasm32.whl
	test -n "${INSTALL_DIR}" || (echo "You must set INSTALL_DIR to the python library path" && exit 1)
	unzip -oq $< -d ${INSTALL_DIR}
	touch $@

install: install-wheels install-libs
install-wheels: $(ALL_INSTALLED_WHEELS)
install-libs: $(ALL_INSTALLED_LIBS)

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