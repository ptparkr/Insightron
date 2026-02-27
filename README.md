# 🎤 Insightron - AI Audio Transcriber

**Transform audio into beautifully structured insights with lightning-fast precision.**

## 🚀 Quick Start

### Run the Application

```bash
# Recommended (after install): GUI
insightron
python -m insightron.app.main

# Or (legacy)
python run_insightron.py

# Or use the app module
python insightron/app/main.py
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
python install.py

# Or platform-specific installers
automation/setup/install_windows.bat    # Windows
./automation/setup/install_unix.sh      # Linux/macOS
```

> **Note:** Some versions of the underlying `ctranslate2` / `faster-whisper`
> stack may emit a `pkg_resources is deprecated as an API` warning when used
> with very new `setuptools` versions. Insightron pins `setuptools` in its
> requirements and the test suite filters out this third‑party warning. It is
> safe to ignore and does not affect functionality.

## 📚 Documentation

All documentation is in the `docs/` folder:

- **[README.md](docs/README.md)** - Full documentation and features
- **[LLM_USAGE.md](docs/LLM_USAGE.md)** - Guide for LLM integration & setup
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history (see v3.1.0!)
- **[QUICK_START.md](docs/QUICK_START.md)** - Quick start for developers
- **[STRUCTURE.md](docs/STRUCTURE.md)** - Codebase structure guide
- **[ROOT_DIRECTORY.md](docs/ROOT_DIRECTORY.md)** - Root directory organization
- **[RESTRUCTURE_SUMMARY.md](docs/RESTRUCTURE_SUMMARY.md)** - Recent restructuring details

## 📁 Project Structure

```
Insightron/
├── insightron/           # Main source code
│   ├── app/              # Application entry points
│   ├── core/             # Core functionality
│   ├── services/         # Business logic
│   │   └── transcription/ # Multi-pass pipeline
│   └── ui/               # UI components
├── docs/                 # Documentation
├── tests/                # Test suite
├── automation/           # Setup & utility scripts
└── config.yaml           # Configuration file
```

## ✨ Features

### 🎯 NEW in v3.1.0: Multi-Pass Transcription
- 🤖 **AI-Powered Accuracy**: 3-pass pipeline delivers large-model quality at small-model speed
- 📝 **Smart Punctuation**: LLM restores proper punctuation and fixes phonetic errors
- 💭 **Emotion Detection**: Automatic markers like [Cheerful], [Urgent], [Calm]
- 🧠 **Local or Cloud LLMs**: Choose Qwen2.5-3B (local) or OpenAI GPT (API)

### Core Features
- ⚡ **Adaptive & Fast**: Up to 6x faster with Distil-Whisper & Dynamic Chunking
- 🎨 **Responsive GUI**: Professional dark-themed interface that scales perfectly
- 🧠 **Efficiency Layer**: Optimized for low-spec hardware & massive files
- 📦 **Batch Processing**: Process multiple files efficiently with resume capability
- 🔴 **Real-time**: Live audio transcription with VAD
- 🌍 **100+ Languages**: Multi-language support
- 💾 **Obsidian Integration**: Direct save to your vault

## 🛠️ Configuration

Edit `config.yaml` to configure:
- Transcription folder paths
- Model settings (including multi-pass!)
- Language preferences
- Multi-pass LLM provider and emotion thresholds

## 📖 For Developers

See [docs/QUICK_START.md](docs/QUICK_START.md) for development guide.

## 📝 License

See LICENSE file for details.

---

**Happy Transcribing! 🎤✨**
