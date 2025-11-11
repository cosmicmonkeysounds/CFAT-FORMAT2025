# Processing Test Guide

## Automated Test Results

**Date:** 2025-11-11
**Test Suite:** `app/tests/test_processing_comprehensive.py`
**Result:** ✓ **100% PASS** (15/15 tests)

### Tests Completed

#### ✓ 1. Dependencies
- Processing-java detection and verification
- Sketch directory validation
- Location: `/usr/local/bin/processing-java`

#### ✓ 2. Display Detection
- Detected 2 displays successfully
  - Display 0: 5120x1440 (Primary)
  - Display 1: 1728x1117

#### ✓ 3. Wrapper Initialization
- Default configuration
- Custom display configuration

#### ✓ 4. Single Display Configurations
- Display 1 only
- Display 2 only

#### ✓ 5. Multiple Display Configurations
- Displays [1, 2] (normal order)
- Displays [2, 1] (reversed order)

#### ✓ 6. Keyboard Control Modes
- Keyboard enabled
- Keyboard disabled

#### ✓ 7. Process Lifecycle
- Start/stop/restart cycle

---

## Manual Interactive Testing

For interactive GUI testing, run these commands to verify visual output and controls:

### Test 1: Default Configuration (Both Displays)

```bash
cd app
python3 carpet_hotel_pde.py
```

**Expected:**
- Processing windows appear on displays 1 and 2
- Videos play smoothly
- Control window shows status

**Press Ctrl+C to stop**

---

### Test 2: Single Display (Display 1)

```bash
cd app
python3 carpet_hotel_pde.py --displays 1
```

**Expected:**
- Processing window appears only on display 1
- Video plays smoothly

**Press Ctrl+C to stop**

---

### Test 3: Single Display (Display 2)

```bash
cd app
python3 carpet_hotel_pde.py --displays 2
```

**Expected:**
- Processing window appears only on display 2
- Video plays smoothly

**Press Ctrl+C to stop**

---

### Test 4: Reversed Displays

```bash
cd app
python3 carpet_hotel_pde.py --displays 2,1
```

**Expected:**
- Processing windows appear on displays 2 and 1 (reversed order)
- Videos play smoothly

**Press Ctrl+C to stop**

---

### Test 5: With Keyboard Control

```bash
cd app
python3 carpet_hotel_pde.py --keyboard
```

**Expected:**
- Processing windows appear
- Keyboard controls work:
  - `1-9`: Switch to scene
  - `UP/DOWN`: Next/previous scene
  - `D`: Toggle debug panel
  - `F`: Toggle fullscreen
  - `R`: Reload config
  - `SPACE`: Print info

**Press Ctrl+C to stop**

---

### Test 6: Via GUI Launcher

```bash
python3 app/carpet_hotel_gui.py
```

**Expected:**
- GUI control panel appears
- Can configure displays
- Can start/stop Processing
- Status updates correctly

---

### Test 7: Via Launch Script

```bash
./launch_macos.sh
```

**Expected:**
- Checks dependencies
- Installs missing components
- Launches GUI successfully

---

## Configuration Testing

### Test Different Display Combinations

Edit display numbers in various ways:

```bash
# Three displays
python3 app/carpet_hotel_pde.py --displays 1,2,3

# Different order
python3 app/carpet_hotel_pde.py --displays 3,1,2

# Just middle display
python3 app/carpet_hotel_pde.py --displays 2
```

---

## Troubleshooting

### If Processing doesn't start:

1. **Check processing-java is in PATH:**
   ```bash
   which processing-java
   ```

2. **Check Processing.app is installed:**
   ```bash
   ls -la /Applications/Processing.app
   ```

3. **Add to PATH if needed:**
   ```bash
   export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"
   ```

### If displays are wrong:

1. **List available displays:**
   ```bash
   python3 app/carpet_hotel_pde.py --list-displays
   ```

2. **Check system display settings:**
   ```bash
   system_profiler SPDisplaysDataType
   ```

### If videos don't play:

1. **Check data folder:**
   ```bash
   ls -la data/
   ```

2. **Verify video files exist:**
   ```bash
   ls -la data/*.mp4
   ```

3. **Check Processing video library:**
   - Open Processing IDE
   - Go to Sketch > Import Library > Add Library
   - Install "Video" library if missing

### If oscP5 errors occur:

1. **Install oscP5 library:**
   - Open Processing IDE
   - Go to Sketch > Import Library > Add Library
   - Search for "oscP5" and install

---

## Test Results Summary

| Configuration | Status | Notes |
|--------------|--------|-------|
| Display 1 only | ✓ PASS | Tested automatically |
| Display 2 only | ✓ PASS | Tested automatically |
| Displays [1, 2] | ✓ PASS | Tested automatically |
| Displays [2, 1] | ✓ PASS | Tested automatically |
| Keyboard enabled | ✓ PASS | Tested automatically |
| Keyboard disabled | ✓ PASS | Tested automatically |
| Start/stop lifecycle | ✓ PASS | Tested automatically |

---

## Quick Test Commands

Run all automated tests:
```bash
python3 app/tests/test_processing_comprehensive.py
```

Quick manual test:
```bash
cd app && python3 carpet_hotel_pde.py --keyboard
# Press numbers 1-9 to change scenes
# Press D to toggle debug
# Press Ctrl+C to stop
```

---

## Notes

- All automated tests passed with 100% success rate
- System has 2 displays detected (5120x1440 and 1728x1117)
- Processing launches successfully on all display configurations
- Process lifecycle (start/stop/restart) works correctly
- Both keyboard modes (enabled/disabled) function properly

For issues or questions, see:
- Main documentation: `README.md`
- Audio setup: `AUDIO_SETUP.md`
- Test suite code: `app/tests/test_processing_comprehensive.py`
