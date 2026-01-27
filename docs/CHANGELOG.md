Here is a Keep a Changelog–style `CHANGELOG.md` you can drop into your repo and tweak dates as needed.

# Changelog

All notable changes to Insightron will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-01-27

### 🚀 Major Features
- ✅ **New Efficiency Layer**: Implemented a dedicated layer for optimized resource management, handling CPU/RAM usage dynamically.
- ✅ **Advanced VAD System**: Enhanced Voice Activity Detection with adaptive parameters and improved silence pruning for cleaner transcripts.
- ✅ **Dynamic Resource Management**: Introduced sliding window buffering and dynamic chunking to handle large audio streams efficiently on low-spec hardware.
- ✅ **Responsive UI 2.0**: Completely redesigned GUI with a new responsive design system ensuring perfect scaling across all window sizes and resolutions.
- ✅ **Modular Architecture**: Complete refactor of the `AudioTranscriber` service into modular components (`AudioLoader`, `TranscriptionEngine`, `ResultHandler`) for better maintainability.

### Added
- ✅ **Quantization Optimization**: Improved support for INT8/INT4 quantization with significantly reduced memory footprint.
- ✅ **Performance Metrics**: Added `Seconds of Audio processed per CPU Cycle` metric tracking for deeper performance insights.
- ✅ **Extended Documentation**: Comprehensive updates to documentation including new architecture details.

### Changed
- 🔄 **Refactoring**: Massive code cleanup and modularization across the `insightron` package.
- 🔄 **Testing**: Complete overhaul of the test suite with 100% pass rate on the new modular architecture.
- 🔄 **Configuration**: Centralized configuration handling for better consistency across modules.

### Fixed
- 🐛 **Memory Leaks**: Resolved memory leak issues in long-running batch processes.
- 🐛 **Import Paths**: Corrected all import path issues resulting from the restructuring.

## [2.2.0] - 2025-12-05

### Added
- ✅ **Adaptive Segment Merging Algorithm**: Machine-learned gap thresholds that adapt to speaker cadence (fast/slow/normal speech patterns) for more accurate segment merging
- ✅ **Segment Analyzer Module**: Advanced statistical analysis of segment patterns with speech rate detection and adaptive threshold calculation
- ✅ **Enhanced Quality Metrics Calculator**: Comprehensive quality metrics including weighted confidence averages, percentile analysis (p25, p50, p75), quality degradation detection, and quality tiers (excellent/good/acceptable/poor)
- ✅ **Batch State Manager**: JSON-based state persistence for batch processing with resume capabilities after crashes or cancellations
- ✅ **Batch Resume & Recovery**: Enhanced batch processor with automatic retry mechanism (configurable max retries) and resume from previous state
- ✅ **Event-Driven Progress Tracker**: Milestone-based progress tracking system with segment-level events and ETA calculations
- ✅ **Memory Monitor Module**: Real-time memory usage tracking with OOM prevention for batch operations (requires psutil)
- ✅ **Progress Events**: Event types include STARTED, SEGMENT_COMPLETED, MILESTONE, QUALITY_WARNING, ERROR, and COMPLETED

### Changed
- 🔄 **Segment Merging**: Replaced static 0.5s threshold with adaptive algorithm that considers speech rate and gap variability
- 🔄 **Quality Metrics**: Enhanced from simple averaging to weighted scoring by segment duration with degradation detection
- 🔄 **Batch Processing**: Added resume capability with state persistence and automatic retry for failed files
- 🔄 **Code Quality**: Centralized quality metrics calculation in QualityMetricsCalculator to reduce duplication between AudioTranscriber and ModelManager
- 🔄 **Progress Updates**: Replaced arbitrary 5% intervals with meaningful milestone events (25%, 50%, 75%, 100%)

### Technical Details
- Added `transcription/segment_analyzer.py` for adaptive segment analysis
- Added `transcription/quality_metrics.py` for comprehensive quality metrics
- Added `transcription/batch_state_manager.py` for batch state persistence
- Added `transcription/progress_tracker.py` for event-driven progress tracking
- Added `core/memory_monitor.py` for memory usage monitoring
- Updated `transcription/transcribe.py` to use adaptive merging and enhanced quality metrics
- Updated `transcription/batch_processor.py` with resume and retry capabilities
- Updated `core/model_manager.py` to use QualityMetricsCalculator for consistency
- Added `psutil>=5.9.0` to requirements.txt for memory monitoring

