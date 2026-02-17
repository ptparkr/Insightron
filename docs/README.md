# 🎤 Insightron v3.1.0 - Experience the Future of AI Transcription

**Transform audio into beautifully structured insights with lightning-fast precision.**

Insightron is a next-generation transcription application powered by **faster-whisper** (CTranslate2), featuring a stunning dark-themed GUI, batch processing capabilities, and seamless Obsidian integration. Experience up to **6x faster transcription** with **Distil-Whisper** models, instant model reuse, and optimized realtime performance.

## ✨ Key Features

### 🤖 **NEW in v3.1.0: Multi-Pass Transcription**
- **3-Pass Intelligence**: Revolutionary pipeline that delivers large-model accuracy at small-model speed
  - **Pass 1 (Detection)**: Lightning-fast base model for raw text and precise timestamps
  - **Pass 2 (Contextual Restoration)**: AI-powered LLM restores punctuation and fixes phonetic errors
  - **Pass 3 (Emotion Mapping)**: Sentiment analysis injects emotional context markers
- **Smart Batch Processing**: 30-second chunking with 2-second overlap for optimal memory and context
- **Flexible LLM Support**: 
  - **Local**: Qwen2.5-3B-Instruct (recommended), Phi-3-mini, Gemma-2B with 4-bit quantization
  - **Cloud**: OpenAI GPT-3.5/4, with support for Anthropic Claude and Google Gemini coming soon
- **Emotion Markers**: Automatic detection of [Cheerful], [Urgent], [Calm], [Excited], [Serious] tones
- **Granular Control**: 131 lines of config options for complete customization
- **Opt-In Design**: Multi-pass is disabled by default for complete backward compatibility
- **Detailed Guide**: See **[LLM_USAGE.md](LLM_USAGE.md)** for setup and configuration details

### 🚀 **Performance & Reliability**
- **⚡ faster-whisper Engine**: Up to **4x faster** transcription using CTranslate2 optimization
- **🔥 Distil-Whisper Support**: Up to **6x faster** inference with `distil-medium.en` and `distil-large-v2`
- **🔄 Instant Model Reuse**: Zero-delay start for subsequent transcriptions
- **🧠 Lower Memory Usage**: INT8 quantization for efficient CPU processing
- **🎯 GPU Acceleration**: Automatic CUDA detection for maximum speed
- **📊 Real-time Progress**: Segment-level progress updates for smooth UX
- **💾 Smart File Operations**: Atomic writes prevent data corruption
- **🔧 Cross-Platform**: Seamless Windows, macOS, and Linux support
- **🔴 Realtime Transcription**: Low-latency live audio capture with automatic Obsidian note saving
- 🛡️ **Robust Error Handling**: Intelligent retry mechanism with automatic parameter adjustment for difficult audio
- 🧠 **Adaptive VAD**: Dynamic voice activity detection that adapts to changing background noise levels
- ✨ **Adaptive Segment Merging**: Machine-learned gap thresholds that adapt to speaker cadence and natural pauses
- 📊 **Enhanced Quality Metrics**: Weighted confidence scoring with degradation detection and quality tiers
- 🔄 **Batch Resume & Recovery**: Resume failed batches from where they left off with state persistence
- 📈 **Event-Driven Progress**: Milestone-based progress tracking with segment-level events
- 💾 **Memory Monitoring**: Real-time memory tracking to prevent OOM conditions during batch processing
- ⚡ **Efficiency Layer**: Dedicated resource management for optimal CPU/RAM usage
- 🎯 **Dynamic Chunking**: Smart audio processing that adapts to hardware capabilities 

### 🧠 **Intelligent Efficiency**
- **Smart Resource Management**: Sliding window buffering for handling large files on any hardware
- **Advanced VAD**: Adaptive Voice Activity Detection with silence pruning
- **Quantization Support**: INT8/INT4 optimization for reduced memory footprint
- **Metric Tracking**: Real-time performance monitoring (Audio/Cycle)

### 🎨 **Modern Dark-Black Theme** ✨
- **Pure Black Background**: Material Dark theme perfect for OLED screens
- **Premium Color Palette**: 
  - 🔵 Bright Blue for Model selection
  - 🟣 Purple for Language selection
  - 🟢 Emerald for Formatting options
