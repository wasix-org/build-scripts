ifndef WASIX_SYSROOT
$(error You need to define WASIX_SYSROOT)
endif

SHELL:=/usr/bin/bash

PWD:=$(shell pwd)
PYTHON_WASIX_BINARIES:=$(PWD)/../python-wasix-binaries
MESON_CROSSFILE=$(shell pwd)/resources/wasi.meson.cross
BAZEL_TOOLCHAIN=$(shell pwd)/resources/bazel-toolchain

# Wheels build a .whl file
WHEELS=
WHEELS+=numpy
WHEELS+=pytz
WHEELS+=markupsafe
# Not a native package at all
WHEELS+=dateutil
# Technically not a native package, but it uses a native build process to prepare some files.
WHEELS+=tzdata
WHEELS+=pandas
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
WHEELS+=shapely
WHEELS+=regex
WHEELS+=lxml
WHEELS+=protobuf
WHEELS+=numpy1

#####     List of all wheel in python-wasix-binaries with reasons for inclusion in here     #####
PYTHON_WASIX_BINARIES_WHEELS=

# Included: Not moved to build-scripts yet
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=aiohttp-3.12.4-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=cffi-1.17.1-cp313-cp313-wasix_wasm32.whl
# Included: Rust
PYTHON_WASIX_BINARIES_WHEELS+=cryptography-45.0.4-cp313-abi3-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=dateutil-cp313-cp313-wasix_wasm32.whl
# Included: Not moved to build-scripts yet
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=ddtrace-3.10.2-cp313-cp313-wasix_wasm32.whl
# Included: Not moved to build-scripts yet
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=google_crc32c-1.7.1-py3-none-any.whl
# Included: Not moved to build-scripts yet
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=httptools-0.6.4-cp313-cp313-wasix_wasm32.whl
# Included: Rust
PYTHON_WASIX_BINARIES_WHEELS+=jiter-0.10.0-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=lxml-6.0.0-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=markupsafe-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=msgpack-1.1.0-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=mysqlclient-2.2.7-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=numpy-wasix-cp313-cp313-wasix_wasm32.whl
# Included: Rust
PYTHON_WASIX_BINARIES_WHEELS+=orjson-3.11.0-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=pandas-cp313-cp313-wasix_wasm32.whl
# Included: Not moved to build-scripts yet
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=peewee-3.18.2-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=psycopg-3.2.9-py3-none-any.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=psycopg_c-3.2.9-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=psycopg_pool-3.3.0.dev1-py3-none-any.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=pycryptodome-3.23.0-cp37-abi3-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=pycryptodomex-3.23.0-cp37-abi3-wasix_wasm32.whl
# Included: Rust
PYTHON_WASIX_BINARIES_WHEELS+=pydantic_core-2.33.2-cp313-cp313-wasix_wasm32.whl
# Included: Not moved to build-scripts yet
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=pynacl-1.5.0-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=pytz-cp313-cp313-wasix_wasm32.whl
# Included: Not moved to build-scripts yet
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=pyyaml-6.0.2-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=regex-2025.5.18-cp313-cp313-wasix_wasm32.whl
# Included: Rust
PYTHON_WASIX_BINARIES_WHEELS+=rpds_py-0.26.0-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=shapely-2.1.1-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=six-cp313-cp313-wasix_wasm32.whl
# Included: Rust
PYTHON_WASIX_BINARIES_WHEELS+=tiktoken-0.9.0-cp313-cp313-wasix_wasm32.whl
# Included: Rust
PYTHON_WASIX_BINARIES_WHEELS+=tokenizers-0.21.3-cp313-cp313-wasix_wasm32.whl
# Included: Not moved to build-scripts yet. Does not seem native.
# TODO: Move to build-scripts
PYTHON_WASIX_BINARIES_WHEELS+=tornado-6.5.2-cp39-abi3-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=tzdata-cp313-cp313-wasix_wasm32.whl
# Not included: Source build in build-scripts
#PYTHON_WASIX_BINARIES_WHEELS+=uvloop-0.21.0-cp313-cp313-wasix_wasm32.whl

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
LIBS+=util-linux
LIBS+=dropbear
LIBS+=tinyxml2
LIBS+=geos
LIBS+=libxslt
LIBS+=libxml2

