ifndef WASIX_SYSROOT
$(error You need to define WASIX_SYSROOT)
endif

CROSSFILE=$(shell pwd)/wasi.meson.cross
SHELL:=/usr/bin/bash

PWD:=$(shell pwd)
PYTHON_WASIX_BINARIES:=$(PWD)/../python-wasix-binaries

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
WHEELS+=uvloop
WHEELS+=mysqlclient
WHEELS+=python-qrcode
WHEELS+=pycparser
WHEELS+=pydantic
WHEELS+=typing_extensions
WHEELS+=typing-inspection
WHEELS+=annotated-types

PYTHON_WASIX_BINARIES_WHEELS=
PYTHON_WASIX_BINARIES_WHEELS+=mysqlclient-2.2.7-cp313-cp313-wasix_wasm32
# PYTHON_WASIX_BINARIES_WHEELS+=cffi-1.17.1-cp313-cp313-wasix_wasm32
PYTHON_WASIX_BINARIES_WHEELS+=cryptography-45.0.4-cp313-abi3-any
PYTHON_WASIX_BINARIES_WHEELS+=pydantic_core-2.33.2-cp313-cp313-any
PYTHON_WASIX_BINARIES_WHEELS+=jiter-0.10.0-cp313-cp313-any
PYTHON_WASIX_BINARIES_WHEELS+=lxml-6.0.0-cp313-cp313-wasix_wasm32
PYTHON_WASIX_BINARIES_WHEELS+=rpds_py-0.26.0-cp313-cp313-any

# Libs build a .tar.xz file with a sysroot
LIBS=
LIBS+=zbar
LIBS+=libffi
LIBS+=pandoc
LIBS+=postgresql
LIBS+=brotli
LIBS+=zlib
LIBS+=libjpeg-turbo
LIBS+=xz
LIBS+=libtiff
LIBS+=libwebp
LIBS+=giflib
LIBS+=libpng
LIBS+=SDL3
LIBS+=openjpeg
LIBS+=libuv
LIBS+=mariadb-connector-c
LIBS+=openssl

DONT_INSTALL=
# Dont install pypandoc because it uses the same name as pypandoc_binary
DONT_INSTALL+=pypandoc
DONT_INSTALL+=mysqlclient
DONT_INSTALL+=psycopg-binary

SUBMODULES=$(WHEELS) $(LIBS)

BUILT_WHEELS=$(addsuffix _wasm32.whl,$(WHEELS))
UNPACKED_LIBS=$(addsuffix .build,$(LIBS))
BUILT_LIBS=$(addsuffix .tar.xz,$(LIBS))

WHEELS_TO_INSTALL=$(filter-out $(DONT_INSTALL),$(WHEELS))
PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL=$(filter-out $(DONT_INSTALL),$(PYTHON_WASIX_BINARIES_WHEELS))
LIBS_TO_INSTALL=$(filter-out $(DONT_INSTALL),$(LIBS))

BUILT_WHEELS_TO_INSTALL=$(addsuffix _wasm32.whl,$(WHEELS_TO_INSTALL))
BUILT_PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL=$(addprefix ${PYTHON_WASIX_BINARIES}/wheels/,$(addsuffix .whl,$(PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL)))
BUILT_LIBS_TO_INSTALL=$(addsuffix .tar.xz,$(LIBS_TO_INSTALL))

ALL_INSTALLED_WHEELS=$(addprefix ${INSTALL_DIR}/.,$(addsuffix .installed,$(WHEELS_TO_INSTALL)))
ALL_INSTALLED_WHEELS+=$(addprefix ${INSTALL_DIR}/.pwb-,$(addsuffix .installed,$(filter-out $(DONT_INSTALL),$(PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL))))
ALL_INSTALLED_LIBS=$(addprefix ${WASIX_SYSROOT}/.,$(addsuffix .installed,$(LIBS_TO_INSTALL)))

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
cd $@ && find ../patches -name '$@*.patch' | sort | xargs -n1 git am
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

all: $(BUILT_LIBS_TO_INSTALL) $(BUILT_WHEELS_TO_INSTALL) $(BUILT_PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL)

