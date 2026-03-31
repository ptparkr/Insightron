# 🎤 Insightron v4.1.0 - AI Audio Transcriber

**Transform audio into beautifully structured insights with lightning-fast precision.**

## 🚀 Quick Start

### Run the Application

```bash
# GUI mode (default)
python -m insightron.app.main

# Web UI mode
python -m insightron.app.main --web

# Batch processing
python -m insightron.app.main batch -i /path/to/audio

# System check
python -m insightron.app.main --check
```

### Installation

```bash
# Create venv (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install (editable)
python -m pip install -U pip
pip install -e .

# Optional: Multi-pass LLM dependencies
pip install -e ".[llm]"

# Alternative: use the bundled installer
python automation/setup/install.py
```

> **Note:** Some versions of the underlying `ctranslate2` / `faster-whisper`
> stack may emit a `pkg_resources is deprecated as an API` warning when used
> with very new `setuptools` versions. Insightron pins `setuptools` in its
> requirements and the test suite filters out this third‑party warning. It is
> safe to ignore and does not affect functionality.

## 📚 Documentation

All documentation is in the `docs/` folder:

- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history (see v4.1.0!)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture guide

## 📁 Project Structure

```
Insightron/
├── insightron/           # Main source code
│   ├── app/              # Application entry points
│   ├── core/             # Core functionality (config, model, resources, bus)
│   ├── services/         # Business logic
│   │   ├── audio/         # Optimized audio processing
│   │   ├── pipeline/     # Unified transcription pipeline
│   │   └── batch/        # Batch processing
│   └── ui/               # UI components
├── docs/                 # Documentation
├── tests/                # Test suite
├── automation/           # Setup scripts
└── config.toml           # Configuration file (TOML)
```

## ✨ Features

### 🎯 NEW in v4.1.0: Minimal Architecture
- ⚡ **O(1) Config Lookup**: TOML-based config with caching
- 🚀 **O(log n) Audio Chunking**: Binary search indexed access
- 🎨 **O(n) Text Formatting**: Single-pass processing with pre-compiled regex
- 🧠 **Resource Pool**: Priority allocation for ML workloads
- 📡 **Message Bus**: Event-driven inter-component communication
- 🔄 **Async Startup**: Non-blocking initialization

### Core Features
- ⚡ **Adaptive & Fast**: Up to 6x faster with Distil-Whisper & Dynamic Chunking
- 🎨 **Responsive GUI**: Professional dark-themed interface
- 📦 **Batch Processing**: Process multiple files with retry + circuit breaker
- 🔴 **Real-time**: Live audio transcription with VAD
- 🌍 **100+ Languages**: Multi-language support

## 🛠️ Configuration

Edit `config.toml` to configure:
- Transcription folder paths
- Model settings
- Language preferences
- Audio preprocessing options

## 📖 For Developers

```bash
# System check
python -m insightron.app.main --check

# Run tests
pytest tests/
```

## 📝 License

See LICENSE file for details.

---

**Happy Transcribing! 🎤✨**