DONT_INSTALL=
# Dont install pypandoc because it uses the same name as pypandoc_binary
DONT_INSTALL+=pypandoc
DONT_INSTALL+=psycopg-binary
# Dont install numpy1, because we already have numpy 2
DONT_INSTALL+=numpy1

SUBMODULES=$(WHEELS) $(LIBS)

BUILT_WHEELS=$(addprefix pkgs/,$(addsuffix .whl,$(WHEELS)))
UNPACKED_WHEELS=$(addprefix pkgs/,$(addsuffix .wheel,$(WHEELS)))
BUILT_SDISTS=$(addprefix pkgs/,$(addsuffix .tar.gz,$(WHEELS)))
UNPACKED_SDISTS=$(addprefix pkgs/,$(addsuffix .sdist,$(WHEELS)))
UNPACKED_LIBS=$(addprefix pkgs/,$(addsuffix .build,$(LIBS)))
BUILT_LIBS=$(addprefix pkgs/,$(addsuffix .tar.xz,$(LIBS)))

DONT_INSTALL_LIBS=$(addprefix pkgs/,$(addsuffix .tar.xz,$(DONT_INSTALL)))
DONT_INSTALL_WHEELS=$(addprefix pkgs/,$(addsuffix .whl,$(DONT_INSTALL)))

PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL=$(filter-out $(DONT_INSTALL),$(PYTHON_WASIX_BINARIES_WHEELS))

BUILT_WHEELS_TO_INSTALL=$(filter-out $(DONT_INSTALL_WHEELS),$(BUILT_WHEELS))
BUILT_PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL=$(addprefix ${PYTHON_WASIX_BINARIES}/wheels/,$(addsuffix .whl,$(PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL)))
BUILT_LIBS_TO_INSTALL=$(filter-out $(DONT_INSTALL_LIBS),$(BUILT_LIBS))

ALL_INSTALLED_WHEELS=$(addprefix ${INSTALL_DIR}/.,$(addsuffix .installed,$(BUILT_WHEELS_TO_INSTALL)))
ALL_INSTALLED_WHEELS+=$(addprefix ${INSTALL_DIR}/.pwb-,$(addsuffix .installed,$(filter-out $(DONT_INSTALL),$(PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL))))
ALL_INSTALLED_LIBS=$(addprefix ${WASIX_SYSROOT}/.,$(addsuffix .installed,$(BUILT_LIBS_TO_INSTALL)))

# mkdir but resets the timestamp if it didnt exist before
define reset_builddir
bash -c 'rm -rf $$1 ; mkdir $$1 && touch -t 197001010000.00 $$1 || true' .
endef