- **Tabbed Interface**: Dedicated tabs for Single File, Batch Mode, and Realtime
- **Settings Persistence**: Your preferences automatically saved
- **Compact Timestamped Logs**: Terminal-style output with `[HH:MM:SS]` timestamps
- **Smooth Hover Effects**: Premium animations throughout the UI

### 🎵 **Audio Excellence**
- **Universal Format Support**: MP3, WAV, M4A, FLAC, MP4, OGG, AAC, WMA
- **Smart Format Detection**: Automatic audio format recognition
- **Quality Optimization**: Model-specific parameters for best results
- **File Size Validation**: Automatic 500MB limit checking
- **Enhanced Audio Processing**: Improved librosa and soundfile integration

### 🌍 **Multi-Language Support**
- **100+ Languages**: Support for all Whisper-supported languages including English, Spanish, French, German, Chinese, Japanese, Arabic, Hindi, and many more
- **Auto-Detection**: Intelligent language detection for multilingual content
- **Manual Selection**: Choose specific languages for optimal accuracy
- **UTF-8 Encoding**: Perfect support for non-Latin scripts and special characters
- **Language-Aware Processing**: Optimized transcription parameters for each language

### 📝 **Intelligent Text Processing**
- **Smart Formatting**: Auto-detects paragraph breaks and sentence structure
- **Filler Word Removal**: Cleans up "um", "uh", and repetitive phrases
- **Transcription Fixes**: Corrects common Whisper AI errors
- **Multiple Styles**: Auto, paragraph, bullets, and minimal formatting options

### 🔗 **Obsidian Integration**
- **Seamless Workflow**: Direct save to your Obsidian vault
- **Rich Metadata**: Duration, file size, language, processing time
- **Timestamp Support**: Optional segment-by-segment timestamps
- **Tag System**: Automatic tagging for easy organization

## 🚀 Quick Start

### 1. **One-Click Installation**

```bash
# Download and setup Insightron
git clone https://github.com/ptparkr/Insightron.git
cd Insightron

# Universal installer (recommended - works on all platforms)
python install.py

# Platform-specific installers
# Platform-specific installers
automation/setup/install_windows.bat    # Windows
./automation/setup/install_unix.sh      # Linux/macOS (chmod +x install_unix.sh first)

# Alternative installers
python automation/setup/install_dependencies.py  # Cross-platform Python installer
python automation/setup/setup.py                  # Enhanced setup script

# Or manual installation
pip install -r automation/setup/requirements.txt
```

### 2. **Configuration**

Insightron uses a `config.yaml` file for easy configuration. The file is automatically created on first run if it doesn't exist.

Edit `config.yaml` to set your paths and preferences:

```yaml
runtime:
  # Where to save transcription files
  transcription_folder: "D:\\2. Areas\\IdeaVerse\\Areas\\Inner Library\\Notes"
  
  # Where to save audio recordings
  recordings_folder: "D:\\2. Areas\\IdeaVerse\\Areas\\Inner Library\\Recordings"

model:
  name: "small"
  device: "auto"
  compute_type: "int8"
```

### 3. **Launch Insightron**

**🎨 GUI Mode (Recommended):**
```bash
python insightron.py
```

**⚡ Command Line Mode:**
```bash
# Basic transcription with auto-detection
python cli.py audio.mp3

# Advanced options with language selection
python cli.py audio.wav -m large -v -f paragraphs -l es

# Multi-language examples
python cli.py spanish_audio.mp3 -l es -m medium
python cli.py french_audio.wav -l fr -f auto
python cli.py chinese_audio.m4a -l zh -m large
python cli.py arabic_audio.mp3 -l ar -v
```

## 📖 Usage Guide

### **🤖 Multi-Pass Transcription (v3.1.0)**

Enable the revolutionary 3-pass pipeline for large-model accuracy at small-model speed!

#### **Quick Setup**

1. **Open `config.yaml`** and set:
```yaml
multi_pass:
  enabled: true  # Enable multi-pass pipeline
```

2. **Choose Your LLM Provider:**

