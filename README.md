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

- **[STRUCTURE.md](docs/STRUCTURE.md)** - Architecture diagrams and codebase structure with detailed mermaid charts
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture guide with design patterns
- **[QUICK_START.md](docs/QUICK_START.md)** - Quick start guide
- **[BATCH_PROCESSING.md](docs/BATCH_PROCESSING.md)** - Batch processing documentation
- **[LLM_USAGE.md](docs/LLM_USAGE.md)** - LLM integration guide
- **[PERFORMANCE_UPGRADE.md](docs/PERFORMANCE_UPGRADE.md)** - Performance optimizations
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history (see v4.1.0!)
- **[README.md](docs/README.md)** - Full documentation index

## 📁 Project Structure

```
Insightron/
├── insightron/           # Main source code
│   ├── app/              # Application entry points (GUI, CLI, Web)
│   ├── core/             # Core functionality (config, model, resources, bus)
│   ├── services/         # Business logic
│   │   ├── transcription/ # Transcription pipeline
│   │   ├── batch/         # Batch processing
│   │   └── realtime/      # Real-time transcription
│   └── ui/               # UI components
├── docs/                 # Documentation
│   ├── STRUCTURE.md      # Architecture diagrams (mermaid)
│   ├── ARCHITECTURE.md   # Detailed architecture
│   ├── QUICK_START.md    # Quick start guide
│   └── ...
├── automation/           # Setup scripts
└── config.toml           # Configuration file (TOML)
```

## ✨ Features

### NEW in v4.1.0: Minimal Architecture
- ⚡ **O(1) Config Lookup**: TOML-based config with caching
- 🚀 **O(log n) Audio Chunking**: Binary search indexed access
- 🎨 **O(n) Text Formatting**: Single-pass processing with pre-compiled regex
- 🧠 **Resource Pool**: Priority allocation for ML workloads
- 📡 **Message Bus**: Event-driven inter-component communication
- 🔄 **Async Startup**: Non-blocking initialization
- 📊 **Architecture Diagrams**: Detailed mermaid diagrams in `docs/STRUCTURE.md`

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
```

Architecture documentation: See [docs/STRUCTURE.md](docs/STRUCTURE.md) for detailed mermaid diagrams.

## 📝 License

See LICENSE file for details.

---

**Happy Transcribing! 🎤✨**
