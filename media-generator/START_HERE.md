# 👋 Welcome to Media Generator!

## 🚀 Quick Start (Recommended)

**Just want to run it? Use our smart launcher scripts!**

### macOS / Linux
```bash
./run.sh 10 -t mp4 --embed-audio
```

### Windows
```cmd
run.bat 10 -t mp4 --embed-audio
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
./run.sh 10 -t mp4                    # Generate 10 videos
./run.sh 10 -t jpg                    # Generate 10 images
./run.sh 10 -t wav                    # Generate 10 audio files
./run.sh 5 -t mp4 --embed-audio       # Videos with audio
./run.sh --help                       # Show all options

# Windows
run.bat 10 -t mp4                     # Generate 10 videos
run.bat 10 -t jpg                     # Generate 10 images
run.bat 10 -t wav                     # Generate 10 audio files
run.bat 5 -t mp4 --embed-audio        # Videos with audio
run.bat --help                        # Show all options
```

---

**Not sure where to start?** → Use the launcher: `./run.sh --help` (or `run.bat --help` on Windows)
