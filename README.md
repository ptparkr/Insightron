# 🎤 Insightron - AI Audio Transcriber

**Transform audio into beautifully structured insights with lightning-fast precision.**

## 🚀 Quick Start

### Run the Application

```bash
# Main entry point (recommended)
python src/app/main.py

# Or use legacy entry point
python insightron.py
```

### Installation

```bash
# Run the installer
python setup/install.py

# Or platform-specific
setup/install_windows.bat    # Windows
setup/install_unix.sh        # Linux/macOS
```

## 📚 Documentation

All documentation is in the `docs/` folder:

- **[STRUCTURE.md](docs/STRUCTURE.md)** - Codebase structure guide
- **[QUICK_START.md](docs/QUICK_START.md)** - Quick start for developers
- **[ROOT_DIRECTORY.md](docs/ROOT_DIRECTORY.md)** - Root directory organization
- **[README.md](docs/README.md)** - Full documentation and features
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history
- **[RESTRUCTURE_SUMMARY.md](docs/RESTRUCTURE_SUMMARY.md)** - Recent restructuring details

## 📁 Project Structure

```
Insightron/
├── src/                   # Main source code
│   ├── app/              # Application entry points
│   ├── core/             # Core functionality
│   ├── services/         # Business logic
│   └── ui/               # UI components
├── docs/                 # Documentation
├── benchmarks/          # Benchmarking tools
├── tests/                # Test suite
├── setup/                # Installation scripts
└── scripts/              # Utility scripts
```

## ✨ Features

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
- Model settings
- Language preferences

## 📖 For Developers

See [docs/QUICK_START.md](docs/QUICK_START.md) for development guide.

## 📝 License

See LICENSE file for details.

---

**Happy Transcribing! 🎤✨**
