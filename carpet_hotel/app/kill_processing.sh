#!/bin/bash
#
# Kill all Processing processes
#
# Use this script if Processing processes are left running after a crash
# or interrupted test.
#

echo "Killing all Processing processes..."

# Kill Processing
pkill -9 -f "Processing.app" 2>/dev/null || true

# Wait a bit
sleep 1

# Check if any are still running
if ps aux | grep -i "Processing.app" | grep -v grep > /dev/null 2>&1; then
    echo "⚠ Some Processing processes may still be running"
    echo "Running processes:"
    ps aux | grep -i "Processing.app" | grep -v grep
else
    echo "✓ All Processing processes killed"
fi
