Here is a Keep a Changelog–style `CHANGELOG.md` you can drop into your repo and tweak dates as needed.

# Changelog

All notable changes to Insightron will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.0] - 2026-03-31

### 🚀 Major Architecture Refactoring

**Performance Focus**: Reduced algorithmic complexity from O(n) to O(1) for config lookups, implemented async startup, and optimized ML resource allocation.

### Added

- ✅ **TOML Configuration**: Migrated from YAML to TOML (`config.toml`) for O(1) config parsing using Python 3.11+ `tomllib`
- ✅ **Resource Pool** (`insightron/core/resources.py`): Unified ML workload resource management with O(1) allocation
- ✅ **Message Bus** (`insightron/core/bus.py`): Event-driven inter-component communication with O(1) pub/sub
- ✅ **Modular Config** (`insightron/core/config/`): Split config into models, loader, and manager for better maintainability
- ✅ **Async Startup**: Non-blocking initialization with `--check` mode for system diagnostics
- ✅ **Lazy Imports**: Deferred module loading for faster startup time

### Changed

- 🔄 **main.py**: Refactored to ~200 LOC with async main, lazy imports, and modular entry points
- 🔄 **Config System**: O(1) lookup via `@cache` decorator instead of O(n) YAML parsing per access
- 🔄 **Entry Points**: New `--check` mode for system health diagnostics
- 🔄 **Backward Compatibility**: Legacy `config.py` preserved with deprecation warnings for YAML config

### Technical Details

- New files:
  - `insightron/core/config/models.py` - Dataclass definitions (frozen=True)
  - `insightron/core/config/loader.py` - TOML loader with caching
  - `insightron/core/config/__init__.py` - Unified config manager
  - `insightron/core/resources.py` - Resource pool (150 LOC)
  - `insightron/core/bus.py` - Message bus (120 LOC)
  - `config.toml` - New TOML configuration (replaces YAML)
- Modified:
  - `insightron/app/main.py` - Async startup, lazy imports
  - `insightron/core/config.py` - Backward compatibility wrapper
  - `insightron/core/__init__.py` - Updated exports

### Deprecations

- ⚠️ `config.yaml` - Migrate to `config.toml` (YAML still supported with warnings)
- ⚠️ Synchronous model loading - Use async patterns for new code

### Performance Improvements

| Operation | Before | After | Method |
|-----------|--------|-------|--------|
| Config access | O(n) | O(1) | @cache + TOML |
| Startup time | ~2s | ~0.5s | Lazy imports |
| Resource detection | Per-call | O(1) | Cached quota |

## [4.0.0] - 2026-02-28

### 🚀 Major Features
- ✅ **Single-Phase Engine Architecture**: New layered mental-model replacing the monolithic transcription flow:
  - **BaseTranscriber** (Ground Truth Layer): Camera-like literal transcription — no cleanup, no guessing
  - **TranscriptionEngine** (Single-Pass Brain): Refines literal output into a usable first draft with light error correction
  - **TextFormatter** (Typesetter): Deterministic formatting into paragraphs, bullets, or named views
  - **ResultHandler** (Contract): Unified output with quality scoring, diarization, and artifact persistence
- ✅ **Dashboard Reports**: New `MarkdownRenderer` with rich quality dashboards including metrics tables, speaker timelines, low-confidence flags, and raw metadata JSON
- ✅ **Audio Preprocessing Pipeline**: New `AudioPreProcessor` with 4-stage pipeline — noise reduction (noisereduce), LUFS normalization (pyloudnorm), pre-emphasis filtering, and edge trimming
- ✅ **Speaker Diarization**: Optional pyannote-powered speaker identification via `Diarizer` and overlap-based `SpeakerAttribution`
- ✅ **FormattingView System**: Named formatting views (`auto`, `thinking_session`, `meeting_notes`, `study_notes`, `bullets`, `minimal`) with per-view sentence limits and LaTeX mode support
- ✅ **Typed Data Contracts**: Frozen dataclasses (`SegmentData`, `WordTimestamp`, `TranscriptionMetrics`, `TranscriptionReport`, `DiarizationResult`, `DiarizationTurn`) for type-safe pipeline data flow

### Added
- ✅ **BaseTranscriber** (`services/base_transcriber.py`): Ground Truth Layer with resource validation, literal transcription using `ModelManager`, and word-level timestamps
- ✅ **AudioPreProcessor** (`services/transcription/audio_preprocessor.py`): Configurable audio preprocessing with `AudioPreprocessConfig` dataclass
- ✅ **MarkdownRenderer** (`services/transcription/markdown_renderer.py`): Dashboard-style reports with quality metrics, speaker timeline, and file hash verification
- ✅ **MetricsCalculator** (`services/transcription/metrics_calculator.py`): Word-level and temporal quality metrics computation
- ✅ **Diarizer** (`services/transcription/diarization.py`): Thin pyannote wrapper with HF token support and configurable speaker constraints
- ✅ **SpeakerAttribution** (`services/transcription/speaker_attribution.py`): Maximum-overlap speaker labeling for ASR segments and words
- ✅ **Contracts Module** (`services/transcription/contracts.py`): Typed data contracts for the entire pipeline
- ✅ **v2 LLM Restoration Philosophy**: Prompt profiles (`thinking_session`, `meeting_notes`, `study_notes`), JSON response contract with `segment_texts` and `flags`, boundary stitching for chunk seams

