@echo off
setlocal EnableDelayedExpansion

echo ================================================
echo    Insightron v2.2.0 - Windows Installer
echo    Enhanced Whisper AI Transcription Tool
echo ================================================
echo.

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 - 3.12 from https://python.org
    pause
    exit /b 1
)

for /f %%I in ('python -c "import sys; print(sys.version_info.minor)"') do set PYTHON_MINOR=%%I

if %PYTHON_MINOR% geq 13 (
    echo.
    echo [WARNING] You are using Python 3.%PYTHON_MINOR%.
    echo           Many scientific packages ^(like onnxruntime^) do not yet support Python 3.13+.
    echo           This installation will likely fail.
    echo.
    echo           PLEASE INSTALL PYTHON 3.10, 3.11, or 3.12.
    echo.
    echo           Press Ctrl+C to cancel or any key to try anyway...
    pause
)

echo.
echo Installing Insightron dependencies for Windows...
echo.

REM Check for Rust/Cargo (needed for tokenizers on some systems)
cargo --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Cargo not found in PATH. Checking default install location...
    if exist "%USERPROFILE%\.cargo\bin\cargo.exe" (
        echo [INFO] Found Cargo at %USERPROFILE%\.cargo\bin
        set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
        echo [INFO] Added Cargo to PATH for this session.
    ) else (
        echo [WARNING] Rust/Cargo not found. If installation fails, you may need to install Rust.
        echo           Visit https://rustup.rs/ to install Rust.
    )
)

REM Get script directory for relative paths
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Upgrade pip first
echo [1/4] Upgrading pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo WARNING: pip upgrade failed, continuing anyway...
)

REM Install NumPy with pre-compiled wheel (Windows-specific)
echo.
echo [2/4] Installing NumPy...
python -m pip install numpy --prefer-binary --upgrade
if %errorlevel% neq 0 (
    echo ERROR: NumPy installation failed
    echo Please install Visual Studio Build Tools or try: conda install numpy
    pause
    exit /b 1
)

REM Install other dependencies
echo.
echo [3/4] Installing other dependencies...
if exist "setup\requirements.txt" (
    python -m pip install -r setup\requirements.txt --prefer-binary --no-cache-dir
) else if exist "requirements.txt" (
    python -m pip install -r requirements.txt --prefer-binary --no-cache-dir
) else (
    echo ERROR: requirements.txt not found
    echo Please run this script from the Insightron root directory
    pause
    exit /b 1
)
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Standard installation failed.
    echo           This is often due to missing pre-built wheels for your Python version.
    echo.
    echo           Attempting to install 'tokenizers' explicitly...
    python -m pip install tokenizers --prefer-binary
    
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] 'tokenizers' installation failed.
        echo         This usually means you need to install Rust to build it from source.
        echo.
        echo         Please install Rust from: https://rustup.rs/
        echo         Then run this installer again.
        echo.
        pause
        exit /b 1
    )

    echo.
    echo [INFO] Retrying full installation...
    python -m pip install -r setup/requirements.txt --prefer-binary --no-cache-dir
    if !errorlevel! neq 0 (
        echo.
        echo [WARNING] Some dependencies failed, trying minimal installation...
        if exist "setup\requirements-minimal.txt" (
            python -m pip install -r setup\requirements-minimal.txt --prefer-binary --no-cache-dir
        ) else if exist "requirements-minimal.txt" (
            python -m pip install -r requirements-minimal.txt --prefer-binary --no-cache-dir
        ) else (
            echo ERROR: requirements-minimal.txt not found
            pause
            exit /b 1
        )
        if !errorlevel! neq 0 (
            echo ERROR: Installation failed completely
            echo Please run: python scripts/troubleshoot.py
            pause
            exit /b 1
        )
    )
)

REM Verify installation
echo.
echo [4/4] Verifying installation...
python -c "import faster_whisper, librosa, numpy, customtkinter, sounddevice; print('All core dependencies working!')"
if errorlevel 1 (
    echo.
    echo [WARNING] Verification failed!
    echo           This might be due to a missing dependency or an incompatibility.
    echo.
    echo           Common fixes:
    echo           1. Install Visual Studio Build Tools (for C++ compilation)
    echo           2. Install Rust (for tokenizers): https://rustup.rs/
    echo           3. Ensure you are using Python 3.10 - 3.12
    echo.
    echo           Run: python scripts/troubleshoot.py for detailed diagnostics.
)

echo.
echo ================================================
echo    Installation Complete!
echo ================================================
echo.
echo You can now run Insightron:
echo   python insightron.py    # GUI mode (recommended)
echo   python cli.py audio.mp3  # Command line mode
echo.
echo For help: python scripts/troubleshoot.py
echo Documentation: README.md
echo.
pause
