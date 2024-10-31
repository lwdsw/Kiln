# Desktop Apps

## MacOS Environment Setup

Something similar probably needed on other platforms.

Basic idea: install system python including TK/TCL, and tell UV venv to use that.

Currently has to be python 3.12.

```
# Install python 3.12 and python-tk 3.12 with homebrew. Can't UV python, it doens't have TK.
brew install python-tk@3.12
brew install python@3.12

# check uv can see it hoembrew version
uv python list --python-preference only-system

# setup 3.12 uv-managed venv with system (homebrew) python 3.12
uv venv --python 3.12 --python-preference only-system

# Check it worked
uv run python --version

# Run desktop
uv run python -m app.desktop.desktop
```

## MacOS Code Signing

How to sign on of the builds from GitHub Actions for official release.

Easy way, but just signs with personal ID, not developer ID: `codesign --force --deep -s - kiln.app`

Proper way with a developer ID:

1. Get developer ID name: `security find-identity -v -p codesigning`
2. Run `codesign --force --deep -s "Developer ID Application: YOUR NAME (XXXXXXXX)" kiln.app`
