# Python native modules for WASIX

## Python Index

You can use this index for WASIX easily by providing this index to `pip` or `uv`: <https://pythonindex.wasix.org/>

### Using the index in your projects

The actual **Simple API** endpoint that pip/uv expect lives under the `simple/` path, so the full base URL is:

```bash
https://pythonindex.wasix.org/simple
```

Below are a few common ways to point your tooling at it.

#### pip (one-off)

Install a package **only** from the WASIX index (no PyPI fallback):

```bash
pip install --index-url https://wasix-org.github.io/build-scripts/simple <package-name>
```

Keep the default PyPI index but let pip also search the WASIX index:

```bash
pip install --extra-index-url https://wasix-org.github.io/build-scripts/simple <package-name>
```

You can also set an environment variable once per shell:

```bash
export PIP_INDEX_URL=https://wasix-org.github.io/build-scripts/simple
pip install <package-name>
```

#### uv (one-off)

`uv` accepts the same flags as pip, so you can run e.g.:

```bash
# Only use the WASIX index
uv pip install --index-url https://wasix-org.github.io/build-scripts/simple <package-name>

# Or combine with PyPI
uv pip install --extra-index-url https://wasix-org.github.io/build-scripts/simple <package-name>
```

#### uv (project configuration)

For a permanent, checked-in configuration add a custom index section to your `pyproject.toml`:

```toml
[[tool.uv.index]]
# A human-friendly name you pick
name = "wasix"
# The Simple index URL
url = "https://wasix-org.github.io/build-scripts/simple"
# Optional – make this the primary index
default = true
```

After that, every `uv sync` / `uv pip install` inside the project will automatically resolve packages against the WASIX index.

---

### Rebuilding the index

All the supported native modules are already compiled in the [`artifacts/`](./artifacts) folder.
For each commit that changes the modules, we generate a new index using `dumb-pypi` that is statically stored in the provided URL index.

If you want to regenerate the index manually, you just need to do:

```bash
./generate-index.sh
```

## Building modules from source

Buildscripts to build numpy and other wheels for wasix. For convenience, this package already includes prebuilt versions of all the wheels and libraries.

### Usage

The build script is controlled by the following environment variables:

* `CC`, `CXX`, `AR`, `LD`, `RANLIB`, etc... : The cross-compiler tools. These should all be normal clang tools, but target wasm32-wasix by default and use the wasix sysroot.
* `WASIX_SYSROOT`: The path to the wasix sysroot that is used by the toolchain. Libraries will get installed here when you run `make install` or when they are required to build a package.
* `INSTALL_DIR`: The path to the python library path. Wheels will get installed here when you run `make install`.
* `WASMER`: The path to the wasmer binary. You must have it registered to handle wasm files as binfmt_misc. You can do this with `sudo $WASMER binfmt reregister`.

The easiest way to setup all the environment variables is to activate the wasix-clang environment using `source wasix-clang/activate`.

Then you can run `make all` to build all wheels and libraries.

### Usage with [wasix-clang](https://github.com/wasix-org/wasix-clang)

Example for building a numpy wheel from scratch:

```bash
# Install common dependencies
sudo apt install -y git git-lfs build-essential make cmake python3.13 python3.13-venv autopoint libtool pkg-config autoconf dejagnu meson ninja-build bison flex perl patchelf po4a yq
# Some packages need some more exotic or big dependencies. More details in the spoiler below

# Install wasix-clang
curl -sSf https://raw.githubusercontent.com/wasix-org/wasix-clang/refs/heads/main/setup.sh | bash
source ~/wasix-clang/activate

# Fetch this repo
git clone https://github.com/wasix-org/build-scripts.git
cd build-scripts

# Build numpy
make pkgs/numpy.whl
```

The above example was tested in a freshly installed ubuntu VM created with:

```bash
multipass launch 25.04 -n wasix-test --disk 50G --cpus 4 --memory 16G
multipass shell wasix-test
```

<details>
  <summary>More dependencies</summary>
  
  ```bash
  # giflib docs require these but they are quite big
  sudo apt install -y xmlto imagemagick
  
  # pandoc requires a haskell toolchain for wasm32 which we build with nix
  curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sudo sh -s -- install $(! test -f /.dockerenv || echo "linux --init none") --no-confirm
  source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
  
  # grpc and protobuf require bazel. I found bazelisk the easiest way to install bazel
  wget https://github.com/bazelbuild/bazelisk/releases/download/v1.27.0/bazelisk-linux-amd64
  sudo install -m755 bazelisk-linux-amd64 /usr/bin/bazel
  rm bazelisk-linux-amd64
  ```

