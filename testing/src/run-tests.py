import contextlib
import glob
import io
import os
import runpy
import sys


class Tee(io.StringIO):
    def __init__(self, *streams):
        super().__init__()
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()
        super().write(data)


# Check if a specific test is provided
if len(sys.argv) > 1:
    TEST_FILE = sys.argv[1]
    print(f"Checking file: {TEST_FILE}")
    if not os.path.isfile(TEST_FILE):
        print("Error: Test file '{}' not found.".format(TEST_FILE))
        sys.exit(1)
    TEST_FILES = [TEST_FILE]
    # Remove any subsequent arguments since these breaks pytest
    # for some ungodly reason (this one took a while to figure out)
    sys.argv = [sys.argv[0]]
else:
    test_dir = os.getenv("TEST_DIR", "./tests/")
    g = f"{test_dir}*.py"
    print(f"Checking glob: {g}")
    # Find all Python test files in ./tests directory
    TEST_FILES = [f for f in glob.glob(g) if ".skip" not in f and ".broken" not in f]

# Colors for output
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


# Function to run a test and display result
def run_test(test_file):
    print("{}Running test: {}{}".format(YELLOW, test_file, NC))

    buf = Tee(sys.stdout)
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(test_file, run_name="__main__")
        print(buf.getvalue())
        print("{}✓ PASS: {}{}".format(GREEN, test_file, NC))
        return True
    except SystemExit as e:
        output = buf.getvalue()
        print(output)
        if e.code == 0:
            print("{}✓ PASS: {}{}".format(GREEN, test_file, NC))
            return True
        else:
            print("{}✗ FAIL: {}{}".format(RED, test_file, NC))
            return False
    except Exception:
        output = buf.getvalue()
        print(output)
        print("{}✗ FAIL: {}{}".format(RED, test_file, NC))
        import traceback

        traceback.print_exc()
        return False


# Initialize counters and failed list
TOTAL_TESTS = 0
PASSED_TESTS = 0
FAILED_TESTS = 0
FAILED_LIST = []

# Run each test
print("Found {} tests, list: {}".format(len(TEST_FILES), TEST_FILES))
for test in TEST_FILES:
    TOTAL_TESTS += 1
    print(test)
    if run_test(test):
        PASSED_TESTS += 1
    else:
        FAILED_TESTS += 1
        FAILED_LIST.append(test)
    print("")

# Summary
print("{}Test Summary:{}".format(YELLOW, NC))
print("Total tests: {}".format(TOTAL_TESTS))
print("{}Passed: {}{}".format(GREEN, PASSED_TESTS, NC))
print("{}Failed: {}{}".format(RED, FAILED_TESTS, NC))

# List failed tests if any
if FAILED_TESTS > 0:
    print("{}Failed tests:{}".format(RED, NC))
    for failed in FAILED_LIST:
        print("{}  - {}{}".format(RED, failed, NC))

# Exit with failure if any test failed
if FAILED_TESTS > 0:
    sys.exit(1)
else:
    print("{}All tests passed! Package works.{}".format(GREEN, NC))
