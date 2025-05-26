set -e

WORKDIR=$(pwd)
if test -z "$WASIX_SYSROOT" ; then
    echo "WASIX_SYSROOT is not set. Please set it to the sysroot path (Something like /home/lennart/Documents/wasix-libc/sysroot)."
    exit 1
fi

git submodule update --init --recursive
cd numpy
git am ../patches/*.patch
cd ..

wasmer package download zebreus/python -o python.webc
wasmer package unpack python.webc --out-dir python

python3 -m venv ./native-venv
source ./native-venv/bin/activate
pip install crossenv

python3 -m crossenv $(pwd)/python/tmp/wasix-install/cpython/bin/python3.wasm ./cross-venv --cc 'clang-19 --sysroot='"$WASIX_SYSROOT"' --target=wasm32-wasix' --cxx 'clang-19 --sysroot='"$WASIX_SYSROOT"' --target=wasm32-wasix -fPIC'
source ./cross-venv/bin/activate
python3 -m pip install cython build 
CROSSFILE=$(pwd)/wasi.meson.cross
cd numpy
python3 -m build --wheel -Csetup-args="--cross-file=$CROSSFILE"