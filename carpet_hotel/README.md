# CARPET HOTEL - Gallery Setup Guide
## For Gallery Staff & Non-Technical Artists

**A synchronized multi-screen video installation with audio and smooth floor transitions.**

---

## 🚀 Quick Launch

### macOS
1. **Double-click** `launch_macos.sh`
2. If macOS asks permission: right-click → Open → Open anyway
3. Control panel opens → Click **Start**

### Windows
1. **Double-click** `launch_windows.bat`
2. If Windows asks permission: "More info" → "Run anyway"
3. Control panel opens → Click **Start**

**That's it!** The launch scripts handle everything automatically.

---

## 🎛️ Control Panel Guide

### Page 1: Audio Setup
**Question:** Which speakers should the audio come from?

**Options:**
- **MacBook Pro Speakers** ← Safe default
- **Built-in Output** ← Try if default doesn't work
- **Multi-Output Device** ← For multiple speaker systems
- **Custom** ← Only if you know exact device name
- **Automatic** ← Let SuperCollider choose

**Tip:** If you hear no sound, try a different device and click Start again.

---

### Page 2: Display Setup
**Question:** Which monitors show the videos?

**Two lists:**
- **Available Displays** - All your monitors
- **Selected Displays** - What the installation uses

**How to use:**
1. **Hover** over display name → preview appears on that screen!
2. **Double-click** to move between lists
3. **Order matters:** First = Floor N, Second = Floor N+1

**Typical setup:** Two side-by-side monitors (Display 1 and Display 2)

---

### Page 3: Control Methods
**Question:** How should scenes change?

**Enable any combination:**
- ☑ **Keyboard Control** - Press 1-9 in Processing window
  - Good for: Testing, rehearsal
- ☑ **Python Terminal** - Type scene numbers in terminal
  - Good for: Manual control, troubleshooting
- ☑ **External OSC** - Arduino elevator controller
  - Good for: Exhibition mode

**Tip:** Enable all three during setup. Disable keyboard for exhibition.

**Note:** Mouse wheel volume control is always available.

---

### Page 4: Review & Start
Review your settings → Click **Start**

**Status shows:**
- Ready → Starting → Running
- **Stop** / **Pause** buttons appear

---

## 🎮 Running the Installation

### Stop Button
- Kills all processes
- Keeps control panel open
- Use when: Changing major settings

### Pause Button
- Mutes audio
- Pauses videos
- Use when: Making adjustments during exhibition
- Click again to **Resume**

### Quit
- Close control panel window, OR
- Click **Quit** button

---

## 🎹 Keyboard Controls (if enabled)

**In Processing window:**
- **1-9** - Jump to scenes 0-8
- **UP/DOWN arrows** - Next/previous scene
- **Mouse wheel** - Volume up/down
- **D** - Toggle debug info
- **F** - Toggle fullscreen
- **SPACE** - Print scene info
- **ESC** - Close all windows

---

## 💡 Exhibition Tips

### Before Opening
1. Launch the installation
2. Test all scenes (1-9 keys)
3. Verify displays are correct (check both screens)
4. Set volume with mouse wheel
5. Disable keyboard control if using Arduino

### During Exhibition
- **Pause** for quick adjustments (mutes audio, pauses video)
- **Stop** only if changing major settings (kills everything)
- Control panel stays open - no need to relaunch

### After Closing
- Click **Stop** or close window
- Settings are saved automatically for next time

---

## 🔧 Troubleshooting

### "SuperCollider failed to start"

**Symptoms:**
- No audio
- Error message about audio server
- Status stays on "Starting..."

**Fix:**
1. Click **Stop**
2. Go to **Page 1: Audio**
3. Try different audio device:
   - Switch from "MacBook Pro Speakers" to "Built-in Output"
   - Or try "Automatic"
4. Click **Start** again

**Still not working?**
- Check `carpet_hotel.log` file for errors
- Make sure no other audio app is using the device
- Restart your computer and try again

---

### "Videos not appearing"

**Symptoms:**
- Black screens
- Processing windows open but show nothing
- Error about missing videos

**Fix:**
1. Check `data/` folder contains:
   - `carpet_1.mp4`, `carpet_2.mp4`, etc.
   - At least 2-10 video files
2. Verify videos are H.264 MP4 format
3. Check file names match exactly (underscore, not dash)

**Test videos:**
- Right-click video file → Open With → VLC/QuickTime
- If it plays there, it should work in installation

---

### "Windows on wrong screens"

**Symptoms:**
- Video appears on laptop instead of external monitor
- Both videos on same screen
- Preview windows don't match actual windows

**Fix:**
1. Click **Stop**
2. Go to **Page 2: Displays**
3. **Hover** over display names - preview shows on actual screen
4. **Double-click** to rearrange order
5. Make sure selected displays match your physical setup
6. Click **Start** again

**Still wrong?**
- Check monitor cables are connected
- Check Display Settings in System Preferences (macOS) or Settings (Windows)
- Restart installation after changing monitor setup

---

### "Installation keeps crashing"

**Symptoms:**
- Windows close immediately
- "Error" status in control panel
- Crashes after a few seconds

**Fix:**
1. Check `carpet_hotel.log` for error details
2. Close control panel completely
3. Launch again (settings are saved)
4. Try with minimal settings:
   - Only 2 displays
   - Keyboard control only
   - Default audio device

