@echo off
REM AI Coding Assistant Evaluation Framework - Windows Setup Script
REM This script sets up the development environment and installs dependencies

setlocal EnableDelayedExpansion

echo 🚀 AI Coding Assistant Evaluation Framework Setup
echo ==================================================

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [INFO] Please install Python 3.8+ from https://python.org
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [SUCCESS] Python !PYTHON_VERSION! found
)

REM Check Python version (basic check for 3.x)
for /f "tokens=1 delims=." %%i in ("!PYTHON_VERSION!") do set MAJOR_VERSION=%%i
if !MAJOR_VERSION! LSS 3 (
    echo [ERROR] Python 3.8 or higher is required. Found: !PYTHON_VERSION!
    pause
    exit /b 1
)

REM Check if pip is available
echo [INFO] Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available
    echo [INFO] Please reinstall Python with pip or install pip manually
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python -m pip --version 2^>^&1') do set PIP_VERSION=%%i
    echo [SUCCESS] pip !PIP_VERSION! found
)

REM Remove existing virtual environment if it exists
if exist "venv" (
    echo [WARNING] Virtual environment already exists. Removing old environment...
    rmdir /s /q venv
)

REM Create virtual environment
echo [INFO] Setting up virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated

REM Upgrade pip in virtual environment
echo [INFO] Upgrading pip in virtual environment...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing...
) else (
    echo [SUCCESS] pip upgraded
)

REM Install dependencies
echo [INFO] Installing Python dependencies...
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed

REM Create data directories
echo [INFO] Creating data directories...
if not exist "data" mkdir data
if not exist "data\raw" mkdir data\raw
if not exist "data\processed" mkdir data\processed
if not exist "data\backups" mkdir data\backups
if not exist "reports" mkdir reports
if not exist "reports\generated" mkdir reports\generated
echo [SUCCESS] Data directories created

REM Initialize database
echo [INFO] Initializing database...
python -m src.database.database
if errorlevel 1 (
    echo [ERROR] Failed to initialize database
    pause
    exit /b 1
)
echo [SUCCESS] Database initialized

REM Create startup scripts
echo [INFO] Creating startup scripts...

REM Create activation script
(
echo @echo off
echo REM Activate the AI Coding Evaluation Framework environment
echo.
echo echo 🔧 Activating AI Coding Evaluation Framework...
echo.
echo REM Activate virtual environment
echo if exist "venv\Scripts\activate.bat" ^(
echo     call venv\Scripts\activate.bat
echo     echo ✅ Virtual environment activated
echo.
echo     REM Add current directory to Python path
echo     set PYTHONPATH=%%PYTHONPATH%%;%%CD%%
echo.
echo     echo 🚀 Framework ready! Available commands:
echo     echo   python -m src.logging.cli --help    # Show CLI help
echo     echo   python -m src.logging.cli init      # Initialize database
echo     echo   python -m src.logging.cli start     # Start evaluation session
echo     echo.
echo     echo 📖 See docs\ARCHITECTURE.md for more information
echo ^) else ^(
echo     echo ❌ Virtual environment not found. Run setup.bat first.
echo ^)
) > activate.bat

echo [SUCCESS] Activation script created (activate.bat)

REM Test installation
echo [INFO] Testing installation...

REM Test database module
python -m src.database.database >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Database module test failed
    pause
    exit /b 1
)
echo [SUCCESS] Database module working

REM Test CLI module
python -m src.logging.cli --help >nul 2>&1
if errorlevel 1 (
    echo [ERROR] CLI module test failed
    pause
    exit /b 1
)
echo [SUCCESS] CLI module working

echo [SUCCESS] Installation test passed

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Run: activate.bat
echo 2. Test: python -m src.logging.cli init
echo 3. Start using: python -m src.logging.cli start
echo.
echo 📚 Documentation: docs\ARCHITECTURE.md
echo 🐛 Issues: Create an issue in the project repository
echo.

pause