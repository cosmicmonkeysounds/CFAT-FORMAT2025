# macOS Setup Guide for Carpet Hotel

## Quick Fix for Video Library Issues

### Step 1: Install the Correct Library

In Processing:
1. Go to **Sketch → Import Library → Add Library...**
2. In the search box, type: **"Video"**
3. Look for **"Video | GStreamer-based video library for Processing"**
4. Author should be: **The Processing Foundation**
5. Click **Install**

### Step 2: Restart Processing

**Important**: After installing the library, completely quit and restart Processing. Not just close the window - actually quit the application (Cmd+Q).

### Step 3: Check Your Folder Structure

Make sure your files are organized like this:

```
carpet_hotel/
├── carpet_hotel.pde
└── data/
    └── carpets/
        ├── carpet1.mp4
        ├── carpet2.mp4
        └── carpet3.mp4
```

The `data` folder must be in the same directory as your `.pde` file!

## Common macOS Issues

### "Cannot open file" or Permission Errors

macOS Gatekeeper may block Processing from accessing files:
1. Go to **System Settings → Privacy & Security**
2. Scroll down to **Files and Folders**
3. Make sure Processing has access to the folders containing your videos

### GStreamer Not Found

If videos won't play:
1. The Video library should install GStreamer automatically
2. If it doesn't work, you may need to install GStreamer manually:
   - Visit: https://gstreamer.freedesktop.org/download/
   - Download the macOS installer
   - Install both the runtime and development packages

### Video Codecs

For best compatibility on macOS:
- **Format**: MP4
- **Video Codec**: H.264
- **Audio Codec**: AAC

You can convert videos using QuickTime Player:
1. Open video in QuickTime
2. **File → Export As... → 1080p** (or your desired resolution)
3. This creates an H.264 MP4 file

Or use FFmpeg (if you have Homebrew installed):
```bash
brew install ffmpeg
ffmpeg -i input.mov -c:v libx264 -preset slow -crf 22 -c:a aac output.mp4
```

## Testing the Setup

### Create a Test Video

If you don't have carpet videos yet, create a test:

1. Record a quick video with your iPhone/Mac camera (even just 5 seconds)
2. Export it from Photos as MP4
3. Rename it to `carpet1.mp4`
4. Put it in `data/carpets/` folder
5. Run the sketch!

### What You Should See

When the sketch runs correctly:
- The video plays in the window
- Console shows: `Loaded: carpet1.mp4 (duration: X.Xs)`
- Overlay shows floor info
- You can switch between floors with number keys (if you have multiple videos)

### If You See a Black Screen

Wait 2-3 seconds - videos take a moment to initialize. If still black:
1. Check the console for error messages
2. Verify the video file path is correct
3. Try a different video file
4. Make sure the video codec is H.264

## Performance Tips for macOS

### For Apple Silicon (M1/M2/M3) Macs

Processing 4 runs natively on Apple Silicon - you should get excellent performance!

### For Intel Macs

Performance should also be good. If you have issues:
- Keep video resolution at 1080p or lower
- Close other applications
- Make sure you're not running on battery saver mode

### Multiple Videos

The P3D renderer uses your GPU, so even Intel Macs with integrated graphics can handle 2-3 videos simultaneously.

## Why We're Not Using GLVideo

GLVideo has native library issues on macOS (especially Apple Silicon). The standard Video library:
- ✅ Works reliably out of the box
- ✅ No native library errors
- ✅ Maintained by Processing Foundation
- ✅ Still supports shaders via P3D renderer
- ✅ Better for your setup

## Still Having Issues?

1. **Check Processing version**: Make sure you're running Processing 4.x
2. **Check Java version**: Processing should handle this automatically
3. **Completely remove and reinstall**: 
   - Remove the Video library
   - Restart Processing
   - Reinstall the Video library
   - Restart Processing again

4. **Console output**: Copy any error messages - they're helpful for debugging!

## Next Steps

Once you have it working:
- Add more carpet videos (carpet2.mp4, carpet3.mp4, etc.)
- Try switching between floors with number keys
- Press SPACE to see detailed info
- Check out SHADER_GUIDE.md for visual effects!

---

Happy carpet hotel building! 🏨✨