**Option A: Local (Privacy-First, No API Costs)**
```yaml
multi_pass:
  contextual_restoration:
    provider: "local"
    local_model:
      model_name: "Qwen/Qwen2.5-3B-Instruct"  # Recommended
      quantization: "4bit"  # 2GB memory
```

**Option B: Cloud API (Higher Quality)**
```yaml
multi_pass:
  contextual_restoration:
    provider: "openai"
    api_settings:
      model: "gpt-3.5-turbo"  # or gpt-4
```

Set API key as environment variable:
```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

3. **Transcribe Normally** - The 3-pass pipeline activates automatically!

#### **What You Get**

✅ **Professional Punctuation** - Proper commas, periods, capitalization  
✅ **Error Correction** - Fixes phonetic mistakes like "there/their/they're"  
✅ **Emotion Context** - Markers like [Cheerful], [Urgent], [Calm] for tone  
✅ **Smart Chunking** - 30-second batches with context preservation  

#### **Performance**
- **Local LLM**: ~1.8x slower than single-pass, ~2GB RAM
- **Cloud API**: 2-5x slower (network dependent), ~$0.002/minute (GPT-3.5)

#### **Customization**

```yaml
multi_pass:
  emotion_mapping:
    enabled: true
    enabled_emotions: [cheerful, urgent, calm, excited, serious]
    thresholds:
      high_energy_wps: 3.5  # Words per second for high energy
      low_energy_wps: 2.0   # Words per second for calm tone
```

**Disable specific passes:**
```yaml
multi_pass:
  enabled: true
  contextual_restoration:
    enabled: true  # Pass 2: ON
  emotion_mapping:
    enabled: false  # Pass 3: OFF (skip emotion detection)
```

### **GUI Interface**

#### **Single File Mode**
1. **Launch**: Run `python insightron.py`
2. **Select Tab**: Use "Single File" tab (default)
3. **Choose Audio**: Click "📁 Choose Audio File"
4. **Configure Settings**: Select Model (try `distil-medium.en` for speed!), Language, and Formatting
5. **Transcribe**: Click "⚡ Start Transcription"
6. **Monitor**: Watch real-time progress in the status bar and timestamped log
7. **Review**: Open output folder when complete

#### **Batch Mode** 📦
1. **Switch Tab**: Click "Batch Mode" tab
2. **Select Files**: 
   - Click "📄 Choose Files" to select multiple audio files
   - OR click "📂 Choose Folder" to process an entire folder
3. **Process**: Click "⚡ Process All Files"
4. **Monitor**: Track progress as each file is completed in the log
5. **Review**: Check summary statistics when finished

#### **Realtime Mode** 🔴
1. **Switch Tab**: Click "Realtime" tab
2. **Configure**: Select Model and Language
3. **Start**: Click "🔴 Start Recording"
4. **Speak**: Speak into your microphone
5. **Visualize**: See real-time audio levels and text generation
6. **Stop**: Click "⏹️ Stop Recording" to save audio and transcript

### **Command Line Interface**

```bash
# Basic usage
python cli.py audio.mp3

# With specific model
python cli.py audio.mp3 -m large

# Custom formatting
python cli.py audio.mp3 -f paragraphs

# Create bulleted lists from speech
python cli.py meeting_notes.wav -f bullets

# Batch processing (multiple files)
python cli.py audio1.mp3 audio2.mp3
python cli.py *.mp3 -b

# Batch with specific worker count
python cli.py *.wav -b -w 4

# Use process pool (better for CPU-bound tasks)
python cli.py *.mp3 -b --use-processes