</details>

### Patches

For the most part we try to keep patches to a minimum and contribute changes back upstream if they provide any additional value besides adding WASIX support.

Patches are mostly applied to make existing build processes that don't support a WASI target work. In the rare cases where software uses features that are not available in WASIX we might also patch it to add workarounds/remove broken code paths. We try to keep software as vanilla as possible.

One exception is `numpy` where we have a special patch that helps when building other crates. More on that below.

### Versions

Here is a list of the versions of the wheels and libraries that are included in this package:

#### Wheels

* numpy: numpy/numpy main
* markupsafe: 3.0.2
* pandas: 2.3.2
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
* matplotlib: 3.10.6
* uvloop: 0.21.0
* mysqlclient: 2.2.7
* python-qrcode: 8.2
* pycparser: 2.22
* pydantic: 2.11.7
* typing_extensions: 4.14.1
* typing-inspection: 0.4.1
* annotated-types: 0.7.0
* shapely: 2.1.1
* mrab-regex: 2025.7.31
* lxml: 6.0.0
* protobuf: 31.1
* grpc: 1.74.1
* numpy: 1.26.5
* numpy: 2.0.2
* numpy: 2.3.2
* python-crc32c: 1.7.1
* requests: 2.32.4
* urllib3: 2.5.0
* idna: 3.10
* certifi: 2025.08.03
* charset-normalizer: 3.4.3
* pypng: 0.20250521.0
* pyarrow: 19.0.1
* pyarrow: 21.0.0
* packaging: 25.0
* pyparsing: 3.2.3
* cycler: 0.12.1
* kiwisolver: 1.4.9
* contourpy: 1.3.3
* pyopenssl: 25.1.0
* aspw: 3.50.4.0
<!-- WHEEL_VERSIONS_END -->

psycopg3-c is just the sdist of psycopg3-binary

#### Libraries

* libzbar: 0.23.93
* libffi: wasix-org/libffi main
* pandoc: haskell-wasm/pandoc wasm
* postgresql: 17.5
* brotli: 1.1.0
* zlib: develop
  * 1.3.1 does not have proper cmake support, so we are using develop for now
* libjpeg-turbo: 3.1.1
* xz: 5.8.1
* libtiff: 4.7.0
* libwebp: 1.5.0
* giflib: 5.2.2
* libpng: 1.6.50
* SDL: 3.2.16
  * SDL has all subsystems disabled
* openjpeg: 2.5.3
* libuv: 1.51.0
* mariadb-connector-c: 3.4.6
* openssl: 3.5.1
* bzip2: 1.0.8
* util-linux: 2.41.1
  * We only build libuuid from util-linux
* openssh: 10.0p2
* dropbear: 2025.88
* tinyxml2: 11.0.0
* geos: 3.13.1
* libxslt: 1.1.43
* libxml2: 2.14.5
* google-crc32c: 1.1.2
* arrow: 19.0.1
* arrow: 21.0.0
* rapidjson: 1.1.0
* icu: 77.1
* readline: 8.2
* ncurses: 6.4.20230225
* curl: curl/curl ab18c04218ff316cd67b1e928c5cee579b2f66a0
  * This was the current commit in the wasix fork. We can probably update to the next release
* pycurl: 7.45.6
* sqlite: 3.50.4
* wasix-libc: wasix-org/wasix-libc e4e5cfcf1009e690207821e9b3a63cdce2ee9e86
  * The commit before we removed fork. A few packages don't build if fork is not defined.
* libcxx: wasix-org/llvm-project 6bb93a243f6d15855f485f5aec3810d9e2de150d
  * This is the commit that is currently used by wasix-libc
* compiler-rt: wasix-org/llvm-project 6bb93a243f6d15855f485f5aec3810d9e2de150d
  * This is the commit that is currently used by wasix-libc
* cpython: wasix-org/cpython feat/dl
<!-- LIB_VERSIONS_END -->

### Notes

All built library packages should include a pkg-config file for each library.

When building wheels that depend on detecting numpy headers via `numpy.get_include()` at compiletime it might be required to set the `NUMPY_ONLY_GET_INCLUDE` environment variable. We have a special patch that detects that variable when importing numpy and only exports the `get_include()` function in that case. Otherwise importing numpy causes it to load all native modules and crash when crosscompiling because wasm native modules won't work on x86_64 CPUs.

