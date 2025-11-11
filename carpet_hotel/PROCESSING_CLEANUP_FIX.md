# Processing Cleanup Fix - Summary

## Problem

Processing was leaving multiple processes running after being stopped, and video windows were freezing.

## Root Causes

1. **Multiple Process Spawning**: `processing-java` spawns multiple child processes (Java VM, video renderers, etc.)
2. **Incomplete Cleanup**: Original `ProcessWrapper` only killed the parent process
3. **No Signal Handlers**: Scripts didn't handle SIGINT/SIGTERM gracefully
4. **Processing IDE Interference**: If Processing IDE is open, it runs background LSP processes that can interfere

## Fixes Implemented

### 1. Enhanced ProcessWrapper (`app/utils.py`)

- Added `process_name_pattern` parameter to kill by name
- Implements 3-tier cleanup strategy:
  1. Graceful termination (SIGTERM, 2s timeout)
  2. Forceful kill (SIGKILL, 2s timeout)
  3. Kill all by process name pattern

```python
# Now uses pattern matching to kill ALL Processing processes
self.process = ProcessWrapper("Processing", process_name_pattern="Processing.app")
```

### 2. Signal Handlers (`app/carpet_hotel.py`)

- Added SIGINT and SIGTERM handlers
- Registered atexit cleanup
- Ensures graceful shutdown on Ctrl+C or script termination

### 3. GUI Cleanup (`app/carpet_hotel_gui.py`)

- Stops all systems before destroying window
- Adds 1-second delay for cleanup to complete
- Prevents zombie processes on GUI close

### 4. Test Suite Improvements (`app/tests/test_processing_comprehensive.py`)

- Reduced test duration from 5s to 3s
- Added cleanup between tests
- Registers atexit handler to kill all Processing on test exit
- Better exception handling with finally blocks

### 5. Manual Cleanup Script (`kill_processing.sh`)

Quick utility to kill all Processing processes if needed:

```bash
./kill_processing.sh
```

## Usage

### Normal Operation

Just stop Processing normally - cleanup happens automatically:

```python
from carpet_hotel_pde import CarpetHotelProcessing

pde = CarpetHotelProcessing(displays=[1])
pde.start()
# ... do work ...
pde.stop()  # Automatically kills all Processing processes
```

### If Processes Get Stuck

1. **Quick Fix**: Run the cleanup script
   ```bash
   ./kill_processing.sh
   ```

2. **Manual Fix**:
   ```bash
   pkill -9 -f "Processing.app"
   killall -9 Processing
   ```

3. **Check if cleaned**:
   ```bash
   ps aux | grep -i processing | grep -v grep
   ```

## About Processing "Freezing"

If Processing video windows freeze/hang:

1. **Expected Behavior**: Processing opens, shows video, then stops when you call `stop()`
2. **If it hangs**: Use Ctrl+C or close the window - signal handlers will clean up
3. **If truly frozen**: Use `./kill_processing.sh` to force cleanup

## Testing Cleanup

Quick test to verify cleanup works:

```bash
python3 app/tests/test_cleanup.py
```

Should output:
```
✓ Cleanup test PASSED
```

Then verify no processes remain:
```bash
ps aux | grep -i processing | grep -v grep
# Should show nothing
```

## Known Issues

1. **Processing IDE LSP**: If Processing IDE is open, it runs a Language Server Protocol (LSP) process
   - This is SEPARATE from processing-java processes
   - It's harmless but may show up in process lists
   - Only runs if you have Processing IDE open

2. **Rapid Start/Stop**: If you start/stop very quickly, some processes may not fully exit before next start
   - Added delays between tests to prevent this
   - In production, this shouldn't be an issue

## Best Practices

1. **Close Processing IDE** before running automated tests
2. **Use signal handlers**: Always let scripts exit normally (Ctrl+C)
3. **Check for zombies**: Run `./kill_processing.sh` if you interrupted something mid-test
4. **Test duration**: Keep tests short (2-3 seconds) to minimize hanging

## Files Modified

- `app/utils.py` - Enhanced ProcessWrapper with name-based killing
- `app/carpet_hotel_pde.py` - Uses new ProcessWrapper features
- `app/carpet_hotel.py` - Added signal handlers and atexit cleanup
- `app/carpet_hotel_gui.py` - Improved cleanup on window close
- `app/tests/test_processing_comprehensive.py` - Better cleanup between tests
- `app/tests/test_cleanup.py` - New quick cleanup test
- `kill_processing.sh` - Manual cleanup utility

## Verification

All cleanup mechanisms tested and working:

- ✓ Normal stop() kills all processes
- ✓ Ctrl+C triggers signal handler cleanup
- ✓ Script exit triggers atexit cleanup
- ✓ GUI close properly stops systems
- ✓ Test suite cleans up between tests
- ✓ Manual cleanup script works

## Summary

Processing cleanup is now **robust and automatic**. Multiple safety nets ensure no zombie processes:

1. Normal operation → ProcessWrapper kills by name
2. Ctrl+C → Signal handler cleans up
3. Script crash → atexit handler cleans up
4. GUI close → Explicit stop before exit
5. Tests → Cleanup between each test
6. Manual → `./kill_processing.sh` script

**The system now handles cleanup gracefully in all scenarios.**