#####     Downloading and uploading the python webc     #####

PYTHON_WEBC=zebreus/python
PYTHON_WITH_PACKAGES_WEBC=zebreus/python-with-packages

python.webc python.version:
	wasmer package download $(PYTHON_WEBC) -o python.webc
	touch python.webc
python: python.webc
	wasmer package unpack python.webc --out-dir python
	cp python/modules/python python/artifacts/wasix-install/cpython/bin/python3.wasm
	touch python
python-with-packages: python postgresql.build zbar.build libjpeg-turbo.build $(BUILT_WHEELS_TO_INSTALL) $(BUILT_PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL)
	### Prepare a python release with all the deps
	# Copy the base python package
	rm -rf python-with-packages
	cp -r python python-with-packages

	# Install the wheels
	INSTALL_DIR=$(PWD)/python-with-packages/artifacts/wasix-install/cpython/lib/python3.13 make install-wheels

	# Install the libs
	mkdir -p python-with-packages/artifacts/wasix-install/lib
	cp -L $(PWD)/postgresql.build/usr/local/lib/wasm32-wasi/*.so* python-with-packages/artifacts/wasix-install/lib
	cp -L $(PWD)/zbar.build/usr/local/lib/wasm32-wasi/libzbar.so* python-with-packages/artifacts/wasix-install/lib
	cp -L $(PWD)/libjpeg-turbo.build/usr/local/lib/wasm32-wasi/libjpeg.so* python-with-packages/artifacts/wasix-install/lib

	# Copy the python-wasix-binaries wheels (tomlq is provided in the yq package (but only in the python implementation))
	tomlq -i '.package.name = "$(PYTHON_WITH_PACKAGES_WEBC)"' python-with-packages/wasmer.toml --output-format toml
	tomlq -i '.fs."/lib" = "./artifacts/wasix-install/lib"' python-with-packages/wasmer.toml --output-format toml
	tomlq -i '.module[0]."source" = "./artifacts/wasix-install/cpython/bin/python3.wasm"' python-with-packages/wasmer.toml --output-format toml

	echo 'Build python-with-packages'
	echo 'To test it run: `bash run-tests.sh`'
	echo 'To publish it run: `wasmer package publish python-with-packages`' 

#####     Preparing a wasm crossenv     #####

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
%: | %/.git
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
$(BUILT_WHEELS): %_wasm32.whl: % | cross-venv
%_wasm32.whl: %
	$(build_wheel)

# Depends on zbar headers being installed
# setup.py is not in the root directory
pytz_wasm32.whl: PYPROJECT_PATH = build/dist
# Build the tzdb locally
pytz_wasm32.whl: PREPARE = CCC_OVERRIDE_OPTIONS='^--target=x86_64-unknown-linux' CC=clang CXX=clang++ make build

psycopg_wasm32.whl: PYPROJECT_PATH = psycopg
psycopg-pool_wasm32.whl: PYPROJECT_PATH = psycopg_pool

psycopg-binary_wasm32.whl: PYPROJECT_PATH = psycopg_binary
psycopg-binary_wasm32.whl: PREPARE = rm -rf psycopg_binary && python3 tools/build/copy_to_binary.py
# Inject a mock pg_config to the PATH, so the build process can find it
psycopg-binary_wasm32.whl: BUILD_ENV_VARS = PATH="${PWD}/resources:$$PATH" WASIX_FORCE_STATIC_DEPENDENCIES=true
# Pretend we are a normal posix-like target, so we automatically include <endian.h>
psycopg-binary_wasm32.whl: export CCC_OVERRIDE_OPTIONS = ^-D__linux__=1

pillow_wasm32.whl: BUILD_ENV_VARS = PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig WASIX_FORCE_STATIC_DEPENDENCIES=true
pillow_wasm32.whl: BUILD_EXTRA_FLAGS = -Cplatform-guessing=disable



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

uvloop_wasm32.whl: BUILD_ENV_VARS = WASIX_FORCE_STATIC_DEPENDENCIES=true
uvloop_wasm32.whl: BUILD_EXTRA_FLAGS = '-C--build-option=build_ext --use-system-libuv'

mysqlclient_wasm32.whl: BUILD_ENV_VARS = PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig

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

xz.build: xz
	cd xz && bash autogen.sh
	# Force configure to build shared libraries. This is a hack, but it works.
	cd xz && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd xz && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --disable-xz --disable-symbol-versions
	cd xz && make
	$(reset_builddir) $@
	cd xz && make install DESTDIR=${PWD}/xz.build
	touch $@

libtiff.build: libtiff
	cd libtiff && bash autogen.sh
	# Force configure to build shared libraries. This is a hack, but it works.
	cd libtiff && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd libtiff && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd libtiff && make
	$(reset_builddir) $@
	cd libtiff && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig make install DESTDIR=${PWD}/libtiff.build
	touch $@

libwebp.build: libwebp
	cd libwebp && bash autogen.sh
	# Force configure to build shared libraries. This is a hack, but it works.
	cd libwebp && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd libwebp && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd libwebp && make
	$(reset_builddir) $@
	cd libwebp && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig make install DESTDIR=${PWD}/libwebp.build
	touch $@

giflib.build: giflib resources/giflib.pc
	cd giflib && make
	$(reset_builddir) $@
	cd giflib && make install PREFIX=/usr/local LIBDIR=/usr/local/lib/wasm32-wasi DESTDIR=${PWD}/giflib.build
	# giflib does not include a pkg-config file, so we need to install it manually. We need to bump the version in that file as well, when we update the version
	install -Dm644 ${PWD}/resources/giflib.pc ${PWD}/libwebp.build/usr/local/lib/wasm32-wasi/pkgconfig/giflib.pc
	touch $@

libpng.build: libpng
	# Force configure to build shared libraries. This is a hack, but it works.
	cd libpng && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd libpng && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd libpng && make
	$(reset_builddir) $@
	cd libpng && make install DESTDIR=${PWD}/libpng.build
	touch $@

SDL3.build: SDL3
	cd SDL3 && cmake . -DSDL_UNIX_CONSOLE_BUILD=ON -DSDL_RENDER_GPU=OFF -DSDL_VIDEO=OFF -DSDL_AUDIO=OFF -DSDL_JOYSTICK=OFF -DSDL_HAPTIC=OFF -DSDL_HIDAPI=OFF -DSDL_SENSOR=OFF -DSDL_POWER=OFF -DSDL_DIALOG=OFF -DSDL_STATIC=ON -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd SDL3 && make
	$(reset_builddir) $@
	cd SDL3 && make install DESTDIR=${PWD}/SDL3.build
	touch $@

openjpeg.build: openjpeg
	cd openjpeg && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig cmake . -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd openjpeg && make
	$(reset_builddir) $@
	cd openjpeg && make install DESTDIR=${PWD}/openjpeg.build
	touch $@

libuv.build: libuv
	cd libuv && rm -rf out
	cd libuv && cmake -B out -DLIBUV_BUILD_TESTS=OFF -DCMAKE_SYSTEM_NAME=WASI -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd libuv && make -C out
	$(reset_builddir) $@
	cd libuv && make -C out install DESTDIR=${PWD}/$@
	touch $@

# TODO: Improve, after openssl is building
mariadb-connector-c.build: mariadb-connector-c
	# cd mariadb-connector-c && rm -rf out
	cd mariadb-connector-c && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig cmake -B out \
	 -DCMAKE_SYSTEM_NAME=WASI \
	 -DOPENSSL_INCLUDE_DIR=${WASIX_SYSROOT}/usr/local/include \
	 -DOPENSSL_SSL_LIBRARY=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/libcrypto.a \
	 -DOPENSSL_CRYPTO_LIBRARY=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/libcrypto.a \
	 -DZLIB_INCLUDE_DIR=${WASIX_SYSROOT}/usr/local/include \
	 -DZLIB_LIBRARY=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/libz.a \
	 -DWITH_MYSQLCOMPAT=ON \
	 -DCLIENT_PLUGIN_DIALOG=static \
     -DCLIENT_PLUGIN_SHA256_PASSWORD=static \
     -DCLIENT_PLUGIN_CACHING_SHA2_PASSWORD=static \
     -DCLIENT_PLUGIN_CLIENT_ED25519=static \
     -DCLIENT_PLUGIN_PARSEC=static \
     -DCLIENT_PLUGIN_MYSQL_CLEAR_PASSWORD=static \
	 -DWITH_EXTERNAL_ZLIB=ON \
	 -DWITH_UNIT_TESTS=OFF \
	 -DCMAKE_BUILD_TYPE=Release \
	 -DINSTALL_INCLUDEDIR='include' \
	 -DINSTALL_LIBDIR='lib/wasm32-wasi' \
	 -DINSTALL_PCDIR='lib/wasm32-wasi/pkgconfig'
	cd mariadb-connector-c && make -j16 -C out
	$(reset_builddir) $@
	cd mariadb-connector-c && make -j16 -C out install DESTDIR=${PWD}/$@
	cd ${PWD}/$@/usr/local/lib/wasm32-wasi/pkgconfig && sed -i "s|${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi|\$${libdir}|g" libmariadb.pc
	cd ${PWD}/$@/usr/local/lib/wasm32-wasi/pkgconfig && sed "s|libmariadb|libmysql|g" libmariadb.pc > libmysql.pc
	cd ${PWD}/$@/usr/local/lib/wasm32-wasi && ln -s libmariadbclient.a ./libmysqlclient.a
	cd ${PWD}/$@/usr/local/lib/wasm32-wasi && ln -s libmariadb.so ./libmysql.so
	touch ${PWD}/$@/usr/local/lib/wasm32-wasi

openssl.build: openssl
	# Options adapted from https://github.com/wasix-org/openssl/commit/52cc90976bea2e4f224250ef72cfa992c42bf410
	# Add no-pic to disable PIC
	cd openssl && ./Configure no-asm no-tests no-apps no-afalgeng no-dgram no-secure-memory --prefix /usr/local --libdir=lib/wasm32-wasi
	cd openssl && make -j8
	$(reset_builddir) $@
	cd openssl && make install_sw DESTDIR=${PWD}/$@
	touch $@
#####     Installing wheels and libs     #####

# Use `install` to install everything
# Use `install-SUBMODULE` to install a specific submodule
# Use `install-wheels` to install all wheels
# Use `install-libs` to install all libs


${WASIX_SYSROOT}/.%.installed: %.tar.xz
	test -n "${WASIX_SYSROOT}" || (echo "You must set WASIX_SYSROOT to your wasix sysroot" && exit 1)
	tar mxJf $< -C ${WASIX_SYSROOT}
	touch $@

${INSTALL_DIR}/.%.installed: %_wasm32.whl
	test -n "${INSTALL_DIR}" || (echo "You must set INSTALL_DIR to the python library path" && exit 1)
	unzip -oq $< -d ${INSTALL_DIR}
	touch $@

${INSTALL_DIR}/.pwb-%.installed: ${PYTHON_WASIX_BINARIES}/wheels/%.whl
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
# Install a wheel from python-wasix-binaries
INSTALL_PYTHON_WASIX_BINARIES_WHEELS_TARGETS=$(addprefix install-pwb-,$(PYTHON_WASIX_BINARIES_WHEELS))
$(INSTALL_PYTHON_WASIX_BINARIES_WHEELS_TARGETS): install-pwb-%: ${INSTALL_DIR}/.pwb-%.installed

clean: $(SUBMODULES)
	rm -rf python python.webc
	rm -rf cross-venv native-venv
	rm -rf *.build

.PRECIOUS: $(WHEELS) $(LIBS) $(UNPACKED_LIBS) $(BUILT_LIBS) $(BUILT_WHEELS)
.PHONY: install install-wheels install-libs $(INSTALL_WHEELS_TARGETS) $(INSTALL_LIBS_TARGETS) clean 