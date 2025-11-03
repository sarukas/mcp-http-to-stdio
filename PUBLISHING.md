# Publishing to PyPI

This document provides step-by-step instructions for publishing the `mcp-http-to-stdio` package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/
2. **API Token**: Generate an API token from https://pypi.org/manage/account/token/
3. **Build Tools**: Install required tools:
   ```bash
   pip install build twine
   ```

## Publishing Steps

### 1. Clean Previous Builds

```bash
cd packages/mcp-http-to-stdio
rm -rf dist/ build/ *.egg-info
```

### 2. Update Version Number

Edit `mcp_http_to_stdio/__init__.py` and `pyproject.toml`:

```python
# mcp_http_to_stdio/__init__.py
__version__ = "0.1.0"  # Increment as needed
```

```toml
# pyproject.toml
version = "0.1.0"  # Must match __init__.py
```

### 3. Build the Package

```bash
python -m build
```

This creates:
- `dist/mcp_http_to_stdio-0.1.0-py3-none-any.whl` (wheel distribution)
- `dist/mcp-http-to-stdio-0.1.0.tar.gz` (source distribution)

### 4. Check the Build

```bash
twine check dist/*
```

Expected output:
```
Checking dist/mcp_http_to_stdio-0.1.0-py3-none-any.whl: PASSED
Checking dist/mcp-http-to-stdio-0.1.0.tar.gz: PASSED
```

### 5. Test Upload to TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --no-deps mcp-http-to-stdio

# Test the command
mcp-http-to-stdio --help
```

### 6. Upload to PyPI (Production)

```bash
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your API token (starts with `pypi-...`)

### 7. Verify Installation

```bash
# Install from PyPI
pip install mcp-http-to-stdio

# Verify command works
mcp-http-to-stdio --help
```

## Updating the Package

When releasing a new version:

1. Update version in `__init__.py` and `pyproject.toml`
2. Update `README.md` with changes (if applicable)
3. Clean previous builds: `rm -rf dist/ build/ *.egg-info`
4. Build: `python -m build`
5. Upload: `twine upload dist/*`

## Version Numbering

Follow Semantic Versioning (https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backwards compatible)
- **PATCH** version for bug fixes (backwards compatible)

Examples:
- `0.1.0` - Initial release
- `0.1.1` - Bug fix
- `0.2.0` - New feature
- `1.0.0` - First stable release

## Troubleshooting

### "File already exists" error

If you get an error that the file already exists on PyPI:
- You cannot replace an existing release
- Increment the version number and rebuild

### Import errors after installation

Check that:
- `__init__.py` exports the `main` function
- `pyproject.toml` has correct console script entry point
- Package structure is correct (see `python -m build` output)

### Command not found after pip install

- Ensure pip's bin directory is in PATH
- On Windows: `%APPDATA%\Python\PythonXX\Scripts`
- On Linux/Mac: `~/.local/bin`

## Resources

- PyPI Documentation: https://packaging.python.org/
- PyPI Project Page (after publishing): https://pypi.org/project/mcp-http-to-stdio/
- Twine Documentation: https://twine.readthedocs.io/
