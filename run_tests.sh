#!/bin/bash

# Usage: ./run_tests.sh [--testname <test_name>]
# If --testname is not specified, all tests in test_integration.py are run.

TEST_FILE="tests/test_integration.py"
TEST_NAME=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --testname)
      TEST_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: $0 [--testname <test_name>]"
      exit 1
      ;;
  esac
done

# Build and run the pytest command
if [[ -n "$TEST_NAME" ]]; then
  echo "Running test: $TEST_NAME"
  python3.11 -m pytest "${TEST_FILE}::${TEST_NAME}" -v
else
  echo "Running all tests in $TEST_FILE"
  python3.11 -m pytest "$TEST_FILE" -v
fi
