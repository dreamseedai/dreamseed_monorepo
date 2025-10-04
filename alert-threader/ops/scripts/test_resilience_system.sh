#!/usr/bin/env bash
# Comprehensive test script for the resilience system (retry + QoS guard)
set -euo pipefail

echo "🧪 Testing resilience system (retry backoff + QoS guard)..."

# Ensure scripts are executable
chmod +x /usr/local/sbin/retry_backoff.sh /usr/local/sbin/qos_guard.sh

# Test 1: Retry backoff mechanism
echo "Test 1: Retry backoff mechanism"
if /usr/local/sbin/retry_backoff.sh 2 1 -- echo "Retry test success"; then
    echo "✅ Retry backoff test passed"
else
    echo "❌ Retry backoff test failed"
    exit 1
fi

# Test 2: QoS guard mechanism
echo "Test 2: QoS guard mechanism"
if /usr/local/sbin/qos_guard.sh status; then
    echo "✅ QoS guard initial status test passed"
else
    echo "❌ QoS guard initial status test failed"
    exit 1
fi

# Test 3: Lock and unlock cycle
echo "Test 3: Lock and unlock cycle"
/usr/local/sbin/qos_guard.sh lock 1
if ! /usr/local/sbin/qos_guard.sh status; then
    echo "✅ QoS guard lock test passed"
else
    echo "❌ QoS guard lock test failed"
    exit 1
fi

/usr/local/sbin/qos_guard.sh unlock
if /usr/local/sbin/qos_guard.sh status; then
    echo "✅ QoS guard unlock test passed"
else
    echo "❌ QoS guard unlock test failed"
    exit 1
fi

# Test 4: Integration test - retry with guard check
echo "Test 4: Integration test"
/usr/local/sbin/qos_guard.sh lock 1
if /usr/local/sbin/retry_backoff.sh 2 1 -- /usr/local/sbin/qos_guard.sh status; then
    echo "❌ Integration test failed (should have failed due to locked guard)"
    exit 1
else
    echo "✅ Integration test passed (correctly failed due to locked guard)"
fi

/usr/local/sbin/qos_guard.sh unlock

# Test 5: Simulate rollback scenario
echo "Test 5: Simulate rollback scenario"
/usr/local/sbin/qos_guard.sh lock 1
echo "Simulating rollback with guard-window locked..."
if /usr/local/sbin/retry_backoff.sh 2 1 -- echo "Rollback simulation"; then
    echo "✅ Rollback simulation test passed"
else
    echo "❌ Rollback simulation test failed"
    exit 1
fi

/usr/local/sbin/qos_guard.sh unlock

# Test 6: Error handling
echo "Test 6: Error handling"
if /usr/local/sbin/retry_backoff.sh 1 1 -- false; then
    echo "❌ Error handling test failed (should have failed)"
    exit 1
else
    echo "✅ Error handling test passed (correctly failed)"
fi

echo "🎉 All resilience system tests passed!"
echo "System is ready for production use."


