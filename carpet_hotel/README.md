# CARPET HOTEL

**A synchronized multi-screen video installation with audio**

---

## Quick Launch

### macOS
1. **Double-click** `launch_macos.sh`
2. If macOS blocks it: Right-click → Open → Open anyway
3. Follow the on-screen prompts to configure audio and displays
4. Click **Start**

### Windows
1. **Double-click** `launch_windows.bat`
2. If Windows blocks it: Click "More info" → "Run anyway"
3. Follow the on-screen prompts to configure audio and displays
4. Click **Start**

**That's it!** The installation will automatically:
- Install required software (first time only)
- Load all video and audio files
- Sync multiple screens
- Start playing

---

## Control Panel

When launched, a control panel appears with four setup pages:

### 1. Audio Setup
Choose which speakers/audio device to use for sound output.

**Tip:** Start with the default. If no sound, try "Built-in Output"

### 2. Display Setup
Select which monitors show the video floors.

**Tip:** Hover over a display name to see a preview on that screen!

### 3. Control Methods
Choose how to change scenes:
- **Keyboard** - Press 1-9 keys (good for testing)
- **Python Terminal** - Type scene numbers (good for manual control)
- **External OSC** - Arduino elevator controller (exhibition mode)

**Tip:** Enable all three during setup, disable keyboard for exhibition

### 4. Review & Start
Review your settings and click **Start**

---

## During Exhibition

### Pause
Click **Pause** to temporarily mute audio and pause videos
- Useful for making adjustments
- Click again to Resume

### Stop
Click **Stop** to fully stop all processes
- Keeps control panel open
- Use when changing major settings
- Click **Start** to relaunch

### Quit
Close the control panel window or click **Quit**

---

## Troubleshooting

**No video showing?**
- Check display selection on page 2
- Hover over display names to verify which screen is which

**No audio?**
- Try a different audio device on page 1
- Check system volume
- Restart and try "Automatic" audio device

**Videos out of sync?**
- Click **Stop**, then **Start** again
- This reloads all media files

**Elevator control not working?**
- Ensure "External OSC" is enabled on page 3
- Check Arduino is connected via USB
- See technical documentation in `app/README.md`

---

## File Structure

```
carpet_hotel/
├── launch_macos.sh         ← Launch script for Mac
├── launch_windows.bat      ← Launch script for Windows
├── README.md              ← This file (for gallery staff)
├── app/                   ← Application code (see app/README.md)
└── data/                  ← Video and audio files (see data/README.md)
```

---

## Technical Documentation

For developers and technical staff, see:
- **app/README.md** - Application architecture and code
- **data/README.md** - Media file requirements and naming

---

## Credits

Carpet Hotel Installation
Artist: Grey Muldoon
Technical Lead: John Janigan-Mills