**Common causes:**
- Too many displays (try 2 first)
- Missing video/audio files in `data/` folder
- Incorrect audio device selected

---

### "Mouse wheel not changing volume"

**Symptoms:**
- Scrolling does nothing
- Volume doesn't change

**Fix:**
1. Make sure cursor is **over a Processing window**
2. Click on the Processing window first to focus it
3. Then try mouse wheel
4. Volume changes are sent to SuperCollider

**Note:** Volume control works regardless of input mode settings.

---

### "Keyboard shortcuts not working"

**Symptoms:**
- Pressing 1-9 does nothing
- Arrow keys don't change scenes

**Check:**
1. Is **Keyboard Control** enabled in settings?
   - Stop → Page 3 → Check "Keyboard Control" → Start
2. Is a Processing window focused?
   - Click on a Processing window first
3. Are you pressing keys in the **Processing window** (not control panel)?

---

### "Can't find launch script"

**Symptoms:**
- Double-clicking doesn't work
- Script won't run
- Permission denied errors

**macOS Fix:**
1. Right-click `launch_macos.sh`
2. Click **Open**
3. Click **Open** again in warning dialog
4. If still blocked: System Settings → Privacy & Security → Allow

**Windows Fix:**
1. Right-click `launch_windows.bat`
2. Click **"Run as administrator"** if prompted
3. Or: Click **"More info"** → **"Run anyway"**

---

### "Settings not saving"

**Symptoms:**
- Have to reconfigure every time
- Display order resets
- Audio device resets

**Fix:**
1. Check file permissions in installation folder
2. Look for `.carpet_hotel_config.json` file
   - Should be created automatically
   - Contains your saved settings
3. If missing, check you have write permissions
4. macOS: Right-click folder → Get Info → check permissions

---

### "Processing/SuperCollider not installed"

**Symptoms:**
- "Processing not found" error
- "SuperCollider not found" error
- Launch script fails

**Fix:**
The launch scripts try to install automatically, but if that fails:

**Manual Installation:**

**macOS:**
1. Processing: Download from https://processing.org/download
2. SuperCollider: `brew install --cask supercollider`
   - Or download from https://supercollider.github.io/downloads
3. Python: Usually pre-installed, or `brew install python3`

**Windows:**
1. Processing: Download from https://processing.org/download
2. SuperCollider: Download from https://supercollider.github.io/downloads
3. Python: Download from https://www.python.org/downloads/

Then run launch script again.

---

### "First time setup required"

**Symptoms:**
- Launch script asks to install oscP5
- Pause for manual installation

**Fix:**
1. Open Processing IDE (not the installation)
2. Click **Sketch → Import Library → Add Library...**
3. Search for **"oscP5"**
4. Click **Install**
5. Close Processing IDE
6. Return to launch script and press Enter

**Only needed once!** After this, everything is automatic.

---

## 📂 File Checklist

Before running, make sure you have:

```
carpet_hotel/
├── launch_macos.sh or launch_windows.bat  ✓
├── run_carpet_hotel.py                     ✓
├── carpet_hotel.pde                        ✓
├── carpet_hotel_audio.scd                  ✓
└── data/
    ├── carpet_1.mp4  ✓
    ├── carpet_2.mp4  ✓
    ├── carpet_1.wav  ✓
    ├── carpet_2.wav  ✓
    └── ... (up to carpet_10)
```

**Video requirements:**
- Format: H.264 MP4
- Resolution: 1920×1080 recommended
- Naming: `carpet_N.mp4` (underscore, not dash)

**Audio requirements:**
- Format: Stereo WAV, 44.1kHz
- Naming: `carpet_N.wav` (matches video number)

---

## 📞 Getting Help

If something isn't working:

1. **Check the log:**
   - Look for `carpet_hotel.log` in installation folder
   - Shows detailed error messages

2. **Take notes:**
   - What were you doing?
   - What error message appeared?
   - Which step in this guide were you on?

3. **Screenshot the control panel:**
   - Shows your settings
   - Shows error messages

4. **Contact technical team with:**
   - Description of problem
   - Log file content
   - Screenshot of control panel
   - What you already tried

---

## 🔄 Common Workflows

### Daily Exhibition Setup
1. Double-click launch script
2. Control panel opens (settings already loaded)
3. Click **Start**
4. Done!

### Changing Settings Mid-Exhibition
1. Click **Pause** (keeps everything running)
2. Make adjustments in gallery
3. Click **Resume**

### Major Changes (Different Displays, Audio)
1. Click **Stop**
2. Adjust settings in control panel
3. Click **Start**
4. Test everything

### End of Day
1. Click **Stop** or close control panel
2. All processes killed cleanly
3. Settings saved for tomorrow

---

## 🆘 Emergency Procedures

### If Installation Freezes
1. Close control panel window
2. Check Activity Monitor (macOS) / Task Manager (Windows)
3. Force quit: Processing, SuperCollider, Python
4. Relaunch

### If Computer Crashes
1. Restart computer
2. Launch installation normally
3. Settings are saved - just click Start

### If Videos Are Corrupted
1. Stop installation
2. Replace bad video files in `data/` folder
3. Keep same naming convention
4. Start installation again

---

**For technical details and advanced setup:** See [README_TECHNICAL.md](README_TECHNICAL.md)

**Your settings are always saved!** The installation remembers your configuration between sessions.
