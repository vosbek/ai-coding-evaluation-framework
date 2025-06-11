# Installation Guide

## Quick Start

### Linux/macOS
```bash
# Clone or navigate to the project directory
cd ai-coding-evaluation-framework

# Run setup script
chmod +x setup.sh
./setup.sh

# Activate environment
source activate.sh

# Test installation
python -m src.logging.cli init
```

### Windows
```cmd
# Navigate to the project directory
cd ai-coding-evaluation-framework

# Run setup script
setup.bat

# Activate environment
activate.bat

# Test installation
python -m src.logging.cli init
```

## Prerequisites

### All Platforms
- Python 3.8 or higher
- pip (Python package installer)
- Git (for version control integration)

### Platform-Specific Requirements

#### Linux
**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install python3 python3-pip python3-venv git
# or on newer versions:
sudo dnf install python3 python3-pip python3-venv git
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip git
```

#### macOS
**Using Homebrew (recommended):**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python3 git
```

**Using Python.org installer:**
1. Download Python from [python.org](https://python.org)
2. Install Git from [git-scm.com](https://git-scm.com)

#### Windows
1. **Python**: Download from [python.org](https://python.org)
   - ✅ Check "Add Python to PATH" during installation
   - ✅ Check "Install pip"
2. **Git**: Download from [git-scm.com](https://git-scm.com)

## Manual Installation

If the setup scripts don't work, follow these manual steps:

### 1. Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python -m src.database.database
```

### 4. Test Installation
```bash
python -m src.logging.cli --help
python -m src.logging.cli init
```

## Verification

After installation, verify everything works:

```bash
# Check database
python -m src.logging.cli info

# Start a test session
python -m src.logging.cli start

# List available commands
python -m src.logging.cli --help
```

## Directory Structure After Installation

```
ai-coding-evaluation-framework/
├── venv/                     # Virtual environment
├── data/                     # Data storage
│   ├── evaluation_framework.db  # SQLite database
│   ├── raw/                  # Raw test data
│   ├── processed/           # Processed data
│   └── backups/             # Database backups
├── reports/generated/       # Generated reports
├── activate.sh             # Linux/macOS activation script
├── activate.bat            # Windows activation script
└── ...
```

## Troubleshooting

### Common Issues

**"python command not found"**
- Linux/macOS: Use `python3` instead of `python`
- Windows: Python not in PATH - reinstall Python with "Add to PATH" option

**"pip command not found"**
- Try `python -m pip` or `python3 -m pip`
- Reinstall Python with pip option enabled

**"ModuleNotFoundError: No module named 'sqlalchemy'"**
- Virtual environment not activated
- Run `source activate.sh` (Linux/macOS) or `activate.bat` (Windows)

**Permission denied on Linux/macOS**
- Make setup script executable: `chmod +x setup.sh`
- Don't use `sudo` with pip in virtual environment

**Virtual environment activation fails**
- Delete `venv` folder and run setup script again
- Check Python installation is complete

### Getting Help

1. Check this documentation
2. Review error messages carefully
3. Ensure all prerequisites are installed
4. Try manual installation steps
5. Create an issue in the project repository

## Development Setup

For development work, install additional dependencies:

```bash
# Activate environment first
source activate.sh  # or activate.bat on Windows

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Run tests
pytest

# Format code
black src/

# Check code quality
flake8 src/
mypy src/
```

## Uninstallation

To remove the framework:

1. Deactivate virtual environment: `deactivate`
2. Delete project directory
3. Remove any global Python packages if installed with `pip install -e .`