## [2.1.0] - 2025-12-04

### Added
- ✅ **Smart Segment Merging**: Confidence-based merging of micro-segments to improve transcription coherence and reduce fragmentation.
- ✅ **Adaptive VAD**: Advanced Voice Activity Detection configuration for better speech isolation in noisy environments.
- ✅ **Robust Error Handling**: Retry mechanism with fallback strategies for transcription failures to ensure reliability.
- ✅ **Bullets Formatting**: New "Bullets" text formatting mode that organizes transcripts into bulleted lists based on paragraph breaks.
- ✅ **GUI Bullets Option**: "Bullets" formatting is now selectable directly from the GUI dropdown.
- ✅ **Configurable Optimizations**: New settings in `config.yaml` for segment merging, VAD parameters, and retry logic.

### Changed
- 🔄 **Installation**: Improved `install_windows.bat` and dependency checks to fix issues with Rust, Visual Studio Build Tools, and `tokenizers`.
- 🔄 **Dependencies**: Updated `requirements.txt` to use `faster-whisper>=1.2.0` and compatible `tokenizers` versions.
- 🔄 **Text Formatter**: Enhanced sentence splitting to better handle abbreviations and improved paragraph detection.
- 🔄 **Runtime Checks**: `insightron.py` now correctly verifies `faster-whisper` presence instead of `openai-whisper`.
- 🔄 **Refactoring**: Replaced `pkg_resources` with `importlib.metadata` for faster and warning-free version checking.

### Fixed
- 🐛 **Realtime Transcription**: Resolved "auto" language code error and GUI note saving issues.
- 🐛 **Batch Processing**: Fixed `ThreadPoolExecutor` mocking in tests and ensured robust batch processing.
- 🐛 **Installation Scripts**: Corrected dependency verification logic in setup scripts to prevent false negatives.

## [2.0.0] - 2025-12-03

### Added
- ✅ **Model Manager & Caching**: Central `ModelManager` for sharing a single Whisper/faster-whisper model instance across single, batch, and realtime modes, eliminating repeated load delays.
- ✅ **Distil-Whisper Models**: Support for `distil-medium.en` and `distil-large-v2` for significantly faster English transcription.
- ✅ **Realtime Buffering**: Deque-based buffering for smoother, low-latency realtime transcription and reduced CPU overhead.
- ✅ **Benchmark Suite**: `benchmark_insightron.py`, sample audio, and `benchmark_results.json` to measure performance across models and modes.

### Changed
- 🔄 **Batch Processing**: Batch mode now reuses a shared model instance for all files to maximize throughput.
- 🔄 **Decoding Strategy**: Smarter beam search defaults with dynamic beam size tuned for either speed or accuracy.
- 🔄 **Configuration**: `config.yaml` extended with model, device, and compute-type options aligned with the new Model Manager.
- 🔄 **Architecture**: Project modularized into `core`, `transcription`, `realtime`, `gui`, `setup`, `scripts`, and `tests` for clearer separation of concerns.

### Technical Details
- Added a centralized `ModelManager` used across CLI, GUI, batch, and realtime pipelines.
- Updated `config.yaml` schema to capture model preferences, device selection, and compute type (e.g., INT8).
- Refactored core logic from `insightron.py` into dedicated modules under `core/`, `transcription/`, and `realtime/`.
- Introduced benchmarking flow that generates test audio, runs single, batch, and realtime simulations, and saves metrics to JSON.

***

## [1.3.0] - 2025-12-01

### Added
- ✅ **Realtime Mode (GUI)**: New “Realtime” tab for live microphone transcription with on-screen text as you speak.
- ✅ **Audio Level Visualization**: Dynamic audio meter to monitor input levels during recording.
- ✅ **Dual Saving**: Automatic saving of both raw audio (e.g., WAV) and Markdown transcript for each realtime session.
- ✅ **Realtime Obsidian Integration**: Realtime transcripts saved directly into the configured Obsidian vault folder.

### Changed
- 🔄 **User Settings**: `user_settings.json` extended to persist realtime preferences (model, language, folders).
- 🔄 **Status & Logging**: GUI log and status bar updated to show realtime recording state, latency, and save locations.

### Technical Details
- Added a dedicated `realtime/` module for microphone capture, buffering, and streaming transcription.
- Integrated realtime pipeline with existing formatting and Markdown export to keep output consistent.

***

## [1.2.0] - 2025-12-01

