#!/usr/bin/env bash
# Test script for retry backoff mechanism
set -euo pipefail

echo "🧪 Testing retry backoff mechanism..."

# Test 1: Successful command (should succeed immediately)
echo "Test 1: Successful command"
if /usr/local/sbin/retry_backoff.sh 3 2 -- echo "Success!"; then
    echo "✅ Test 1 passed"
else
    echo "❌ Test 1 failed"
    exit 1
fi

# Test 2: Failing command (should retry and fail)
echo "Test 2: Failing command"
if /usr/local/sbin/retry_backoff.sh 2 1 -- false; then
    echo "❌ Test 2 failed (should have failed)"
    exit 1
else
    echo "✅ Test 2 passed (correctly failed)"
fi

# Test 3: Eventually successful command
echo "Test 3: Eventually successful command"
attempt=0
if /usr/local/sbin/retry_backoff.sh 3 1 -- bash -c 'attempt=$((attempt+1)); if [ $attempt -lt 3 ]; then exit 1; else echo "Success after $attempt attempts"; fi'; then
    echo "✅ Test 3 passed"
else
    echo "❌ Test 3 failed"
    exit 1
fi

echo "🎉 All retry backoff tests passed!"