### Changed
- 🔄 **TranscriptionEngine**: Refactored from generic transcription wrapper to a "Single-Pass Brain" with `process_signal_single_pass()` and ASR artifact deduplication
- 🔄 **TextFormatter**: Introduced `FormattingView` dataclass with named views, configurable sentence limits per view, LaTeX mode (`off`/`safe`/`math`), and view-aware paragraph/bullet break detection
- 🔄 **LLM Provider**: Upgraded to v2 philosophy with `_build_restoration_instructions()` supporting prompt profiles, `_build_restoration_user_content()` with segment-count awareness, and `_parse_json_response()` for structured LLM output
- 🔄 **ResultHandler**: Unified `save_result()` now integrates diarization, formatting profile resolution, dashboard/classic report styles, configurable filename templates, and restoration flag surfacing
- 🔄 **Configuration**: Added `audio_preprocess`, `diarization`, `report.style`, `post_processing.formatting_profile`, and `transcription.filename_template` config sections
- 🔄 **Result Schema**: Updated from `3.1.0-antigravity` to `4.0.0` with structured `analysis.metrics` and `analysis.diarization` fields

### Technical Details
- Added 7 new production files:
  - `insightron/services/base_transcriber.py` (91 lines)
  - `insightron/services/transcription/contracts.py` (93 lines)
  - `insightron/services/transcription/audio_preprocessor.py` (115 lines)
  - `insightron/services/transcription/markdown_renderer.py` (195 lines)
  - `insightron/services/transcription/metrics_calculator.py` (~100 lines)
  - `insightron/services/transcription/diarization.py` (82 lines)
  - `insightron/services/transcription/speaker_attribution.py` (47 lines)
- Modified 4 core files:
  - `services/transcription/transcription_engine.py` (refactored to Single-Pass Brain)
  - `services/transcription/text_formatter.py` (+FormattingView, named views)
  - `services/transcription/llm_provider.py` (+v2 philosophy, prompt profiles)
  - `services/transcription/result_handler.py` (+diarization, dashboard, templates)
- All new modules use typed dataclasses with `frozen=True` for immutability
- Pipeline is fully backward compatible — single-pass remains the default

## [3.1.0] - 2026-01-29

### 🚀 Major Features
- ✅ **Multi-Pass Transcription Pipeline**: Revolutionary 3-pass system that achieves large-model accuracy at small-model speed:
  - **Pass 1 (Detection)**: Fast base model transcription for raw text and timestamps
  - **Pass 2 (Contextual Restoration)**: AI-powered punctuation restoration and phonetic error correction using LLMs
  - **Pass 3 (Emotion Mapping)**: Sentiment analysis that injects emotional markers ([Cheerful], [Urgent], [Calm], [Excited], [Serious])
- ✅ **Intelligent Batch Processing**: 30-second chunking with 2-second overlap for optimal memory usage and context preservation
- ✅ **Flexible LLM Integration**: Support for both local models and API providers:
  - **Local Models**: Qwen2.5-3B-Instruct (recommended), Phi-3-mini, Gemma-2B with 4-bit quantization
  - **API Providers**: OpenAI (GPT-3.5-turbo, GPT-4), with placeholders for Anthropic Claude and Google Gemini

### Added
- ✅ **Emotion Analyzer Module** (`emotion_analyzer.py`): Advanced sentiment detection using word density, exclamation patterns, and keyword analysis
- ✅ **LLM Provider Abstraction** (`llm_provider.py`): Unified interface for local and cloud-based LLMs with retry logic and token tracking
- ✅ **Multi-Pass Orchestrator** (`multi_pass_transcriber.py`): Coordinates all three passes with intelligent chunking and progress tracking
- ✅ **Comprehensive Configuration**: 131 lines of new config options for multi-pass behavior, LLM selection, and emotion thresholds
- ✅ **Pass-Level Progress Callbacks**: Fine-grained progress updates showing which pass is currently running
- ✅ **Processing Time Metrics**: Detailed timing breakdown for each pass (Detection, Restoration, Emotion mapping)

### Changed
- 🔄 **Default Local LLM**: Updated to **Qwen2.5-3B-Instruct** for superior instruction-following and text restoration quality
- 🔄 **AudioTranscriber Integration**: Seamless multi-pass support with automatic routing based on config (backward compatible)
- 🔄 **Configuration Structure**: Added `multi_pass` section to `config.yaml` with granular control over each pass
- 🔄 **Output Metadata**: Transcription results now include multi-pass metrics (restoration time, emotion detection time, Pass 1 preview)

### Technical Details
- Added 4 new production files totaling ~1,550 lines:
  - `insightron/services/transcription/emotion_analyzer.py` (309 lines)
  - `insightron/services/transcription/llm_provider.py` (447 lines)
  - `insightron/services/transcription/multi_pass_transcriber.py` (432 lines)
  - `tests/test_multi_pass.py` (364 lines)
- Modified 2 core files:
  - `config.yaml` (+131 lines)
  - `transcription/transcribe.py` (+89 lines)
- Test coverage: 24 unit tests with 92% pass rate (22/24 passing)
- Multi-pass mode is **opt-in** via `multi_pass.enabled: true` in config for complete backward compatibility

### Performance Characteristics
- **Single-Pass (Default)**: Baseline speed, ~500MB memory
- **Multi-Pass + Local LLM**: ~1.8x slower, ~2GB memory (4-bit quantized), large-model accuracy
- **Multi-Pass + API**: 2-5x slower (network dependent), minimal memory increase, ~$0.002/min (GPT-3.5)

### Usage Example
```yaml
# Enable in config.yaml
multi_pass:
  enabled: true
  contextual_restoration:
    provider: "local"  # or "openai"
    local_model:
      model_name: "Qwen/Qwen2.5-3B-Instruct"
  emotion_mapping:
    enabled: true
```

Then transcribe normally - multi-pass pipeline activates automatically!

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
- ✅ **Realtime Mode (GUI)**: New "Realtime" tab for live microphone transcription with on-screen text as you speak.
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
- ✅ **Multi-Language Support**: Comprehensive support for 100+ languages via Whisper's full language set.
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