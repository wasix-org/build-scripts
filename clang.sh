#!/usr/bin/env bash

# Array to store filtered arguments
filtered_args=()

# Process each argument
for arg in "$@"; do
    # Skip the arguments we want to discard
    if [[ "$arg" == "-Wl,--end-group" || "$arg" == "-Wl,--start-group" || "$arg" == "-Wl,--as-needed" || "$arg" == "-Wl,--allow-shlib-undefined" ]]; then
        continue
    fi
    # Add all other arguments to our filtered list
    filtered_args+=("$arg")
done

# Execute the real clang with filtered arguments
clang-19 "${filtered_args[@]}"

# Preserve the exit status
exit $?