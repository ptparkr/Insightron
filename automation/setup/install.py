#!/usr/bin/env python3
"""
Insightron v2.2.0 - Universal Cross-Platform Installer
Enhanced dependency installer that works on Windows, macOS, and Linux
with intelligent error handling and compatibility checks.
"""

import subprocess
import sys
import os
import shutil
import platform
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent.parent.parent.absolute()

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    min_version = (3, 10)
    
    if version[:2] < min_version:
        print(f"❌ ERROR: Python {min_version[0]}.{min_version[1]}+ required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print("   Please install Python 3.10, 3.11, or 3.12 from https://python.org")
        return False
    
    if version.minor >= 13:
        print(f"\n⚠️  WARNING: Python 3.{version.minor} detected")
        print("   Many scientific packages (like onnxruntime) do not yet support Python 3.13+.")
        print("   We STRONGLY recommend using Python 3.10, 3.11, or 3.12.")
        print("   The installation is likely to fail.\n")
        response = input("   Do you want to continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    print(f"✅ Python version check passed: {version.major}.{version.minor}.{version.micro}")
    return True

def check_rust_installed():
    """Check if Rust/Cargo is installed and add to PATH if found."""
    if shutil.which("cargo"):
        print("✅ Rust/Cargo found in PATH")
        return True
    
    # Check default locations
    cargo_paths = [
        Path.home() / ".cargo" / "bin" / "cargo.exe",  # Windows
        Path.home() / ".cargo" / "bin" / "cargo",       # Unix
    ]
    
    for cargo_path in cargo_paths:
        if cargo_path.exists():
            cargo_bin = cargo_path.parent
            print(f"⚠️  Found Cargo at {cargo_bin}, but it's not in PATH.")
            print("   Adding it to PATH for this session...")
            os.environ["PATH"] = str(cargo_bin) + os.pathsep + os.environ.get("PATH", "")
            return True
    
    print("⚠️  Rust/Cargo not found. Some packages (like tokenizers) may fail to install")
    print("   if pre-built wheels are not available for your Python version.")
    print("   If installation fails, please install Rust from https://rustup.rs/")
    return False

def run_command(command, description, exit_on_fail=False, timeout=600):
    """Run a command and handle errors gracefully."""
    print(f"🔄 {description}...")
    try:
        # On Windows, ensure proper encoding for subprocess output
        env = os.environ.copy()
        if sys.platform == "win32":
            env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ {description} timed out after {timeout}s")
        if exit_on_fail:
            sys.exit(1)
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        if e.stderr:
            # Decode error output properly
            error_msg = e.stderr[:500] if len(e.stderr) > 500 else e.stderr
            print(f"   Error: {error_msg}")
        if e.stdout:
            # Sometimes useful info is in stdout
            stdout_msg = e.stdout[:200] if len(e.stdout) > 200 else e.stdout
            if stdout_msg.strip():
                print(f"   Output: {stdout_msg}")
        if exit_on_fail:
            sys.exit(1)
        return False
    except Exception as e:
        print(f"❌ {description} failed with unexpected error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        if exit_on_fail:
            sys.exit(1)
        return False

def find_requirements_file(script_dir, filename):
    """Find requirements file in common locations."""
    possible_paths = [
        script_dir / "automation" / "setup" / filename,
        script_dir / filename,
        Path.cwd() / "automation" / "setup" / filename,
        Path.cwd() / filename,
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def install_dependencies():
    """Main installation process."""
    script_dir = get_script_dir()
    original_dir = Path.cwd()
    
    # Change to script directory for consistent path resolution
    try:
        os.chdir(script_dir)
    except Exception as e:
        print(f"⚠️  Could not change to script directory: {e}")
        print("   Continuing with current directory...")
    
    print("\n🎤 Insightron v2.2.0 - Universal Cross-Platform Installer")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.executable}")
    print(f"Working directory: {script_dir}")
    print()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check for Rust
    rust_available = check_rust_installed()
    
    # Upgrade pip first
    print("\n📦 Step 1/4: Upgrading pip...")
    run_command(
        f"{sys.executable} -m pip install --upgrade pip --quiet",
        "Upgrading pip",
        exit_on_fail=False
    )
    
    # Install NumPy first (dependency for many packages)
    print("\n📦 Step 2/4: Installing NumPy...")
    numpy_commands = [
        f"{sys.executable} -m pip install numpy --prefer-binary --upgrade --quiet",
        f"{sys.executable} -m pip install numpy --only-binary=all --quiet",
    ]
    
    numpy_installed = False
    for cmd in numpy_commands:
        if run_command(cmd, "Installing NumPy", exit_on_fail=False):
            numpy_installed = True
            break
    
    if not numpy_installed:
        print("❌ Failed to install NumPy.")
        print("\n💡 System-specific fixes:")
        if platform.system() == "Windows":
            print("   Install Visual Studio Build Tools:")
            print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        elif platform.system() == "Linux":
            print("   Ubuntu/Debian: sudo apt-get install python3-dev build-essential")
            print("   Fedora: sudo dnf install python3-devel gcc")
        elif platform.system() == "Darwin":
            print("   macOS: xcode-select --install")
        return False
    
    # Install other dependencies
    print("\n📦 Step 3/4: Installing dependencies...")
    requirements_path = find_requirements_file(script_dir, "requirements.txt")
    
    if not requirements_path:
        print("❌ ERROR: requirements.txt not found")
        print(f"   Searched in: {script_dir}")
        print("   Please run this script from the Insightron root directory")
        return False
    
    print(f"   Using: {requirements_path}")
    
    # Quote path for Windows compatibility (handles spaces in paths)
    requirements_path_str = f'"{requirements_path}"' if platform.system() == "Windows" else str(requirements_path)
    
    success = run_command(
        f"{sys.executable} -m pip install -r {requirements_path_str} --prefer-binary --no-cache-dir",
        "Installing requirements",
        exit_on_fail=False,
        timeout=900
    )
    
    if not success:
        print("\n🔍 Attempting to fix common issues...")
        
        # Try installing tokenizers separately
        if not run_command(
            f"{sys.executable} -m pip install tokenizers --prefer-binary",
            "Installing tokenizers separately",
            exit_on_fail=False
        ):
            if not rust_available:
                print("❌ Failed to install 'tokenizers'.")
                print("💡 It looks like you need to install Rust to build 'tokenizers' from source.")
                print("   Please install Rust from: https://rustup.rs/")
                return False
        
        # Retry full installation
        print("\n🔄 Retrying full installation...")
        success = run_command(
            f"{sys.executable} -m pip install -r {requirements_path_str} --prefer-binary --no-cache-dir",
            "Retrying requirements installation",
            exit_on_fail=False,
            timeout=900
        )
        
        if not success:
            # Try minimal requirements
            print("\n⚠️  Trying minimal requirements...")
            minimal_req_path = find_requirements_file(script_dir, "requirements-minimal.txt")
            
            if not minimal_req_path:
                print("❌ ERROR: requirements-minimal.txt not found")
                return False
            
            # Quote path for Windows compatibility
            minimal_req_path_str = f'"{minimal_req_path}"' if platform.system() == "Windows" else str(minimal_req_path)
            
            success = run_command(
                f"{sys.executable} -m pip install -r {minimal_req_path_str} --prefer-binary --no-cache-dir",
                "Installing minimal requirements",
                exit_on_fail=False,
                timeout=300
            )
            
            if not success:
                print("❌ Installation failed completely")
                return False
    
    # Verify installation
    print("\n🔍 Step 4/4: Verifying installation...")
    try:
        import numpy
        import faster_whisper
        import librosa
        import soundfile
        import pydub
        import customtkinter
        import sounddevice
        print("✅ All core dependencies are working!")
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        sys.path.insert(0, str(script_dir))
        try:
            from insightron.services.transcription.transcribe import AudioTranscriber
            print("✅ Transcription module loaded successfully!")
        except ImportError:
            print("⚠️  Could not load AudioTranscriber (might be path issue), but dependencies look ok.")
        
        return True
    except ImportError as e:
        print(f"❌ Verification failed: {e}")
        print("💡 Try running: python scripts/troubleshoot.py")
        return False
    finally:
        # Restore original directory
        try:
            os.chdir(original_dir)
        except Exception:
            pass

def main():
    """Main entry point."""
    success = install_dependencies()
    
    if success:
        print("\n🎉 Installation completed successfully!")
        print("\nYou can now run Insightron:")
        print("   • python insightron.py    # GUI mode (recommended)")
        print("   • python cli.py audio.mp3  # Command line mode")
        print("   • python scripts/troubleshoot.py  # For diagnostics")
    else:
        print("\n💥 Installation failed. Please check the errors above.")
        print("   Try running: python scripts/troubleshoot.py")
        sys.exit(1)

if __name__ == "__main__":
    main()

