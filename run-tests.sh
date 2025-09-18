output_file=$(mktemp)

PYTHON_PACKAGE=${1:-"python-with-packages"}

# Set if a test that was not expected to fail did fail
WORKING_FAILED=()
BROKEN_FAILED=()
WORKING_PASSED=()
BROKEN_PASSED=()
SKIPPED=()

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
RESET="\033[0m"

for testfile in tests/*.py; do
    # Extract just the filename without path
    TEST_NAME=$(basename "$testfile")

    # Skip test if it is a *.skip.py file
    if [[ "$TEST_NAME" == *.skip.py ]]; then
        echo -e "${YELLOW}Skipping:${RESET} \033[1m$TEST_NAME${RESET}"
        SKIPPED+=( "$TEST_NAME" )
        continue
    fi

    EXPECT_BROKEN=false
    if [[ "$TEST_NAME" == *-broken.py ]]; then
        EXPECT_BROKEN=true
    fi
    
    # Print colorful running message
    echo -e "\033[0;34m▶ Running:${RESET} \033[1m$TEST_NAME${RESET}"
    
    # Run the test
    $WASMER run --net --mapdir="/src:$(pwd)" --llvm $PYTHON_PACKAGE /src/$testfile
    EXIT_CODE=$?

    # Prepare output color. This will be changed depending on what we expect for the test
    COLOR="$GREEN"
    # Log result and prepare colorful outcome for later
    if [ $EXIT_CODE -eq 0 ]; then
        if $EXPECT_BROKEN; then
            COLOR="${RED}"
            BROKEN_PASSED+=( "$TEST_NAME" )
        else
            COLOR="${GREEN}"
            WORKING_PASSED+=( "$TEST_NAME" )
        fi
        echo -e "  ${COLOR}✓ PASSED${RESET} $TEST_NAME" | tee -a "$output_file"
    else
        if $EXPECT_BROKEN; then
            COLOR="${YELLOW}"
            BROKEN_FAILED+=( "$TEST_NAME" )
        else
            COLOR="${RED}"
            WORKING_FAILED+=( "$TEST_NAME" )
        fi
        echo -e "  ${COLOR}✗ FAILED${RESET} $TEST_NAME" | tee -a "$output_file"
        echo -e "  ${COLOR}└── Test failed with exit code $EXIT_CODE${RESET}" | tee -a "$output_file"
    fi
    echo ""
done

# Check if all broken tests failed and all working tests passed
EXPECTED_OUTCOME=false
if [ ${#WORKING_FAILED[@]} -eq 0 ] && [ ${#BROKEN_PASSED[@]} -eq 0 ]; then
    EXPECTED_OUTCOME=true
fi

BROKEN_TESTS=( ${BROKEN_FAILED[@]} ${BROKEN_PASSED[@]} )
WORKING_TESTS=( ${WORKING_FAILED[@]} ${WORKING_PASSED[@]} )
ALL_TESTS=( ${WORKING_FAILED[@]} ${WORKING_PASSED[@]} ${BROKEN_FAILED[@]} ${BROKEN_PASSED[@]} ${SKIPPED[@]} )


# Print summary
cat "$output_file"
echo ""
echo -e "\033[1;34mSummary:\033[0m"
if $EXPECTED_OUTCOME; then
    echo -e "  \033[0;32mAll tests behaved as expected!\033[0m"
else
    echo -e "  \033[0;31mSome tests did not behave as expected."
fi

if test ${#WORKING_FAILED[@]} -gt 0; then
    echo -e "  ${RED}Failed tests (that were expected to pass):${RESET}"
    for test in "${WORKING_FAILED[@]}"; do
        echo -e "    $RED$test$RESET"
    done
fi
if test ${#BROKEN_FAILED[@]} -gt 0; then
    echo -e "  ${YELLOW}However ${#BROKEN_TESTS[@]} are marked broken. ${RESET}\033[4;5mGo fix the underlying issues.${RESET}"
fi
if test ${#BROKEN_WORKING[@]} -gt 0; then
    echo -e "  ${RED}The following tests were marked broken but passed.${RESET}"
    echo -e "  ${RED}Go mark them as not broken 🎉:${RESET}"
    for test in "${BROKEN_WORKING[@]}"; do
        echo -e "    $YELLOW$test$RESET"
    done
fi

# Exit with the correct code
$EXPECTED_OUTCOME

