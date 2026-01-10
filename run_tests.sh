#!/bin/bash
# Script to run CKAN extension tests locally using act (GitHub Actions runner)
# This simulates the CI environment for testing

set -e  # Exit on error

# Clear screen for clean output
clear

echo "=========================================="
echo "Running CKAN Extension Tests with act"
echo "=========================================="
echo ""

# Run act tests without pulling images (uses cached Docker images)
# Output is both displayed and saved to test_results.txt
act pull_request -j test --pull=false 2>&1 | tee test_results.txt

# Store the exit code from act
EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=========================================="
echo "Cleaning up Docker containers..."
echo "=========================================="

# Clean up act-related Docker containers
docker ps -a --filter "name=act-" --format "{{.ID}}" | xargs -r docker rm -f

echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo "Exit code: $EXIT_CODE"
echo "Full output saved to: test_results.txt"
echo ""

# Check results
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed. Check test_results.txt for details."
fi

exit $EXIT_CODE
