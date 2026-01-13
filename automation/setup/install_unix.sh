#!/bin/bash
# Insightron v2.2.0 - Unix/Linux Installer
# Enhanced Whisper AI Transcription Tool
# Compatible with Linux and macOS

set -e  # Exit on error

echo "================================================"
echo "   Insightron v2.2.0 - Unix/Linux Installer"
echo "   Enhanced Whisper AI Transcription Tool"
echo "================================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect Python executable
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.10 - 3.12 from https://python.org"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

echo "Detected Python: $PYTHON_VERSION"
echo ""

if [ "$PYTHON_MINOR" -ge 13 ]; then
    echo "[WARNING] You are using Python 3.$PYTHON_MINOR."
    echo "          Many scientific packages (like onnxruntime) do not yet support Python 3.13+."
    echo "          This installation will likely fail."
    echo ""
    echo "          PLEASE INSTALL PYTHON 3.10, 3.11, or 3.12."
    echo ""
    read -p "          Press Enter to continue anyway, or Ctrl+C to cancel..."
fi

# Check Python version compatibility (minimum 3.10)
PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "ERROR: Python 3.10 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo ""
echo "Installing Insightron dependencies for Unix/Linux..."
echo ""

# Check for Rust/Cargo
if command -v cargo &> /dev/null; then
    echo "[INFO] Rust/Cargo found in PATH"
elif [ -f "$HOME/.cargo/bin/cargo" ]; then
    echo "[INFO] Found Cargo at $HOME/.cargo/bin"
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "[INFO] Added Cargo to PATH for this session."
else
    echo "[WARNING] Rust/Cargo not found. If installation fails, you may need to install Rust."
    echo "          Visit https://rustup.rs/ to install Rust."
fi

# Upgrade pip first
echo ""
echo "[1/4] Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip --quiet || {
    echo "WARNING: pip upgrade failed, continuing anyway..."
}

# Install NumPy with pre-compiled wheel
echo ""
echo "[2/4] Installing NumPy..."
$PYTHON_CMD -m pip install numpy --prefer-binary --upgrade || {
    echo "ERROR: NumPy installation failed"
    echo "Please try installing system dependencies:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-dev python3-pip build-essential"
    echo "  macOS: xcode-select --install"
    exit 1
}

# Install other dependencies
echo ""
echo "[3/4] Installing other dependencies..."
if [ -f "setup/requirements.txt" ]; then
    REQ_FILE="setup/requirements.txt"
elif [ -f "requirements.txt" ]; then
    REQ_FILE="requirements.txt"
else
    echo "ERROR: requirements.txt not found"
    echo "Please run this script from the Insightron root directory"
    exit 1
fi

$PYTHON_CMD -m pip install -r "$REQ_FILE" --prefer-binary --no-cache-dir || {
    echo ""
    echo "[WARNING] Standard installation failed."
    echo "          This is often due to missing pre-built wheels for your Python version."
    echo ""
    echo "          Attempting to install 'tokenizers' explicitly..."
    $PYTHON_CMD -m pip install tokenizers --prefer-binary || {
        echo ""
        echo "[ERROR] 'tokenizers' installation failed."
        echo "        This usually means you need to install Rust to build it from source."
        echo ""
        echo "        Please install Rust from: https://rustup.rs/"
        echo "        Then run this installer again."
        echo ""
        exit 1
    }
    
    echo ""
    echo "[INFO] Retrying full installation..."
    $PYTHON_CMD -m pip install -r "$REQ_FILE" --prefer-binary --no-cache-dir || {
        echo ""
        echo "[WARNING] Some dependencies failed, trying minimal installation..."
        if [ -f "setup/requirements-minimal.txt" ]; then
            MIN_REQ_FILE="setup/requirements-minimal.txt"
        elif [ -f "requirements-minimal.txt" ]; then
            MIN_REQ_FILE="requirements-minimal.txt"
        else
            echo "ERROR: requirements-minimal.txt not found"
            exit 1
        fi
        
        $PYTHON_CMD -m pip install -r "$MIN_REQ_FILE" --prefer-binary --no-cache-dir || {
            echo "ERROR: Installation failed completely"
            echo "Please run: $PYTHON_CMD scripts/troubleshoot.py"
            exit 1
        }
    }
}

# Verify installation
echo ""
echo "[4/4] Verifying installation..."
$PYTHON_CMD -c "import faster_whisper, librosa, numpy, customtkinter, sounddevice; print('All core dependencies working!')" || {
    echo ""
    echo "[WARNING] Verification failed!"
    echo "          This might be due to a missing dependency or an incompatibility."
    echo ""
    echo "          Common fixes:"
    echo "           1. Install system build tools:"
    echo "              Ubuntu/Debian: sudo apt-get install python3-dev build-essential"
    echo "              macOS: xcode-select --install"
    echo "           2. Install Rust (for tokenizers): https://rustup.rs/"
    echo "           3. Ensure you are using Python 3.10 - 3.12"
    echo ""
    echo "          Run: $PYTHON_CMD scripts/troubleshoot.py for detailed diagnostics."
}

echo ""
echo "================================================"
echo "    Installation Complete!"
echo "================================================"
echo ""
echo "You can now run Insightron:"
echo "  $PYTHON_CMD insightron.py    # GUI mode (recommended)"
echo "  $PYTHON_CMD cli.py audio.mp3  # Command line mode"
echo ""
echo "For help: $PYTHON_CMD scripts/troubleshoot.py"
echo "Documentation: README.md"
echo ""