# Custom output location
python cli.py audio.mp3 -o "D:\Output\transcript.md"
```

Insightron supports **100+ languages** including all major world languages:

#### **Major Languages**
- **English** (en) - Default, highest accuracy
- **Spanish** (es) - Español
- **French** (fr) - Français  
- **German** (de) - Deutsch
- **Chinese** (zh) - 中文 (Mandarin)
- **Japanese** (ja) - 日本語
- **Korean** (ko) - 한국어
- **Arabic** (ar) - العربية
- **Hindi** (hi) - हिन्दी
- **Russian** (ru) - Русский
- **Portuguese** (pt) - Português
- **Italian** (it) - Italiano

#### **Additional Languages**
- **European**: Dutch, Swedish, Norwegian, Danish, Finnish, Polish, Czech, Hungarian, Romanian, Bulgarian, Croatian, Slovak, Slovenian, Estonian, Latvian, Lithuanian, Greek, Welsh, Irish, Maltese, Albanian, Basque, Catalan, Galician
- **Asian**: Thai, Vietnamese, Burmese, Khmer, Lao, Mongolian, Tamil, Telugu, Malayalam, Kannada, Gujarati, Punjabi, Marathi, Nepali, Sinhala, Bengali
- **Middle Eastern/African**: Persian, Urdu, Hebrew, Amharic, Swahili, Zulu, Afrikaans
- **And many more...**

### **Language Usage Examples**

```bash
# Auto-detection (recommended for most cases)
python cli.py audio.mp3 -l auto

# Specific language selection for better accuracy
python cli.py spanish_meeting.mp3 -l es -m medium
python cli.py french_podcast.wav -l fr -m large
python cli.py chinese_lecture.m4a -l zh -v
python cli.py arabic_news.mp3 -l ar -f paragraphs
python cli.py hindi_interview.wav -l hi -m medium
```

### **Language Selection Tips**

- **Auto-detection**: Use `auto` or leave blank for most cases - Whisper is very good at detecting languages
- **Manual selection**: Specify language for better accuracy, especially with:
  - Background noise or poor audio quality
  - Mixed-language content where you want to prioritize one language
  - Less common languages where auto-detection might be uncertain
- **UTF-8 Support**: All non-Latin scripts (Chinese, Arabic, Hindi, etc.) are fully supported with proper UTF-8 encoding

## 🎯 Whisper Model Guide

### **Model Comparison**

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| **tiny** | ~39 MB | ⚡⚡⚡ | ⭐⭐ | Quick drafts, testing |
| **base** | ~74 MB | ⚡⚡ | ⭐⭐⭐ | Balanced performance |
| **small** | ~244 MB | ⚡ | ⭐⭐⭐⭐ | High quality, good speed |
| **medium** | ~769 MB | ⚡ | ⭐⭐⭐⭐⭐ | **Recommended** |
| **large-v2** | ~1550 MB | ⚡ | ⭐⭐⭐⭐⭐ | Maximum accuracy |
| **distil-medium.en** | ~394 MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | **Best Speed/Accuracy** (English only) |
| **distil-large-v2** | ~756 MB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | High accuracy, faster than large |

### **Performance Tips**

- **RAM**: 4GB+ recommended for medium model, 8GB+ for large
- **Storage**: ~2GB for all models combined
- **CPU**: Multi-core processor recommended
- **GPU**: CUDA support available for 3-5x speedup

## 📊 Output Format

Transcripts are saved as beautifully formatted Markdown files with rich metadata:

```markdown
---
title: my_audio_file
date: 2024-01-15 14:30:25
duration: 5:23
duration_seconds: 323.4
file_size: 12.5 MB
model: medium
language: en
formatting: auto
tags: [transcription, audio-note, whisper]
created: 2024-01-15 14:30:25
---

# 🎤 Transcription: my_audio_file

## 📊 Metadata
- **Duration:** 5:23 (323.4 seconds)
- **File Size:** 12.5 MB
- **Model:** medium
- **Language:** en
- **Formatting:** Auto
- **Transcribed:** 2024-01-15 14:30:25

## 📝 Transcript

Your beautifully formatted transcript here with intelligent paragraph breaks...

## 🕐 Timestamps

**00:00 - 00:15:** First segment of speech
**00:15 - 00:30:** Second segment of speech
...

---
*Transcribed using Insightron*  
*Generated on 2024-01-15 14:30:25*
```

## 🛠️ Troubleshooting

### **Common Issues & Solutions**

#### **Installation Problems**
```bash
# Enhanced troubleshooting
python scripts/troubleshoot.py

# Cross-platform installer
python install_dependencies.py

# Windows-specific installer
install_windows.bat

