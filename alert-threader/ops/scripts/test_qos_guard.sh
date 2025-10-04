#!/usr/bin/env bash
# Test script for QoS guard mechanism
set -euo pipefail

echo "🧪 Testing QoS guard mechanism..."

# Test 1: Check initial status (should be unlocked)
echo "Test 1: Initial status check"
if /usr/local/sbin/qos_guard.sh status; then
    echo "✅ Test 1 passed (unlocked)"
else
    echo "❌ Test 1 failed (should be unlocked initially)"
    exit 1
fi

# Test 2: Lock guard-window
echo "Test 2: Lock guard-window"
if /usr/local/sbin/qos_guard.sh lock 1; then
    echo "✅ Test 2 passed (locked)"
else
    echo "❌ Test 2 failed (lock failed)"
    exit 1
fi

# Test 3: Check locked status (should fail)
echo "Test 3: Check locked status"
if /usr/local/sbin/qos_guard.sh status; then
    echo "❌ Test 3 failed (should be locked)"
    exit 1
else
    echo "✅ Test 3 passed (correctly locked)"
fi

# Test 4: Unlock guard-window
echo "Test 4: Unlock guard-window"
if /usr/local/sbin/qos_guard.sh unlock; then
    echo "✅ Test 4 passed (unlocked)"
else
    echo "❌ Test 4 failed (unlock failed)"
    exit 1
fi

# Test 5: Check unlocked status (should succeed)
echo "Test 5: Check unlocked status"
if /usr/local/sbin/qos_guard.sh status; then
    echo "✅ Test 5 passed (unlocked)"
else
    echo "❌ Test 5 failed (should be unlocked)"
    exit 1
fi

# Test 6: Test expired lock cleanup
echo "Test 6: Test expired lock cleanup"
/usr/local/sbin/qos_guard.sh lock 0.01  # Lock for 0.01 minutes (0.6 seconds)
sleep 1  # Wait for expiration
if /usr/local/sbin/qos_guard.sh status; then
    echo "✅ Test 6 passed (expired lock cleaned up)"
else
    echo "❌ Test 6 failed (expired lock not cleaned up)"
    exit 1
fi

echo "🎉 All QoS guard tests passed!"


