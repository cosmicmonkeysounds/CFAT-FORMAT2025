# Carpet Hotel - Media Files

**Video and audio content for the installation**

This directory contains all media files. Files are auto-detected on launch - no configuration needed.

---

## File Naming

```
carpet_N.mp4    # Video for floor N
carpet_N.wav    # Audio for floor N
```

Floor numbering starts at 1. Each floor can have video only, or video + audio.

---

## Current Files

- **Videos:** 9 files (carpet_2.mp4 through carpet_10.mp4)
- **Audio:** 10 files (carpet_1.wav through carpet_10.wav)

**Note:** Floor 1 has audio but no video, so it's skipped.

---

## File Specifications

### Video (`.mp4`)

**Required:**
- Format: H.264 MP4
- Resolution: 1920×1080
- Frame Rate: 30 fps
- Codec: H.264

**Recommended:**
- Bitrate: 5-10 Mbps
- No embedded audio (use separate .wav)

### Audio (`.wav`)

**Required:**
- Format: WAV (uncompressed)
- Sample Rate: 44.1 kHz
- Bit Depth: 16-bit
- Channels: 2 (stereo)

**Note:** Audio loops automatically - ensure clean start/end points.

---

## Adding New Media

1. **Encode video:**
   ```bash
   ffmpeg -i input.mov -c:v libx264 -s 1920x1080 -r 30 -b:v 8M -an carpet_11.mp4
   ```

2. **Encode audio:**
   ```bash
   ffmpeg -i input.mp3 -ar 44100 -ac 2 -sample_fmt s16 carpet_11.wav
   ```

3. **Copy to this directory:**
   ```bash
   cp carpet_11.mp4 carpet_hotel/data/
   cp carpet_11.wav carpet_hotel/data/
   ```

4. **Restart application** - files are auto-detected!

---

## Troubleshooting

**Video not loading:**
- Verify H.264 codec: `ffmpeg -i carpet_N.mp4`
- Re-encode with FFmpeg command above

**Audio not playing:**
- Check format: `file carpet_N.wav` (should show "WAVE audio")
- Verify 44.1kHz stereo

**Poor performance:**
- Reduce bitrate (try 5 Mbps)
- Ensure all videos are 30fps
- Use SSD storage

**Audio clicks/pops:**
- Add short fade in/out (10-50ms)
- Ensure clean loop points

---

## Technical Details

**File Discovery:**
- Videos: Processing scans `data/` for `carpet_*.mp4` files
- Audio: SuperCollider loads `carpet_*.wav` files on startup

**Loading:**
- Videos: On-demand during transitions, cached in memory
- Audio: Pre-loaded into SuperCollider buffers

**Storage:**
- Videos: ~600 MB (9 files × ~65 MB avg)
- Audio: ~8.6 MB (10 files × ~860 KB)

---

For technical docs, see `../app/README.md`
