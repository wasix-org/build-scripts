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
* matplotlib: 3.10.3
* uvloop: 0.21.0
* mysqlclient: 2.2.7
* python-qrcode: 8.2

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
* libtiff: 4.7.0
* libwebp: 1.5.0
* giflib: 5.2.2
* libpng: 1.6.50
* SDL: 3.2.16
* openjpeg: 2.5.3
* libuv: 1.51.0
* mariadb-connector-c: 3.4.6
* openssl: 3.5.1

SDL has all subsystems disabled

## Notes

All built library packages should include a pkg-config file for each library.

### [Variables in pkg-config files](https://www.gnu.org/prep/standards/html_node/Directory-Variables.html)

When building libs, we should make shour they include pkg-config files. The pkg config files should have their prefix set to `/usr/local`, exec_prefix set to `${prefix}`, libdir set to `${exec_prefix}/lib/wasm32-wasi`, and includedir set to `${prefix}/include`. In some cases it might be acceptable to have exec_prefix hardcoded to the same value as prefix. In that case libdir should start with `${prefix}` instead of `${exec_prefix}`.

## Analyzing the output

### Check whether python libaries require shared libs

You can run somethign like

```bash
for f in $(find "$INSTALL_DIR" -name '*.so') ; do echo $f ; wasm-tools print $f | head -n10 | grep '(needed' -C10 ; done
```

to check which python libraries depend on shared libs. We try to keep that to a minimum, so wheels contain everything that is required to use a package.
