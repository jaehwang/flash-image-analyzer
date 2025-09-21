# AGENTS.md

This file provides guidance to AI coding agent when working with code in this repository.

## Project Overview

This is a Flash Image Analysis Tool for embedded systems, specifically focused on analyzing and validating firmware images used in embedded devices. The project is written in Python and provides CLI tools for analyzing flash images from various chipset platforms.

### Key Components

- **Package Name**: `gangimg` - CLI tool for flash image analysis
- **Primary Platform**: Qualcomm (MBN format support)
- **Core Functionality**:
  - Flash image parsing and partition detection
  - Filesystem analysis (ext2/3/4, SquashFS, UBIFS, JFFS2, YAFFS2)
  - Memory layout validation
  - Partition extraction capabilities
- **Target Users**: Embedded system developers, firmware engineers, security researchers

### Project Structure

```
src/gangimg/
├── core/           # Core analysis engine and models
├── platforms/      # Platform-specific analyzers (Qualcomm, etc.)
├── analyzers/      # Filesystem and content analyzers
├── utils/          # Utility functions (formatting, validation)
└── cli.py          # Command-line interface

scripts/            # Development and sample generation scripts
tests/              # Test suite including integration tests
```

### Current Platform Support

- ✅ **Qualcomm**: MBN (Multi-Boot Image) format, TrustZone structure
- 📋 **Planned**: Broadcom (CFE, TRX), MediaTek (Preloader), Marvell (U-Boot)

## Build System

This project uses modern Python tooling with `uv` as the primary package manager and task runner.

### Package Manager: uv (Recommended)

- **Primary tool**: `uv` for dependency management and virtual environment handling
- **Fallback**: Traditional `pip` with manual virtual environment setup
- **Configuration**: `pyproject.toml` with setuptools backend

### Available Make Targets

**Development Setup**:
- `make install-dev` - Install with development dependencies using uv
- `make dev-setup` - Complete development environment setup (includes pre-commit hooks)

**Code Quality**:
- `make lint` - Run flake8 and mypy checks
- `make format` - Auto-format code with black and isort
- `make format-check` - Check formatting without making changes
- `make check-all` - Run all checks (format, lint, test)

**Testing**:
- `make test` - Run pytest test suite
- `make test-cov` - Run tests with coverage reporting

**Sample Generation and Analysis**:
- `make sample` - Generate test flash image samples
- `make example` - Run example analysis on generated samples
- `make example-help` - Show CLI help

**Utilities**:
- `make clean` - Remove build artifacts and cache files
- `make install-hooks` - Install pre-commit hooks

### Python Requirements

- **Minimum Python**: 3.8.1+
- **Recommended Python**: 3.9+ (for mypy configuration)
- **No external dependencies**: Core functionality uses only Python standard library

### Development Dependencies

- **Testing**: pytest, pytest-cov
- **Code Quality**: black, flake8, mypy, isort
- **Pre-commit**: pre-commit hooks for automated checks

### Typical Development Workflow

1. `make dev-setup` - Set up development environment
2. Make code changes
3. `make check-all` - Verify code quality
4. `make test` - Run tests
5. `make sample && make example` - Test with sample data
