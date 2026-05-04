#!/usr/bin/env python3
"""
Enhanced Setup Script for Insightron v4.1.1
Optimized installation process with better error handling, progress tracking,
and faster dependency management for the Whisper AI transcription project.
"""

import subprocess
import sys
import os
import time
import logging
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_rust_installed():
    """Check if Rust/Cargo is installed and add to PATH if found in default location."""
    if shutil.which("cargo"):
        return True
    
    # Check default Windows location
    cargo_home = Path.home() / ".cargo" / "bin"
    if cargo_home.exists() and (cargo_home / "cargo.exe").exists():
        logger.info(f"Found Cargo at {cargo_home}, adding to PATH")
        os.environ["PATH"] += os.pathsep + str(cargo_home)
        return True
    
    return False

def run_command(command: str, description: str, timeout: int = 600) -> Tuple[bool, str]:
    """
    Run a command with enhanced error handling and timeout support.
    """
    logger.info(f"Executing: {description}")
    print(f"Running: {description}...")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Command completed in {elapsed:.1f}s")
        print(f"SUCCESS: {description} completed successfully ({elapsed:.1f}s)")
        return True, result.stdout
        
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout}s"
        logger.error(error_msg)
        print(f"TIMEOUT: {description} timed out after {timeout}s")
        return False, error_msg
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed with return code {e.returncode}: {e.stderr}"
        logger.error(error_msg)
        print(f"ERROR: {description} failed:")
        print(f"Error: {e.stderr}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {description} failed with unexpected error: {e}")
        return False, error_msg

def check_python_version() -> bool:
    """Check if Python version is compatible with Insightron."""
    version = sys.version_info
    min_version = (3, 10)
    max_minor = 12  # Python 3.13+ not yet fully supported
    
    if version[:2] < min_version:
        logger.error(f"Python {min_version[0]}.{min_version[1]}+ required, got {version.major}.{version.minor}")
        print(f"Python {min_version[0]}.{min_version[1]} or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    if version.minor >= 13:
        logger.warning(f"Python 3.{version.minor} detected - many packages don't support Python 3.13+ yet")
        print(f"⚠️  WARNING: Python 3.{version.minor} detected")
        print("   Many scientific packages (like onnxruntime) do not yet support Python 3.13+.")
        print("   We STRONGLY recommend using Python 3.10, 3.11, or 3.12.")
        response = input("   Do you want to continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    logger.info(f"Python version check passed: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies() -> bool:
    """Install required dependencies with optimized installation strategy."""
    logger.info("Starting dependency installation process")
    print("\n📦 Installing dependencies...")
    
    # Get script directory for proper path resolution
    script_dir = Path(__file__).parent.parent.parent
    original_dir = os.getcwd()
    try:
        os.chdir(script_dir)
    except Exception as e:
        logger.warning(f"Could not change to script directory: {e}")
        script_dir = Path(original_dir)
    
    # Check for Rust
    rust_available = check_rust_installed()
    if not rust_available:
        print("⚠️  Rust/Cargo not found. Installation of some packages may fail.")

    # Upgrade pip first with timeout
    success, _ = run_command(
        f"{sys.executable} -m pip install --upgrade pip", 
        "Upgrading pip",
        timeout=120
    )
    if not success:
        logger.warning("pip upgrade failed, continuing with installation")
        print("Warning: pip upgrade failed, continuing anyway...")
    
    # Try installing from requirements.txt first
    logger.info("Attempting installation from requirements.txt")
    requirements_path = script_dir / "automation" / "setup" / "requirements.txt"
    if not requirements_path.exists():
        requirements_path = script_dir / "requirements.txt"
        if not requirements_path.exists():
            print(f"❌ ERROR: requirements.txt not found")
            print(f"   Searched in: {script_dir}")
            print("   Please run this script from the Insightron root directory")
            return False

    success, output = run_command(
        f"{sys.executable} -m pip install -r {requirements_path} --prefer-binary --no-cache-dir", 
        "Installing from requirements.txt",
        timeout=900
    )
    
    if success:
        logger.info("Successfully installed from requirements.txt")
        print("Successfully installed from requirements.txt")
        return True
    
    logger.warning("requirements.txt installation failed, trying minimal installation")
    print("requirements.txt failed, trying minimal installation...")
    
    # Fallback to minimal requirements
    minimal_req_path = script_dir / "automation" / "setup" / "requirements-minimal.txt"
    if not minimal_req_path.exists():
        minimal_req_path = script_dir / "requirements-minimal.txt"
        if not minimal_req_path.exists():
            print(f"❌ ERROR: requirements-minimal.txt not found")
            return False

    success, output = run_command(
        f"{sys.executable} -m pip install -r {minimal_req_path} --prefer-binary --no-cache-dir", 
        "Installing minimal requirements",
        timeout=300
    )
    
    if success:
        logger.info("Successfully installed minimal requirements")
        print("Successfully installed minimal requirements")
        return True
    
    logger.error("Both installation methods failed")
    print("Both installation methods failed")
    print("Try running: python scripts/troubleshoot.py")
    return False

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    try:
        # Try to import config to get path, otherwise use default
        try:
            sys.path.append(os.getcwd())
            from insightron.core.config import TRANSCRIPTION_FOLDER
            TRANSCRIPTION_FOLDER.mkdir(parents=True, exist_ok=True)
            print(f"Created transcription folder: {TRANSCRIPTION_FOLDER}")
        except ImportError:
             print("Could not load config, skipping specific folder creation.")
        return True
    except Exception as e:
        print(f"Failed to create directories: {e}")
        return False

def test_installation():
    """Test if the installation works"""
    print("\nTesting installation...")
    
    try:
        # Test imports
        import faster_whisper
        import librosa
        print("All core modules imported successfully")
        
        # Test basic functionality
        sys.path.append(os.getcwd())
        try:
            from insightron.services.transcription.transcribe import AudioTranscriber
            print("Transcription module loaded successfully")
        except ImportError:
             print("Could not load AudioTranscriber, but dependencies seem ok.")
        
        return True
    except ImportError as e:
        print(f"Import test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("Insightron v4.1.1 Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\nSetup failed during dependency installation")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\nSetup failed during directory creation")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("\nSetup failed during testing")
        sys.exit(1)
    
    print("\nSetup completed successfully!")
    print("\nYou can now run the application:")
    print("   python insightron.py    # GUI mode")
    print("   python cli.py audio.mp3 # CLI mode")
    print("\nSee README.md for detailed usage instructions")

if __name__ == "__main__":
    main()
