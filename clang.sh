#!/usr/bin/env bash
set -euo pipefail

# Detect if we are clang or clang++
if [[ "$0" =~ "++" ]]; then
    NATIVE_COMPILER="/home/lennart/Documents/llvm-project/buildfast/bin/clang++"
else
    NATIVE_COMPILER="/home/lennart/Documents/llvm-project/buildfast/bin/clang"
fi

if [ -z "${WASIX_SYSROOT:-}" ]; then
    echo "WASIX_SYSROOT environment variable not set" >&2
    exit 1
fi

PASSED_ARGS=(
    "$@"
)

# Analyze the arguments
# Check if we are also linking
run_linker=true
# We are building a shared library
shared_library=false
for arg in "${PASSED_ARGS[@]}"; do
    case "$arg" in
        -c|-S|-E)
            run_linker=false
            ;;
        -shared|--shared)
            shared_library=true
            ;;
    esac
done

COMPILER_ARGS=(
    --target=wasm32-wasi
    --sysroot="${WASIX_SYSROOT}"
    -matomics -mbulk-memory -mmutable-globals
    -pthread
    -mthread-model posix
    -ftls-model=global-dynamic
    -fno-trapping-math
    -D_WASI_EMULATED_MMAN -D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS
    -fvisibility=default
    -fwasm-exceptions
    -fPIC
    # Enable sjlj. This is unused when we are only linking, but figuring out if we are only linking is hard
    --start-no-unused-arguments -mllvm --wasm-enable-sjlj --end-no-unused-arguments
)
COMMON_LINKER_ARGS=(
    # Enable PIC
    -Wl,--experimental-pic
    -Wl,--extra-features=atomics,--extra-features=bulk-memory,--extra-features=mutable-globals
    -Wl,--shared-memory
    -Wl,--export-if-defined=__wasm_apply_data_relocs
    -Wl,--export-if-defined=__cxa_thread_atexit_impl
    -Wl,--export=__wasm_call_ctors
    -Wl,-mllvm,--wasm-enable-sjlj
)
LIBRARY_LINKER_ARGS=(
    # No standard libraries, because the main executable already provides them
    --no-standard-libraries -nostdlib++ -Wl,--no-entry
    # Build a shared library
    --shared
    # Import all unresolved symbols
    -Wl,--unresolved-symbols=import-dynamic
    ${WASIX_SYSROOT}/lib/wasm32-wasi/scrt1.o
)
EXECUTABLE_LINKER_ARGS=(
    -Wl,--import-memory
    -Wl,-pie
    -Wl,--export-all
    -Wl,--whole-archive,-lc,-lutil,-lresolv,-lrt,-lm,-lpthread,-lc++,-lc++abi,-lwasi-emulated-mman,-lwasi-emulated-getpid,-lcommon-tag-stubs,--no-whole-archive
)

# Filter unsupported arguments
FILTERED_PASSED_ARGS=( )
for arg in "${PASSED_ARGS[@]}"; do
    # Skip the arguments we want to discard
    if [[ "$arg" == "-Wl,--end-group" || "$arg" == "-Wl,--start-group" || "$arg" == "-Wl,--as-needed" || "$arg" == "-Wl,--allow-shlib-undefined" ]]; then
        continue
    fi
    # Add all other arguments to our filtered list
    FILTERED_PASSED_ARGS+=("$arg")
done

ARGS=()
ARGS+=("${COMPILER_ARGS[@]}")
if $run_linker; then
    ARGS+=("${COMMON_LINKER_ARGS[@]}")

    if $shared_library; then
        ARGS+=("${LIBRARY_LINKER_ARGS[@]}")
    else
        ARGS+=("${EXECUTABLE_LINKER_ARGS[@]}")
    fi
fi


ARGS+=("${FILTERED_PASSED_ARGS[@]}")


# exec ${NATIVE_COMPILER} "${ARGS[@]}"

# TODO: The below code path is only necessary, because we dont support legacy exceptions (yet?)
# TODO: Thsi is really error prone. We do NOT want to maintain a compiler wrapper that does more than just adding flags.
# We can probably just include the exception transformation pass in wasmer

if ! $run_linker; then
    echo ${NATIVE_COMPILER} "${ARGS[@]}"
    # If we are not linking, we can just run the compiler directly
    exec ${NATIVE_COMPILER} "${ARGS[@]}"
fi

# If we are linking, we need to run wasm-opt after the compilation to use the new exception handling
output_file="a.out"
for ((i=0; i<${#ARGS[@]}; i++)); do
    if [ "${ARGS[$i]}" = "-o" ] && [ $((i+1)) -lt ${#ARGS[@]} ]; then
        output_file="${ARGS[$i+1]}"
        break
    elif [[ "${ARGS[$i]}" =~ ^-o(.+)$ ]]; then
        output_file="${BASH_REMATCH[1]}"
        break
    fi
done

set -x
${NATIVE_COMPILER} "${ARGS[@]}" 

# Transform the old exception handling to the new one
wasm-opt --experimental-new-eh "$output_file" -o "$output_file"