# Manual dependency installation
pip install --upgrade pip
pip install -r requirements-minimal.txt
```

#### **Audio File Issues**
- **File too large**: Whisper has a 500MB limit (increased from 25MB) - use audio compression for larger files
- **Unsupported format**: Insightron supports MP3, WAV, M4A, FLAC, MP4, OGG, AAC, WMA
- **Corrupted file**: Try a different audio file or run diagnostics

#### **Performance Issues**
- **Slow transcription**: Use `distil-medium.en` or smaller models (tiny, base, small)
- **Memory errors**: Close other applications, use tiny model
- **GPU not detected**: Install CUDA toolkit for GPU acceleration

#### **Obsidian Integration**
- **Path not found**: Update `transcription_folder` in `config.yaml`
- **Permission denied**: Run as administrator or check folder permissions
- **Files not appearing**: Refresh Obsidian or check the correct folder

### **System Requirements**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.10+ | 3.11+ |
```python
def create_markdown(filename, text, date, duration, model, ...):
    # Your custom template here
    return custom_template
```

### **GUI Themes**
Update `gui.py` to modify colors and styling:

```python
self.colors = {
    'accent': '#your_color',      # Primary accent color
    'bg_primary': '#your_bg',     # Background color
    'text_primary': '#your_text', # Text color
    # ... more colors
}
```

## 📈 Performance Optimization

### **Speed Improvements**
- Use `distil-medium.en` for lightning-fast English transcription
- Use `tiny` or `base` models for faster multi-language transcription
- Enable GPU acceleration with CUDA
- Close unnecessary applications during transcription
- Use SSD storage for better I/O performance

### **Memory Optimization**
- Process shorter audio files
- Use smaller models for large files
- Enable memory-efficient processing in config

### **Quality Improvements**
- Use `medium` or `large` models for better accuracy
- Ensure good audio quality (clear speech, minimal background noise)
- Use appropriate formatting style for your content type

## ⏱️ Benchmarking

Insightron includes a built-in benchmarking tool to test performance on your system.

```bash
# Run standard benchmark
python benchmark_insightron.py

# The benchmark will:
# 1. Generate a test audio file
# 2. Run single-file transcription
# 3. Run batch transcription
# 4. Test realtime simulation
# 5. Save results to benchmark_results.json
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test thoroughly
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### **Development Setup**
```bash
# Clone your fork
git clone https://github.com/ptparkr/Insightron.git
cd Insightron

# Install development dependencies
pip install -r automation/setup/requirements.txt
pip install pytest black flake8

# Run enhanced diagnostics
python troubleshoot.py

# Run tests
python -m pytest

# Format code
black *.py
```

> **Note on warnings:** When running tests you may see a warning from the
> `ctranslate2` / `faster-whisper` stack about
> `pkg_resources is deprecated as an API` on very new `setuptools`
> versions. The project pins `setuptools` in `automation/setup/requirements.txt`
> and `pytest.ini` filters out this third‑party warning; it does not affect
> Insightron’s behavior.

## 🙏 Acknowledgments

