# Project Structure Explained

This document explains what each file and folder in this project does.

## 📁 Directory Structure

```
media-generator/
├── 📄 USER_GUIDE.md              ← START HERE (non-technical users)
├── 📄 README.md                  ← Technical documentation
├── 📄 QUICKSTART.md              ← Quick command reference
├── 📄 PROJECT_STRUCTURE.md       ← This file
│
├── 📦 media_generator/           ← Main Python package
│   ├── __init__.py              ← Package initialization
│   └── __main__.py              ← Core application code
│
├── 🔧 pyproject.toml             ← Package configuration (pip install)
├── 📋 requirements.txt           ← Python dependencies list
├── 📄 MANIFEST.in                ← Files to include in distribution
├── 📄 LICENSE                    ← MIT License
├── 🚫 .gitignore                 ← Git ignore rules
│
├── 🏗️  build_executable.py       ← Script to create standalone .exe files
├── 📄 PACKAGING_SUMMARY.md       ← How the package was created (for developers)
│
└── 🤖 .github/workflows/         ← Automated builds (GitHub Actions)
    └── build.yml                ← CI/CD configuration
```

## 📚 Documentation Files

### For Users
- **`USER_GUIDE.md`** ⭐ - Simple guide for non-programmers. Start here if you're not a developer.
- **`QUICKSTART.md`** - Quick command reference for common tasks
- **`README.md`** - Complete technical documentation

### For Developers
- **`PACKAGING_SUMMARY.md`** - How this package was created, distribution methods
- **`PROJECT_STRUCTURE.md`** - This file, explains the project layout

## 🐍 Python Package Files

### Core Code
- **`media_generator/__init__.py`** - Package entry point, version info
- **`media_generator/__main__.py`** - Main application logic (all the media generation code)

### Configuration
- **`pyproject.toml`** - Modern Python package configuration
  - Defines package metadata (name, version, description)
  - Lists dependencies
  - Creates command-line tools (`media-generator`, `mediagen`)
  - Required for `pip install`

- **`requirements.txt`** - Simple list of dependencies
  - Useful for: `pip install -r requirements.txt`
  - Many people expect this file
  - Kept for compatibility and convenience
  - **Status: Keep it** - not redundant, serves a purpose

- **`MANIFEST.in`** - Tells pip which extra files to include
  - Includes README, LICENSE, etc. in the package

## 🏗️ Build and Distribution

- **`build_executable.py`** - Creates standalone executables
  - Runs PyInstaller
  - Creates single-file applications
  - Users don't need Python installed to run the executable
  - Creates files in `dist/` folder

- **`.github/workflows/build.yml`** - Automated builds
  - Runs when you push a version tag (e.g., `v1.0.0`)
  - Builds executables for Windows, macOS, Linux
  - Creates GitHub Releases automatically

## 🔐 Legal and Configuration

- **`LICENSE`** - MIT License (open source, free to use)
- **`.gitignore`** - Files that Git should ignore
  - Build artifacts
  - Python cache files
  - Generated media files
  - Virtual environments

## ❓ Do We Need requirements.txt?

**Yes, keep it!** Even though `pyproject.toml` also lists dependencies, `requirements.txt` is useful because:

1. **Familiarity** - Most Python users know `pip install -r requirements.txt`
2. **Simplicity** - Single-purpose file, easy to understand
3. **Compatibility** - Older tools and workflows expect it
4. **Quick testing** - Fast way to install just the runtime dependencies
5. **Docker/CI** - Many deployment tools look for this file

**They serve different purposes:**
- `pyproject.toml` - Full package configuration (installation, metadata, scripts)
- `requirements.txt` - Quick dependency installation (development, testing)

## 🗂️ Generated Folders (Not in Git)

These folders are created automatically and are not tracked by Git:

- **`dist/`** - Built executables and distribution packages
- **`build/`** - Temporary build files
- **`*.egg-info/`** - Package metadata
- **`__pycache__/`** - Python bytecode cache
- **`test_media/`** - Default output folder for generated files

## 🚀 What Files Do Users Need?

### If Using Python Package:
Users need everything in this folder for `pip install`

### If Using Executable:
Users only need:
- `dist/media-generator` (or `media-generator.exe` on Windows)
- Optionally: `USER_GUIDE.md` for instructions

That's it! The executable is completely standalone.

## 🔄 Typical Workflows

### For End Users (Gallery Staff)
1. Get the executable file
2. Read `USER_GUIDE.md`
3. Run the executable
4. Done!

### For Developers
1. Clone the repository
2. Run `pip install -e .`
3. Edit `media_generator/__main__.py`
4. Test: `media-generator 5 -t mp4`
5. Build: `python3 build_executable.py`

### For Package Maintainers
1. Edit code in `media_generator/`
2. Update version in `pyproject.toml` and `media_generator/__init__.py`
3. Test locally
4. Commit and tag: `git tag v1.0.0`
5. Push tag: GitHub Actions builds automatically
6. (Optional) Publish to PyPI: `python3 -m build && twine upload dist/*`

## 📦 What Gets Distributed?

### Via GitHub Releases (Automatic)
- `media-generator` (macOS executable)
- `media-generator` (Linux executable)
- `media-generator.exe` (Windows executable)

### Via PyPI (If Published)
- Entire package (all Python files)
- Users install with: `pip install media-generator`

### Via Git Clone
- Everything except `dist/`, `build/`, and generated files

## 🧹 Files That Could Be Removed (But Shouldn't)

Some files might seem redundant but serve important purposes:

- ✅ **Keep requirements.txt** - Useful for quick installs and compatibility
- ✅ **Keep MANIFEST.in** - Ensures LICENSE and README are included in pip packages
- ✅ **Keep PACKAGING_SUMMARY.md** - Helpful for understanding how to maintain/distribute
- ✅ **Keep all documentation** - Different audiences need different guides

## 🆕 Files Added During Packaging

These were added to transform the simple script into a distributable package:

**New files:**
- `media_generator/__init__.py` (package initialization)
- `pyproject.toml` (package configuration)
- `build_executable.py` (create executables)
- `MANIFEST.in` (distribution files)
- `LICENSE` (legal)
- `.gitignore` (git configuration)
- `.github/workflows/build.yml` (CI/CD)
- Documentation: `USER_GUIDE.md`, `QUICKSTART.md`, `PACKAGING_SUMMARY.md`, `PROJECT_STRUCTURE.md`

**Moved files:**
- `media_generator.py` → `media_generator/__main__.py`

**Unchanged files:**
- `requirements.txt` (still useful)
- `README.md` (enhanced but same purpose)

## Summary

This is a **professional Python package** with:
- ✅ Clean, standard structure
- ✅ Multiple installation methods
- ✅ Executable builds for non-Python users
- ✅ Comprehensive documentation for all audiences
- ✅ Automated builds via GitHub Actions
- ✅ No redundant files (everything has a purpose)

Ready for distribution to technical and non-technical users alike!