While `wasix-clang` tries to be as lightweight as possible while still behaving like clang, we have a special `WASIX_FORCE_STATIC_DEPENDENCIES` environment variable that forces all libraries to be static. While WASIX does have full support we don't always like to use shared libs for reasons.

#### [Variables in pkg-config files](https://www.gnu.org/prep/standards/html_node/Directory-Variables.html)

When building libs, we should make shour they include pkg-config files. The pkg config files should have their prefix set to `/usr/local`, exec_prefix set to `${prefix}`, libdir set to `${exec_prefix}/lib/wasm32-wasi`, and includedir set to `${prefix}/include`. In some cases it might be acceptable to have exec_prefix hardcoded to the same value as prefix. In that case libdir should start with `${prefix}` instead of `${exec_prefix}`.

### Analyzing the output

#### Check whether python libaries require shared libs

You can run somethign like

```bash
for f in $(find "$INSTALL_DIR" -name '*.so') ; do echo $f ; wasm-tools print $f | head -n10 | grep '(needed' -C10 ; done
```

to check which python libraries depend on shared libs. We try to keep that to a minimum, so wheels contain everything that is required to use a package.

### Structure

<!-- 
There is the pkgs folder that contains most stuff

For each project that can be built there are multiple files depending on the type.

Every project has a its source added as a submodule as `*.source`. That one contains the clean checkout of the submodule. We try not to modify the `*.source` directory because otherwise git in the build-scripts repo gets really slow because it needs to track all the changes.

Before building a project, the `*.source` repo is used to generate a `*.prepared` directory. This is a worktree of the `*.source` repo with some patches applied, if necessary. If no patches are necessary this is just a clean worktree. This one is persistent and will not get deleted, unless the source changes.

When building the project the `*.prepared` is copied to a `*.build` directory. This is the directory in which the buildstep is executed. There may be a ton of temporary build artifacts in here. This repo may get removed between builds; don't make any manual changes in here.

`*.source` is a clean repo of the upstream source
`*.prepared` is a worktree of the submodule with our patches.
`*.build` source directory we actually build in.

For python modules the buildstep involves creating a `*.tar.gz` sdist from the `*.build` folder. The `*.tar.gz` is then unzipped to a `*.sdist` folder. From that `.sdist` folder a `*.whl` wheel is created.

For WASIX libraries (and application) the buildstep installs the library with the correct directory structure into a `*.lib` folder. That folder is then packed into a final `*.tar.xz`

```
TODO: Make this more understandable
```
-->

Inside the pkgs/ folder there can be the following directories:

* `*.source`: clean submodule checkout
* `*.prepared`: patched worktree of source
* `*.build`: temporary build directory
* `*.tar.gz`: python sdist
* `*.sdist`: unpacked python sdist
* `*.whl`: compiled python wheel
* `*.wheel`: unpacked python wheel
* `*.lib`: unpacked library/application
* `*.tar.xz`: packed library/application

#### Base structure

Each project follows a consistent flow through the first three main directories.

* `*.source`
  * This is a clean checkout of the project's upstream source code, tracked as a git submodule.
  * We avoid modifying this directly, since changes here would slow down git operations in the build-scripts repo.
* `*.prepared`
  * A git worktree created from the `*.source` repository.
  * If patches are needed, they're applied here.
  * If no patches are needed, it's just a clean mirror of the source.
  * This directory is persistent and only refreshed if the source changes so new patches can be developed in this directory
* `*.build`
  * A copy of the `*.prepared` directory, used for the actual build step.
  * Contains all intermediate build artifacts.
  * This directory is temporary and may be deleted between builds. Never make manual changes here.

The remaining steps are different depending on the type of project.

#### Python modules

* The build step creates a `*.tar.gz` sdist from the `*.build` directory.
* The sdist is then extracted into a `*.sdist` folder.
* Finally, a wheel (`*.whl`) is built from the `*.sdist`.
* If you want to you can make a `*.wheel` directory to view the unpacked wheel

#### WASIX libraries and applications

* The build step builds the library and installs it into a `*.lib` folder, following the correct directory structure.
* That folder is then compressed into a final distributable *.tar.xz.

#### Interdependencies

If a project depends on other project they can either be direct dependencies of that project or you can define a `*.sysroot` target with the dependencies as prerequisites.

* `*.sysroot`
  * Contains the merged builds of multiple other projects
  * Useful when a project is using pkg-config to find its dependencies
  * Automatically builds a sysroot from its list of prerequisites