define reset_submodule =
rm -rf $@
git restore $@
git submodule update --init --recursive $@
cd $@ && git clean -dxf >/dev/null 2>&1 || true
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
mkdir -p pkgs
if test -n "${PREPARE}" ; then source ./cross-venv/bin/activate && cd $(subst .whl,.sdist,$@) && _= ${PREPARE} ; fi
source ./cross-venv/bin/activate && cd $(subst .whl,.sdist,$@) && ${BUILD_ENV_VARS} python3 -m build --wheel ${BUILD_EXTRA_FLAGS}
mkdir -p artifacts
cp $(subst .whl,.sdist,$@)/dist/*[2y].whl artifacts
# [2y] is a hack to match anything ending in wasm32 or any
ln -sf ../artifacts/$$(basename $(subst .whl,.sdist,$@)/dist/*[2y].whl) $@
endef

define build_sdist =
mkdir -p pkgs
if test -n "${PREPARE}" ; then source ./cross-venv/bin/activate && cd $(subst pkgs/,,$(subst .tar.gz,,$@)) && _= ${PREPARE} ; fi
source ./cross-venv/bin/activate && cd $(subst pkgs/,,$(subst .tar.gz,,$@))/${PYPROJECT_PATH} && ${BUILD_ENV_VARS} python3 -m build --sdist ${BUILD_EXTRA_FLAGS}
mkdir -p artifacts
cp $(subst pkgs/,,$(subst .tar.gz,,$@))/${PYPROJECT_PATH}/dist/*[0-9].tar.gz artifacts
ln -sf ../artifacts/$$(basename $(subst pkgs/,,$(subst .tar.gz,,$@))/${PYPROJECT_PATH}/dist/*[0-9].tar.gz) $@
endef

# Bundle the first dependency to a tar.xz file in artifacts and link it to the target
define package_lib =
mkdir -p artifacts
cd $< && tar cfJ ${PWD}/artifacts/$(notdir $@) *
ln -sf $(shell realpath -s --relative-to="${PWD}/$(dir $@)" "${PWD}/artifacts/$(notdir $@)") $@
endef

# Command to run something in an environment with a haskell compiler targeting wasi
# Uses an older hash, because the latest version requires tail call support
RUN_WITH_HASKELL=nix shell 'gitlab:haskell-wasm/ghc-wasm-meta/6a8b8457df83025bed2a8759f5502725a827104b?host=gitlab.haskell.org' --command

all: $(BUILT_LIBS_TO_INSTALL) $(BUILT_WHEELS_TO_INSTALL) $(BUILT_PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL)
wheels: $(BUILT_WHEELS_TO_INSTALL)
external-wheels: $(BUILT_PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL)
libs: $(BUILT_LIBS_TO_INSTALL)

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
python-with-packages: python pkgs/postgresql.build pkgs/zbar.build pkgs/libjpeg-turbo.build pkgs/geos.build $(BUILT_WHEELS_TO_INSTALL) $(BUILT_PYTHON_WASIX_BINARIES_WHEELS_TO_INSTALL)
	### Prepare a python release with all the deps
	# Copy the base python package
	rm -rf python-with-packages
	cp -r python python-with-packages

	# Install the wheels
	INSTALL_DIR=$(PWD)/python-with-packages/artifacts/wasix-install/cpython/lib/python3.13 make install-wheels

	# Install the libs
	mkdir -p python-with-packages/artifacts/wasix-install/lib
	cp -L $(PWD)/pkgs/postgresql.build/usr/local/lib/wasm32-wasi/*.so* python-with-packages/artifacts/wasix-install/lib
	cp -L $(PWD)/pkgs/zbar.build/usr/local/lib/wasm32-wasi/libzbar.so* python-with-packages/artifacts/wasix-install/lib
	cp -L $(PWD)/pkgs/libjpeg-turbo.build/usr/local/lib/wasm32-wasi/libjpeg.so* python-with-packages/artifacts/wasix-install/lib
	# TODO: Build shapely without a shared geos dep
	cp -L $(PWD)/pkgs/geos.build/usr/local/lib/wasm32-wasi/libgeos* python-with-packages/artifacts/wasix-install/lib

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
	source ./cross-venv/bin/activate && PIP_EXTRA_INDEX_URL=https://pythonindex.wasix.org/simple build-pip install cffi numpy==2.4.0.dev0
	source ./cross-venv/bin/activate && PIP_EXTRA_INDEX_URL=https://pythonindex.wasix.org/simple pip install build six
# cross-venv: native-venv python
# 	rm -rf ./cross-venv
# 	source ./native-venv/bin/activate && python3 -m crossenv python/artifacts/wasix-install/cpython/bin/python3.wasm ./cross-venv --cc wasix-clang --cxx wasix-clang++
# 	source ./cross-venv/bin/activate && PIP_EXTRA_INDEX_URL=https://pythonindex.wasix.org/simple build-pip install cffi numpy==2.4.0.dev0
# 	source ./cross-venv/bin/activate && PIP_EXTRA_INDEX_URL=https://pythonindex.wasix.org/simple cross-pip install setuptools>=61.0.0 Cython
# 	source ./cross-venv/bin/activate && PIP_EXTRA_INDEX_URL=https://pythonindex.wasix.org/simple pip install build six 

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

protobuf:
	$(reset_submodule)
	# The bazel toolchain files need to be in the repository
	cp -r $(BAZEL_TOOLCHAIN) protobuf/wasix-toolchain

#####     Building wheels     #####

# A target to build a wheel from a python submodule
# To override the build behaviour, add a target for your submodule
$(BUILT_WHEELS): pkgs/%.whl: pkgs/%.sdist | cross-venv
pkgs/%.whl: pkgs/%.sdist
	$(build_wheel)
$(BUILT_SDISTS): pkgs/%.tar.gz: % | cross-venv
pkgs/%.tar.gz: %
	$(build_sdist)
$(UNPACKED_SDISTS): pkgs/%.sdist: pkgs/%.tar.gz | cross-venv
pkgs/%.sdist: pkgs/%.tar.gz
	rm -rf $@
	mkdir -p $@
	tar -xzf $^ -C $@ --strip-components=1
$(UNPACKED_WHEELS): pkgs/%.wheel: | cross-venv
pkgs/%.wheel: pkgs/%.whl
	rm -rf $@
	mkdir -p $@
	unzip -oq $< -d $@ 

# Depends on zbar headers being installed
# setup.py is not in the root directory
pkgs/pytz.tar.gz: PYPROJECT_PATH = build/dist
# Build the tzdb locally
pkgs/pytz.tar.gz: PREPARE = CCC_OVERRIDE_OPTIONS='^--target=x86_64-unknown-linux' CC=clang CXX=clang++ make build

pkgs/psycopg.tar.gz: PYPROJECT_PATH = psycopg
pkgs/psycopg-pool.tar.gz: PYPROJECT_PATH = psycopg_pool

pkgs/psycopg-binary.tar.gz: PYPROJECT_PATH = psycopg_binary
pkgs/psycopg-binary.tar.gz: PREPARE = rm -rf psycopg_binary && python3 tools/build/copy_to_binary.py
# Inject a mock pg_config to the PATH, so the build process can find it
pkgs/psycopg-binary.whl: BUILD_ENV_VARS = PATH="${PWD}/resources:$$PATH" WASIX_FORCE_STATIC_DEPENDENCIES=true
# Pretend we are a normal posix-like target, so we automatically include <endian.h>
pkgs/psycopg-binary.whl: export CCC_OVERRIDE_OPTIONS = ^-D__linux__=1

pkgs/pillow.whl: BUILD_ENV_VARS = PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig WASIX_FORCE_STATIC_DEPENDENCIES=true
pkgs/pillow.whl: BUILD_EXTRA_FLAGS = -Cplatform-guessing=disable

# We need to install, because we can only specify one sysroot in pkgconfig
pkgs/lxml.tar.gz: pkgs/libxml2.build pkgs/libxslt.build | install-libxml2 install-libxslt
pkgs/lxml.tar.gz: BUILD_ENV_VARS = PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${PWD}/pkgs/libxml2.build/usr/local/lib/wasm32-wasi/pkgconfig:${PWD}/pkgs/libxslt.build/usr/local/lib/wasm32-wasi/pkgconfig
pkgs/lxml.whl: BUILD_ENV_VARS = PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${PWD}/pkgs/libxml2.build/usr/local/lib/wasm32-wasi/pkgconfig:${PWD}/pkgs/libxslt.build/usr/local/lib/wasm32-wasi/pkgconfig

pkgs/dateutil.tar.gz: PREPARE = python3 updatezinfo.py

# Needs to run a cython command before building the wheel	
pkgs/msgpack-python.tar.gz: PREPARE = make cython

# Depends on a meson crossfile
pkgs/numpy.whl: BUILD_EXTRA_FLAGS = -Csetup-args="--cross-file=${MESON_CROSSFILE}"
pkgs/numpy.whl: ${MESON_CROSSFILE}

# Depends on a meson crossfile
pkgs/numpy1.tar.gz: BUILD_EXTRA_FLAGS = -Csetup-args="--cross-file=${MESON_CROSSFILE}"
pkgs/numpy1.tar.gz: ${MESON_CROSSFILE}
pkgs/numpy1.whl: BUILD_EXTRA_FLAGS = -Csetup-args="--cross-file=${MESON_CROSSFILE}"
pkgs/numpy1.whl: ${MESON_CROSSFILE}

pkgs/shapely.whl: pkgs/geos.build
# TODO: Static build don't work yet, because we would have to specify recursive dependencies manually
# pkgs/shapely.whl: BUILD_ENV_VARS += WASIX_FORCE_STATIC_DEPENDENCIES=true
# Set geos paths
pkgs/shapely.whl: BUILD_ENV_VARS += GEOS_INCLUDE_PATH="${PWD}/pkgs/geos.build/usr/local/include"
pkgs/shapely.whl: BUILD_ENV_VARS += GEOS_LIBRARY_PATH="${PWD}/pkgs/geos.build/usr/local/lib/wasm32-wasi"
# Use numpy dev build from our registry. Our patches have been merged upstream, so for the next numpy release we can remove this.
pkgs/shapely.whl: BUILD_ENV_VARS += PIP_CONSTRAINT=$$(F=$$(mktemp) ; echo numpy==2.4.0.dev0 > $$F ; echo $$F)
pkgs/shapely.whl: BUILD_ENV_VARS += PIP_EXTRA_INDEX_URL=https://pythonindex.wasix.org/simple
pkgs/shapely.whl: BUILD_EXTRA_FLAGS = --skip-dependency-check

# Needs to have the pypandoc executable in the repo
pkgs/pypandoc_binary.whl: pypandoc_binary/pypandoc/files/pandoc
pypandoc_binary/pypandoc/files/pandoc: pypandoc_binary pkgs/pandoc.tar.xz
	mkdir -p pypandoc_binary/pypandoc/files
	tar xfJ pkgs/pandoc.tar.xz -C pypandoc_binary/pypandoc/files --strip-components=1 bin/pandoc
	touch $@

pkgs/uvloop.whl: BUILD_ENV_VARS = WASIX_FORCE_STATIC_DEPENDENCIES=true
pkgs/uvloop.whl: BUILD_EXTRA_FLAGS = '-C--build-option=build_ext --use-system-libuv'

pkgs/mysqlclient.whl: BUILD_ENV_VARS = WASIX_FORCE_STATIC_DEPENDENCIES=true PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig

# Use numpy dev build from our registry. Our patches have been merged upstream, so for the next numpy release we can remove this.
pkgs/pandas.whl: BUILD_ENV_VARS += PIP_CONSTRAINT=$$(F=$$(mktemp) ; echo numpy==2.4.0.dev0 > $$F ; echo $$F)
pkgs/pandas.whl: BUILD_ENV_VARS += PIP_EXTRA_INDEX_URL=https://pythonindex.wasix.org/simple
pkgs/pandas.whl: BUILD_EXTRA_FLAGS = -Csetup-args="--cross-file=${MESON_CROSSFILE}"
pkgs/pandas.whl: ${MESON_CROSSFILE}

pkgs/protobuf.tar.gz: protobuf
	mkdir -p pkgs
	cd protobuf/python && CC=/usr/bin/gcc CXX=/usr/bin/g++ LD=/usr/bin/ld bazelisk build //python/dist:source_wheel --crosstool_top=//wasix-toolchain:wasix_toolchain --host_crosstool_top=@bazel_tools//tools/cpp:toolchain --cpu=wasm32-wasi
	mkdir -p artifacts
	install -m666 protobuf/bazel-bin/python/dist/protobuf.tar.gz artifacts
	ln -sf ../artifacts/protobuf.tar.gz $@

#####     Building libraries     #####

$(UNPACKED_LIBS): pkgs/%.build: %
$(BUILT_LIBS): pkgs/%.tar.xz: pkgs/%.build
pkgs/%.build: %
	echo "Missing build script for $@" >&2 && exit 1
pkgs/%.tar.xz: pkgs/%.build
	$(package_lib)
	touch $@

# TODO: Add libjpeg support
pkgs/zbar.build: zbar
	cd zbar && autoreconf -vfi
	# Force configure to build shared libraries. This is a hack, but it works.
	cd zbar && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd zbar && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --enable-static --enable-shared --disable-video --disable-rpath --without-imagemagick --without-java --without-qt --without-gtk --without-xv --without-xshm --without-python
	cd zbar && make
	$(reset_builddir) $@
	cd zbar && make install DESTDIR=${PWD}/$@
	touch $@

pkgs/libffi.build: libffi
	cd libffi && autoreconf -vfi
	cd libffi && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --host="wasm32-wasi" --enable-static --disable-shared --disable-dependency-tracking --disable-builddir --disable-multi-os-directory --disable-raw-api --disable-docs
	cd libffi && make
	$(reset_builddir) $@
	cd libffi && make install DESTDIR=${PWD}/$@
	touch $@

pkgs/zlib.build: zlib
	cd zlib && rm -rf combined
	cd zlib && cmake -B combined -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DCMAKE_SKIP_RPATH=YES -DZLIB_BUILD_MINIZIP=OFF
	cd zlib && cmake --build combined -j16
	$(reset_builddir) $@
	cd zlib && DESTDIR=${PWD}/$@ cmake --install combined
	touch $@

pkgs/pandoc.build: pandoc
	cd pandoc && ${RUN_WITH_HASKELL} wasm32-wasi-cabal update
	cd pandoc && ${RUN_WITH_HASKELL} wasm32-wasi-cabal build pandoc-cli
	# Most of these options are copied from https://github.com/tweag/pandoc-wasm/blob/master/.github/workflows/build.yml
	wasm-opt --experimental-new-eh --low-memory-unused --converge --gufa --flatten --rereloop -Oz $$(find pandoc -type f -name pandoc.wasm) -o pandoc/pandoc.opt.wasm
	$(reset_builddir) $@
	mkdir -p $@/bin
	install -m 755 pandoc/pandoc.opt.wasm $@/bin/pandoc
	touch $@

pkgs/postgresql.build: postgresql
	cd postgresql && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --without-icu --without-zlib --without-readline
	cd postgresql && make MAKELEVEL=0 -C src/interfaces
	cd postgresql && make MAKELEVEL=0 -C src/include
	$(reset_builddir) $@
	cd postgresql && make MAKELEVEL=0 -C src/interfaces install DESTDIR=${PWD}/$@
	cd postgresql && make MAKELEVEL=0 -C src/include install DESTDIR=${PWD}/$@
	touch $@

pkgs/brotli.build: brotli
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

pkgs/libjpeg-turbo.build: libjpeg-turbo
	cd libjpeg-turbo && rm -rf out
	# They use a custom version of GNUInstallDirs.cmake does not support libdir starting with prefix.
	# TODO: Add a sed command to fix that
	cd libjpeg-turbo && cmake -DCMAKE_BUILD_TYPE=Release -B out -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd libjpeg-turbo && make -C out
	$(reset_builddir) $@
	cd libjpeg-turbo && make -C out install DESTDIR=${PWD}/$@
	touch $@

pkgs/xz.build: xz
	cd xz && rm -rf static shared
	cd xz && cmake -B shared -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_SHARED_LIBS=ON -DCMAKE_SKIP_INSTALL_RPATH=YES -DCMAKE_SKIP_RPATH=YES
	cd xz && cmake -B static -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_SHARED_LIBS=OFF -DCMAKE_SKIP_INSTALL_RPATH=YES -DCMAKE_SKIP_RPATH=YES
	cd xz && cmake --build shared -j16
	cd xz && cmake --build static -j16
	$(reset_builddir) $@
	cd xz && DESTDIR=${PWD}/$@ cmake --install shared
	cd xz && DESTDIR=${PWD}/$@ cmake --install static
	touch $@

pkgs/libtiff.build: libtiff
	cd libtiff && bash autogen.sh
	# Force configure to build shared libraries. This is a hack, but it works.
	cd libtiff && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd libtiff && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd libtiff && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig make -j4
	$(reset_builddir) $@
	cd libtiff && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig make install DESTDIR=${PWD}/$@
	touch $@

pkgs/libwebp.build: libwebp
	cd libwebp && bash autogen.sh
	# Force configure to build shared libraries. This is a hack, but it works.
	cd libwebp && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd libwebp && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd libwebp && make
	$(reset_builddir) $@
	cd libwebp && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig make install DESTDIR=${PWD}/$@
	touch $@

pkgs/giflib.build: giflib resources/giflib.pc
	cd giflib && make
	$(reset_builddir) $@
	cd giflib && make install PREFIX=/usr/local LIBDIR=/usr/local/lib/wasm32-wasi DESTDIR=${PWD}/$@
	# giflib does not include a pkg-config file, so we need to install it manually. We need to bump the version in that file as well, when we update the version
	install -Dm644 ${PWD}/resources/giflib.pc ${PWD}/$@/usr/local/lib/wasm32-wasi/pkgconfig/giflib.pc
	touch $@

pkgs/libpng.build: libpng
	# Force configure to build shared libraries. This is a hack, but it works.
	cd libpng && sed -i 's/^  archive_cmds=$$/  archive_cmds='\''$$CC -shared $$pic_flag $$libobjs $$deplibs $$compiler_flags $$wl-soname $$wl$$soname -o $$lib'\''/' configure
	cd libpng && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd libpng && make
	$(reset_builddir) $@
	cd libpng && make install DESTDIR=${PWD}/$@
	touch $@

pkgs/SDL3.build: SDL3
	cd SDL3 && cmake . -DSDL_UNIX_CONSOLE_BUILD=ON -DSDL_RENDER_GPU=OFF -DSDL_VIDEO=OFF -DSDL_AUDIO=OFF -DSDL_JOYSTICK=OFF -DSDL_HAPTIC=OFF -DSDL_HIDAPI=OFF -DSDL_SENSOR=OFF -DSDL_POWER=OFF -DSDL_DIALOG=OFF -DSDL_STATIC=ON -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd SDL3 && make
	$(reset_builddir) $@
	cd SDL3 && make install DESTDIR=${PWD}/$@
	touch $@

pkgs/openjpeg.build: openjpeg
	cd openjpeg && PKG_CONFIG_SYSROOT_DIR=${WASIX_SYSROOT} PKG_CONFIG_PATH=${WASIX_SYSROOT}/usr/local/lib/wasm32-wasi/pkgconfig cmake . -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd openjpeg && make
	$(reset_builddir) $@
	cd openjpeg && make install DESTDIR=${PWD}/$@
	touch $@

pkgs/libuv.build: libuv
	cd libuv && rm -rf out
	cd libuv && cmake -B out -DLIBUV_BUILD_TESTS=OFF -DCMAKE_SYSTEM_NAME=WASI -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi'
	cd libuv && make -C out
	$(reset_builddir) $@
	cd libuv && make -C out install DESTDIR=${PWD}/$@
	touch $@

# TODO: Improve, after openssl is building
pkgs/mariadb-connector-c.build: mariadb-connector-c
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

pkgs/openssl.build: openssl
	# Options adapted from https://github.com/wasix-org/openssl/commit/52cc90976bea2e4f224250ef72cfa992c42bf410
	# Add no-pic to disable PIC
	cd openssl && ./Configure no-asm no-tests no-apps no-afalgeng no-dgram no-secure-memory --prefix /usr/local --libdir=lib/wasm32-wasi
	cd openssl && make -j8
	$(reset_builddir) $@
	cd openssl && make install_sw DESTDIR=${PWD}/$@
	touch $@

# We only build a static libuuid for now
pkgs/util-linux.build: util-linux
	cd util-linux && bash autogen.sh
	cd util-linux && ./configure --disable-all-programs --enable-libuuid --host=wasm32-wasi --enable-static --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi'
	cd util-linux && make
	$(reset_builddir) $@
	cd util-linux && make install DESTDIR=${PWD}/$@
	touch $@


pkgs/dropbear.build: dropbear
	cd dropbear && autoreconf -vfi
	cd dropbear && ./configure --prefix=/usr/local --libdir='$${exec_prefix}/lib/wasm32-wasi' --enable-bundled-libtom --without-pam --enable-static --disable-utmp --disable-utmpx --disable-wtmp --disable-wtmpx --disable-lastlog --disable-loginfunc
	cd dropbear && make -j8
	$(reset_builddir) $@
	cd dropbear && make install DESTDIR=${PWD}/$@
	touch $@

pkgs/tinyxml2.build: tinyxml2
	cd tinyxml2 && rm -rf shared static
	cd tinyxml2 && cmake -B static -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_SHARED_LIBS=OFF
	cd tinyxml2 && cmake -B shared -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_SHARED_LIBS=ON
	cd tinyxml2 && cmake --build static -j16
	cd tinyxml2 && cmake --build shared -j16
	$(reset_builddir) $@
	cd tinyxml2 && DESTDIR=${PWD}/$@ cmake --install static
	cd tinyxml2 && DESTDIR=${PWD}/$@ cmake --install shared
	touch $@

pkgs/geos.build: geos
	cd geos && rm -rf static shared
	cd geos && cmake -B static -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_GEOSOP=OFF -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DCMAKE_SKIP_INSTALL_RPATH=YES -DCMAKE_SKIP_RPATH=YES
	cd geos && cmake -B shared -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_GEOSOP=OFF -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_SKIP_INSTALL_RPATH=YES -DCMAKE_SKIP_RPATH=YES
	cd geos && cmake --build static -j16
	cd geos && cmake --build shared -j16
	$(reset_builddir) $@
	cd geos && DESTDIR=${PWD}/$@ cmake --install static
	cd geos && DESTDIR=${PWD}/$@ cmake --install shared
	touch $@

pkgs/libxslt.build: libxslt pkgs/xz.build pkgs/libxml2.build pkgs/zlib.build
	cd libxslt && rm -rf static shared
	cd libxslt && CMAKE_PREFIX_PATH=${PWD}/pkgs/xz.build/usr/local/lib/wasm32-wasi/cmake:${PWD}/pkgs/libxml2.build/usr/local/lib/wasm32-wasi/cmake:${PWD}/pkgs/zlib.build/usr/local/lib/wasm32-wasi/cmake cmake -B static -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_SHARED_LIBS=OFF -DCMAKE_SKIP_RPATH=YES -DLIBXSLT_WITH_PYTHON=OFF
	cd libxslt && CMAKE_PREFIX_PATH=${PWD}/pkgs/xz.build/usr/local/lib/wasm32-wasi/cmake:${PWD}/pkgs/libxml2.build/usr/local/lib/wasm32-wasi/cmake:${PWD}/pkgs/zlib.build/usr/local/lib/wasm32-wasi/cmake cmake -B shared -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DBUILD_SHARED_LIBS=ON -DCMAKE_SKIP_RPATH=YES -DLIBXSLT_WITH_PYTHON=OFF
	cd libxslt && cmake --build static -j16
	cd libxslt && cmake --build shared -j16
	$(reset_builddir) $@
	cd libxslt && DESTDIR=${PWD}/$@ cmake --install static
	cd libxslt && DESTDIR=${PWD}/$@ cmake --install shared
	touch $@

pkgs/libxml2.build: libxml2
	cd libxml2 && rm -rf shared static
	cd libxml2 && cmake -B static -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DCMAKE_SKIP_RPATH=YES -DBUILD_SHARED_LIBS=OFF -DLIBXML2_WITH_PYTHON=OFF
	cd libxml2 && cmake -B shared -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR='lib/wasm32-wasi' -DCMAKE_SKIP_RPATH=YES -DBUILD_SHARED_LIBS=ON -DLIBXML2_WITH_PYTHON=OFF
	cd libxml2 && cmake --build static -j16
	cd libxml2 && cmake --build shared -j16
	$(reset_builddir) $@
	cd libxml2 && DESTDIR=${PWD}/$@ cmake --install static
	cd libxml2 && DESTDIR=${PWD}/$@ cmake --install shared
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

${INSTALL_DIR}/.%.installed: pkgs/%.whl
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
	rm -rf pkgs/*.build
	rm -rf pkgs/*.wheel
	rm -rf pkgs/*.sdist

.PRECIOUS: $(WHEELS) $(LIBS) $(UNPACKED_LIBS) $(BUILT_LIBS) $(BUILT_WHEELS)
.PHONY: install install-wheels install-libs $(INSTALL_WHEELS_TARGETS) $(INSTALL_LIBS_TARGETS) clean wheels libs external-wheels