### Added
- ✅ **faster-whisper Backend**: Migrated core transcription engine from `openai-whisper` to `faster-whisper` (CTranslate2).
- ✅ **INT8 Quantization**: Support for compute-type selection (e.g., `int8`) to optimize CPU performance.
- ✅ **GPU Auto-Detection**: Automatic use of CUDA GPU when available for major speedups.

### Changed
- 🔄 **Performance**: Up to roughly 4x faster transcription on CPU/GPU with significantly lower RAM usage, especially for medium/large models.
- 🔄 **Progress Reporting**: Improved segment-level progress updates for smoother UX in both CLI and GUI.

### Technical Details
- Updated transcription pipeline to call faster-whisper models with configurable device and compute-type parameters.
- Adjusted default model recommendations and docs to highlight `distil-medium.en` and faster-whisper–based models.

***

## [1.1.0] - 2025-10-20

### Added
- ✅ **Multi-Language Support**: Comprehensive support for 100+ languages via Whisper’s full language set.
  - Auto-detection of language from audio content.
  - Manual language selection for improved accuracy.
  - Coverage of major, European, Asian, and Middle Eastern/African languages, plus many more.
- ✅ **UTF-8 Encoding**: Proper handling of non-Latin scripts and special characters in all transcripts.
- ✅ **GUI Language Selector**: Easy language selection directly in the graphical interface.
- ✅ **CLI Language Support**: Command-line language selection via `-l/--language`.[1]
- ✅ **Language Validation**: Automatic fallback to auto-detection for invalid or unsupported language codes.
- ✅ **Enhanced Logging**: More detailed language detection and processing information in logs.

### Changed
- 🔄 **Version**: Updated from v1.0.0 to v1.1.0.
- 🔄 **Documentation**: Added comprehensive multi-language examples and usage guides in README and usage docs.
- 🔄 **Configuration**: Introduced language-related configuration options to `config` and runtime settings.
- 🔄 **Transcription Engine**: Extended to support language-specific parameters and behavior.
- 🔄 **GUI Interface**: Added a language dropdown with all supported language options.
- 🔄 **CLI Interface**: Extended CLI parser to accept `-l, --language` for language selection.

### Technical Details
- Added `SUPPORTED_LANGUAGES` configuration mapping for 100+ languages.
- Enhanced the transcription classes and functions to accept a language parameter.
- Improved UTF-8 handling throughout the pipeline for international character sets.
- Implemented validation and fallback logic when an unsupported language is requested.

### Examples
```bash
# Auto-detection (recommended)
python cli.py audio.mp3 -l auto

# Specific languages
python cli.py spanish_audio.mp3 -l es -m medium
python cli.py french_audio.wav -l fr -m large
python cli.py chinese_audio.m4a -l zh -v
python cli.py arabic_audio.mp3 -l ar -f paragraphs
python cli.py hindi_audio.wav -l hi -m medium
```

***

## [1.0.0] – 2025-10-20

### Added
- ✅ Initial public release of Insightron.
- ✅ Whisper AI integration with multiple model sizes (tiny, base, small, medium, large).
- ✅ Modern macOS-inspired dark GUI interface.
- ✅ Command-line interface with rich options for model, language, formatting, and output paths.
- ✅ Obsidian integration for seamless, Markdown-first note-taking workflows.
- ✅ Smart text formatting with multiple styles (auto, paragraphs, minimal, etc.).
- ✅ Comprehensive audio format support (MP3, WAV, M4A, FLAC, MP4, OGG, AAC, WMA).
- ✅ Atomic file operations to ensure data safety during writes.
- ✅ Progress tracking and real-time status updates during transcription.
- ✅ Cross-platform compatibility (Windows, macOS, Linux).
- ✅ Robust error handling and validation for files, paths, and runtime issues.
- ✅ Detailed documentation and examples for both GUI and CLI usage.
- ✅ Performance-oriented defaults and memory-efficient processing.
- ✅ Audio metadata extraction (duration, size, etc.) embedded in output.
- ✅ Timestamp support for transcript segments.
- ✅ Rich Markdown output with Obsidian-friendly frontmatter and metadata.
- ✅ Troubleshooting and diagnostic helpers for installation and runtime issues.     

***

**Legend:**
- ✅ Added  
- 🔄 Changed  
- ❌ Deprecated  
- 🗑️ Removed  
- 🐛 Fixed  
- 🔒 Security  