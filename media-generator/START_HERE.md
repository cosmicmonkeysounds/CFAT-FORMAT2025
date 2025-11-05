# 👋 Welcome to Media Generator!

## 🚀 Quick Start (Recommended)

**Just want to run it? Use our smart launcher scripts!**

### Interactive Mode (No Command Line Knowledge Needed!)
Simply double-click or run without arguments for a guided experience:

```bash
# macOS / Linux
./run-macos-linux.sh

# Windows
run-windows.bat
```

You'll be guided through all options step-by-step!

### Command Line Mode
```bash
# macOS / Linux
./run-macos-linux.sh 10 -t mp4 --embed-audio

# Windows
run-windows.bat 10 -t mp4 --embed-audio
```

**That's it!** The launcher automatically:
- Installs Python if needed
- Creates a virtual environment
- Installs all dependencies (including bundled ffmpeg!)
- Runs the program

→ Read **[LAUNCHER_README.md](LAUNCHER_README.md)** for complete launcher documentation

---

## Choose Your Path:

### 🎨 **I'm a Gallery Staff Member / Non-Technical User**
→ Read **[USER_GUIDE.md](USER_GUIDE.md)**
- Step-by-step installation
- Simple command examples
- Troubleshooting help
- No programming knowledge needed

### 💻 **I'm a Developer**
→ Read **[README.md](README.md)**
- Technical documentation
- Package structure
- API details
- Development workflow

### ⚡ **I Just Need Commands**
→ Read **[QUICKSTART.md](QUICKSTART.md)**
- Quick installation
- Common commands
- Copy-paste examples

### 📦 **I Want to Understand the Package**
→ Read **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**
- File/folder explanations
- What each file does
- Why we have requirements.txt
- Build and distribution info

### 🎯 **I Want to Use the Launchers**
→ Read **[LAUNCHER_README.md](LAUNCHER_README.md)**
- Smart launcher scripts (macOS/Linux/Windows)
- Automatic setup and dependency management
- No manual installation needed!

### 🚀 **I Want to Distribute This**
→ Read **[PACKAGING_SUMMARY.md](PACKAGING_SUMMARY.md)**
- How to build executables
- Cross-platform builds
- GitHub Actions setup
- PyPI publishing

---

## Quick Command Examples

Using the launcher scripts:

```bash
# macOS/Linux
./run-macos-linux.sh                      # Interactive mode (guided)
./run-macos-linux.sh 10 -t mp4            # Generate 10 videos
./run-macos-linux.sh 10 -t jpg            # Generate 10 images
./run-macos-linux.sh 10 -t wav            # Generate 10 audio files
./run-macos-linux.sh 5 -t mp4 --embed-audio   # Videos with audio
./run-macos-linux.sh --help               # Show all options

# Windows
run-windows.bat                           # Interactive mode (guided)
run-windows.bat 10 -t mp4                 # Generate 10 videos
run-windows.bat 10 -t jpg                 # Generate 10 images
run-windows.bat 10 -t wav                 # Generate 10 audio files
run-windows.bat 5 -t mp4 --embed-audio    # Videos with audio
run-windows.bat --help                    # Show all options
```

---

**Not sure where to start?** → Use interactive mode: `./run-macos-linux.sh` (or `run-windows.bat` on Windows)
