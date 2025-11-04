# Quick Fix: "No carpet videos found" Error

## The Problem
You see this error:
```
ERROR: No carpet videos found!
Place videos in the data folder...
```

## The Solution

### Step 1: Check Your Folder Structure

Your files should look **exactly** like this:

```
carpet_hotel/              ← Folder containing your sketch
├── carpet_hotel.pde       ← Your Processing sketch
└── data/                  ← Must be named "data" (lowercase)
    ├── carpet1.mp4        ← Your videos go here
    ├── carpet2.mp4
    └── carpet3.mp4
```

**Common Mistakes:**
- ❌ Videos in the same folder as the .pde file
- ❌ Folder named "Data" with capital D
- ❌ Videos in a "videos" or "carpets" folder without adjusting the code
- ❌ Using `carpet_1` but naming files `carpet-1` or `carpet 1`

### Step 2: Check Your Video Names

The code supports **two naming patterns**:
- ✅ `carpet1.mp4`, `carpet2.mp4`, `carpet3.mp4`
- ✅ `carpet_1.mp4`, `carpet_2.mp4`, `carpet_3.mp4`

**Must start with 1** (not 0):
- ✅ carpet1.mp4, carpet2.mp4
- ❌ carpet0.mp4, carpet1.mp4

**Must be sequential** (no gaps):
- ✅ carpet1.mp4, carpet2.mp4, carpet3.mp4
- ❌ carpet1.mp4, carpet3.mp4, carpet5.mp4

### Step 3: Check Your videoFolderPath Variable

In your sketch, find this line (around line 18):

```java
String videoFolderPath = "";
```

**If videos are directly in data/ folder:**
```java
String videoFolderPath = "";  // Empty string - correct!
```

**If videos are in data/carpets/ subfolder:**
```java
String videoFolderPath = "carpets/";  // Note the trailing slash
```

**WRONG - Don't do this:**
```java
String videoFolderPath = "./data/";       // ❌ Wrong
String videoFolderPath = "data/";         // ❌ Wrong
String videoFolderPath = "/data/";        // ❌ Wrong
String videoFolderPath = "data/carpets/"; // ❌ Wrong
```

Processing automatically looks in the `data` folder - you don't need to specify it!

### Step 4: Verify Your Video Format

**Best format:** H.264 MP4
```bash
# Check format on macOS:
Get Info on the file in Finder

# Or use ffmpeg if installed:
ffmpeg -i carpet1.mp4
```

**Convert if needed:**
```bash
# Using ffmpeg:
ffmpeg -i input.mov -c:v libx264 -preset slow -crf 22 carpet1.mp4
```

## Quick Test

1. **Create a test video:**
   - Record a 5-second video with your phone
   - Export as MP4
   - Name it `carpet1.mp4`
   - Put it in the `data` folder

2. **Set videoFolderPath:**
   ```java
   String videoFolderPath = "";
   ```

3. **Run the sketch**

4. **Check the console:**
   - ✅ Should see: `Loaded: carpet1.mp4 (duration: X.Xs)`
   - ❌ If error, see below

## Still Not Working?

### Check the Console Output

Look for specific error messages:

**"Cannot load movie file"**
- Video format issue - try converting to H.264 MP4

**"FileNotFoundException"**
- Path is wrong - double-check folder structure
- Make sure `data` folder is in the same directory as your .pde file

**"NullPointerException"**
- Video library might not be installed correctly
- Reinstall the Video library and restart Processing

### Debug Mode

Add this to your `setup()` function right after loading videos:

```java
// Debug: Print current directory and data path
println("Sketch folder: " + sketchPath());
println("Data folder: " + dataPath(""));
println("Looking for: " + dataPath(videoFolderPath + "carpet1.mp4"));

// Debug: List files in data folder
File dataFolder = new File(dataPath(""));
if (dataFolder.exists()) {
  println("\nFiles in data folder:");
  for (File file : dataFolder.listFiles()) {
    println("  - " + file.getName());
  }
} else {
  println("WARNING: data folder doesn't exist!");
}
```

This will show you exactly where Processing is looking for files.

## macOS-Specific Issues

### Gatekeeper/Permissions
If Processing can't access your files:
1. System Settings → Privacy & Security → Files and Folders
2. Allow Processing to access the folders

### Case Sensitivity
macOS is usually case-insensitive, but check:
- Folder must be `data` not `Data`
- Files should be `carpet1.mp4` not `Carpet1.mp4`

## Windows-Specific Issues

### Backslashes
If you need a subfolder, use forward slashes:
```java
String videoFolderPath = "carpets/";  // ✅ Correct
String videoFolderPath = "carpets\\"; // ❌ Wrong
```

### Hidden File Extensions
Make sure your files are really named `carpet1.mp4` and not `carpet1.mp4.mp4`:
1. Open File Explorer
2. View → File name extensions (check this box)
3. Verify file names

## Summary Checklist

- [ ] Video library installed and Processing restarted
- [ ] `data` folder exists in same directory as .pde file
- [ ] Videos are directly in `data` folder (or path is set correctly)
- [ ] Videos named `carpet1.mp4`, `carpet2.mp4`, etc. (starting at 1)
- [ ] Videos are H.264 MP4 format
- [ ] `videoFolderPath = ""` (empty string) if videos are in data/ root
- [ ] Console shows debug info about where it's looking

---

If you've checked all of this and it still doesn't work, copy the entire console output - it will show exactly what's going wrong!