- **OpenAI** for the incredible Whisper AI model
- **The open-source community** for audio processing libraries
- **Obsidian** for the excellent note-taking platform
- **Contributors** who help improve Insightron

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ptparkr/Insightron/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ptparkr/Insightron/discussions)
- **Documentation**: [Wiki](https://github.com/ptparkr/Insightron/wiki)

---

**Happy Transcribing! 🎤✨**

*Transform audio into structured wisdom — locally, beautifully, intelligently.*

**Insightron v3.1.0** - Multi-Pass Intelligence

## 🆕 What's New in v3.1.0

### **🤖 Multi-Pass Transcription Revolution**
- ✅ **3-Pass Pipeline**: Achieve large-model accuracy at small-model speed with innovative multi-pass processing
  - **Pass 1 (Detection)**: Fast base model transcription
  - **Pass 2 (Contextual Restoration)**: AI-powered punctuation and error correction
  - **Pass 3 (Emotion Mapping)**: Sentiment analysis with emotional markers
- ✅ **Flexible LLM Integration**: Support for both local (Qwen2.5-3B, Phi-3, Gemma) and cloud (OpenAI GPT) models
- ✅ **Smart Batch Processing**: 30-second chunking with 2-second overlap for memory efficiency
- ✅ **Emotion Detection**: Automatic markers - [Cheerful], [Urgent], [Calm], [Excited], [Serious]
- ✅ **Granular Control**: 131 lines of config options for complete customization
- ✅ **Backward Compatible**: Opt-in design keeps single-pass as default

### **Previous Updates (v3.0.0)**

### **🚀 Core Evolution**
- ✅ **New Efficiency Layer**: Dedicated optimization layer managing CPU/RAM usage dynamically for consistent performance.
- ✅ **Advanced VAD System**: Interactive Voice Activity Detection with adaptive parameters and improved silence pruning.
- ✅ **Dynamic Resource Management**: Smart sliding window buffering and dynamic chunking to handle massive audio files on low-spec systems.
- ✅ **Responsive UI 2.0**: Brand new responsive design system ensuring perfect scaling across all displays.
- ✅ **Modular Architecture**: Complete codebase refactor for superior stability and maintainability.

### **Previous Updates (v2.2.0)**

### **🚀 New Features**
- ✅ **Bullets Formatting**: New "bullets" formatting style to automatically create bulleted lists from speech.
- ✅ **Smart Segment Merging**: Intelligent algorithm to merge fragmented speech segments based on confidence and timing.
- ✅ **Adaptive VAD**: Dynamic Voice Activity Detection that adjusts thresholds based on audio characteristics.
- ✅ **Retry Mechanism**: Robust error handling that automatically retries failed transcriptions with fallback parameters.
- ✅ **Quality Metrics**: Detailed quality reporting including confidence scores and low-confidence segment counts.

### **Previous Updates (v2.0.0)**

### **🚀 Performance Revolution**
- ✅ **Instant Model Reuse**: Implemented smart caching to eliminate model loading delays (10-20s saved per file)
- ✅ **Distil-Whisper Support**: Added `distil-medium.en` and `distil-large-v2` for **6x faster** transcription
- ✅ **Optimized Realtime**: New `deque`-based buffering for lower latency and CPU usage
- ✅ **Enhanced Batch Mode**: Shared model instance across batch files for maximum throughput
- ✅ **Smart Beam Search**: Dynamic beam size adjustment (1 for speed, 5 for accuracy)

### **Previous Updates (v1.3.0)**

### **🔴 Realtime Transcription**
- ✅ **Live Audio Capture**: Record and transcribe microphone input in real-time
- ✅ **Instant Feedback**: See text appear as you speak
- ✅ **Audio Visualization**: Dynamic audio level meter
- ✅ **Dual Saving**: Saves both audio recording (WAV) and transcription (MD)
- ✅ **Obsidian Integration**: Auto-saves directly to your vault

### **Previous Updates (v1.2.0)**

### **🚀 Performance Engine Swap**
- ✅ **faster-whisper Integration**: Migrated from `openai-whisper` to `faster-whisper` (CTranslate2)
- ✅ **4x Speed Boost**: Up to 4x faster transcription on both CPU and GPU
- ✅ **Lower Memory Usage**: Significantly reduced RAM consumption
- ✅ **INT8 Quantization**: Optimized for CPU with minimal accuracy loss
- ✅ **GPU Auto-Detection**: Automatic CUDA acceleration when available
- ✅ **Real-time Progress**: Segment-level progress tracking for smooth UX

### **🎨 Modern Dark-Black Theme**
- ✅ **Pure Black Background**: Material Dark theme (`#000000`) perfect for OLED
- ✅ **Premium Color Palette**: Bright Blue, Purple, and Emerald accents
- ✅ **Polished Cards**: Subtle borders and improved spacing
- ✅ **Enhanced Typography**: Larger icons and better font hierarchy
- ✅ **Smooth Animations**: Premium hover effects throughout
- ✅ **Batch Processing**: Dedicated tab for multi-file processing
- ✅ **Settings Persistence**: Preferences saved automatically
- ✅ **Compact Logs**: Cleaner terminal output

### **Previous Updates (v1.1.0)**
- ✅ **100+ Languages**: Support for all Whisper-supported languages
- ✅ **UTF-8 Encoding**: Perfect support for non-Latin scripts