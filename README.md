# more than numpy

Buildscripts to build numpy and other wheels for wasix. For convenience, this package already includes prebuilt versions of all the wheels and libraries.

## Usage

The build script is controlled by the following environment variables:

* `CC`, `CXX`, `AR`, `LD`, `RANLIB`, etc... : The cross-compiler tools. These should all be normal clang tools, but target wasm32-wasix by default and use the wasix sysroot.
* `WASIX_SYSROOT`: The path to the wasix sysroot that is used by the toolchain. Libraries will get installed here when you run `make install` or when they are required to build a package.
* `INSTALL_DIR`: The path to the python library path. Wheels will get installed here when you run `make install`.
* `WASMER`: The path to the wasmer binary. You must have it registered to handle wasm files as binfmt_misc. You can do this with `sudo $WASMER binfmt reregister`.

The easiest way to setup all the environment variables is to activate the wasix-clang environment using `source wasix-clang/activate`.

Then you can run `make all` to build all wheels and libraries.

## Versions

Here is a list of the versions of the wheels and libraries that are included in this package:

### Wheels

* numpy: 2.0.2
* markupsafe: 3.0.2
* pandas: 2.2.3
* pytz: 2025.2
* dateutil: 2.9.0
* tzdata: 2025.2
* six: 1.17.0
* msgpack: 1.1.0
* pycryptodome: 3.23.0
* pycryptodomex: 3.23.0
* pyzbar: 0.1.9
* cpython: 3.1.2
* pypandoc: 1.15
* pypandoc_binary: 1.15
* psycopg: 3.2.9
* psycopg-binary: 3.2.9
* psycopg-pool: pool-3.2.6
* brotlicffi: 1.1.0.0
* cffi: 1.17.1
* pillow: 11.3.0

psycopg3-c is just the sdist of psycopg3-binary

### Libraries

* libzbar: 0.23.93
* libffi: wasix-org/libffi main
* pandoc: haskell-wasm/pandoc wasm
* postgresql: 17.5
* brotli: 1.1.0
* zlib: 1.3.1
* libjpeg-turbo: 3.1.1
* xz: 5.8.1
