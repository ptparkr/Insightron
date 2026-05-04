# Insightron Architecture Documentation

## Overview

Insightron is a professional-grade AI audio transcription application built with Python, leveraging OpenAI's Whisper technology through the faster-whisper implementation. The application features a modular, layered architecture that separates concerns across multiple domains: core configuration, transcription services, UI/presentation, and batch processing.

## Version

**Current Version**: 4.1.1

---

## 1. High-Level Architecture

Insightron follows a **layered architecture** pattern with clear separation between:

1. **Entry Points** - Application startup (CLI, GUI, Web)
2. **Core Layer** - Configuration, resource management, model loading
3. **Services Layer** - Business logic (transcription, batch processing, realtime)
4. **Presentation Layer** - GUI components, Web API
5. **Utilities** - Helpers, themes, settings

### 1.1 Directory Structure

```
insightron/
├── app/                    # Application entry points
│   ├── main.py            # Main entry point (GUI/Batch)
│   ├── gui/               # Tkinter-based GUI
│   │   └── main_window.py # Main GUI window
│   └── auto_ingest.py     # Auto file monitoring
├── core/                   # Core functionality
│   ├── config.py          # Configuration management
│   ├── model_manager.py   # Whisper model loading/caching
│   ├── resource_manager.py # System resource monitoring
│   ├── settings_manager.py # User preferences
│   ├── memory_monitor.py  # Memory usage tracking
│   ├── vad.py            # Voice Activity Detection
│   └── utils.py           # Utility functions
├── services/               # Business logic services
│   ├── base_transcriber.py # Ground truth layer
│   ├── transcription/     # Transcription pipeline
│   │   ├── transcription_engine.py # Single-pass brain
│   │   ├── multi_pass_transcriber.py # 3-pass pipeline
│   │   ├── transcribe.py  # Main transcription orchestrator
│   │   ├── audio_loader.py # Audio file loading
│   │   ├── audio_preprocessor.py # Audio preprocessing
│   │   ├── text_formatter.py # Output formatting
│   │   ├── result_handler.py # Result saving
│   │   ├── speaker_attribution.py # Speaker diarization
│   │   ├── emotion_analyzer.py # Emotion detection
│   │   ├── llm_provider.py # LLM integration
│   │   └── ...
│   ├── batch/             # Batch processing
│   │   ├── batch_processor.py # Batch orchestration
│   │   ├── batch_state_manager.py # State persistence
│   │   └── batch_summary.py # Summary generation
│   └── realtime/          # Realtime transcription
│       └── realtime_transcriber.py
├── ui/                     # UI components
│   ├── components/        # Reusable UI components
│   ├── themes/           # Theme management
│   └── responsive.py      # Responsive layout
└── utils/                  # Utilities

automation/                 # Setup scripts
docs/                       # Documentation
```

---

## 2. Entry Points

### 2.1 Main Entry (insightron/app/main.py)

The `main.py` serves as the primary application orchestrator, supporting two distinct modes:

1. **GUI Mode** (default) - Launches CustomTkinter-based desktop application
2. **Batch Mode** (`batch` subcommand) - CLI-based batch processing

```python
# Entry flow:
main() 
  ├── check_dependencies()    # Validate required packages
  ├── check_paths()           # Validate configured directories
  └── run_gui() / run_batch()
```

### 2.2 Legacy Entry (run_insightron.py)

Legacy script wrapper that ensures the repo root is on Python path before importing the main application module.

---

## 3. Core Layer

### 3.1 Configuration System (config.py)

The configuration system uses a **Singleton Pattern** with YAML file support:

```
ConfigManager (Singleton)
├── model: ModelConfig          # Whisper model settings
├── audio_preprocess: AudioPreProcessConfig  # Audio preprocessing
├── diarization: DiarizationConfig            # Speaker diarization
├── runtime: RuntimeConfig     # Runtime paths & worker settings
├── realtime: RealtimeConfig    # Realtime transcription
├── post_processing: PostProcessingConfig    # Text formatting
├── transcription: TranscriptionConfig       # Segment handling
└── multi_pass: MultiPassConfig  # Multi-pass pipeline
```

**Key Features**:
- YAML-based configuration with dot-notation access
- Automatic directory creation
- Configuration validation with defaults
- Singleton pattern ensures single configuration instance

**Configuration Dataclasses**:
- `DecodeConfig` - Whisper decoding parameters (temperature, beam_size, etc.)
- `ModelConfig` - Model selection, compute type, device, VAD settings
- `AudioPreProcessConfig` - Noise reduction, LUFS normalization, pre-emphasis
- `DiarizationConfig` - pyannote speaker diarization settings
- `MultiPassConfig` - LLM restoration and emotion mapping

### 3.2 Model Manager (model_manager.py)

**Purpose**: Manages Whisper model loading, caching, and inference

**Design Pattern**: Singleton with thread-safe lazy loading

**Key Features**:
- Model caching (loads once, reuses across requests)
- Thread-safe model loading with `_load_lock`
- Quality modes: `high`, `balanced`, `fast`
- Dynamic beam size optimization based on audio duration
- Adaptive VAD parameter tuning based on audio characteristics
- Model warmup for optimized first inference
- Retry mechanism with fallback parameters

**Core Methods**:
```python
class ModelManager:
    def load_model() -> WhisperModel
    def transcribe(audio, language, task) -> (segments, info)
    def get_quality_metrics(segments) -> Dict
```

**Model Parameters** (DEFAULT_PARAMS):
- `beam_size`: 5 (accuracy priority)
- `best_of`: 5
- `temperature`: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] (fallback chain)
- `word_timestamps`: True
- VAD filtering enabled by default

### 3.3 Resource Manager (resource_manager.py)

**Purpose**: System resource monitoring and optimization recommendations

**Key Features**:
- CPU core detection
- RAM availability monitoring (via psutil)
- Optimal worker count calculation based on:
  - Available CPU cores (reserves 1-2 for system)
  - Available RAM (model size determines memory per worker)
- Quantization recommendation (int8 for constrained systems)
- Health status checking

**Memory Estimates per Worker**:
- tiny/base: ~0.5 GB
- small: ~1 GB
- medium: ~2 GB
- large: ~4 GB

---

## 4. Services Layer

### 4.1 Transcription Pipeline Architecture

Insightron implements a **layered transcription philosophy**:

```
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                            │
│  TextFormatter → ResultHandler → File Output               │
├─────────────────────────────────────────────────────────────┤
│                  QUALITY ENHANCEMENT                        │
│  EmotionAnalyzer → SpeakerAttribution → QualityMetrics    │
├─────────────────────────────────────────────────────────────┤
│                  SINGLE-PASS BRAIN                        │
│  TranscriptionEngine → Error Resolution → Normalization   │
├─────────────────────────────────────────────────────────────┤
│                   GROUND TRUTH LAYER                       │
│  BaseTranscriber → ModelManager → Whisper Model           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Ground Truth Layer (base_transcriber.py)

**Mental Model**: Camera, not editor

**Responsibilities**:
- Raw audio-to-text conversion without modifications
- Preserves hesitations, repetitions, uncertainty markers
- No cleanup, no formatting, no guessing
- Returns literal output with word-level timestamps

**Key Constraint**: `condition_on_previous_text=False` to prevent model "smoothing"

### 4.3 Single-Pass Brain (transcription_engine.py)

**Mental Model**: First draft that must be usable

**Responsibilities**:
- Light normalization
- Obvious ASR error resolution
- Boundary break fixes
- Timestamp adjustment for chunked audio

**Key Constraint**: No lookahead rewriting, no stylistic changes

### 4.4 Multi-Pass Transcriber (multi_pass_transcriber.py)

Implements a **3-pass pipeline** for enhanced transcription quality:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   PASS 1     │ -> │   PASS 2     │ -> │   PASS 3     │
│  Detection   │    │ Restoration  │    │   Emotion    │
│  (Whisper)   │    │   (LLM)      │    │   Mapping    │
└──────────────┘    └──────────────┘    └──────────────┘
```

**Pass 1: Detection**
- Uses TranscriptionEngine for raw transcription
- Chunks audio into 30-second segments with 2-second overlap
- Processes chunks sequentially

**Pass 2: Contextual Restoration**
- Uses LLM (local or cloud) for punctuation and formatting
- Maintains segment boundaries
- Supports:
  - Local models (Qwen2.5-3B-Instruct)
  - Cloud APIs (OpenAI GPT)
- JSON response contracts for structured output

**Pass 3: Emotion Mapping**
- Analyzes text for emotional content
- Injects emotion markers: [Cheerful], [Urgent], [Calm], [Excited], [Serious]
- Based on:
  - Words per second (energy)
  - Exclamation marks
  - Sentence length

### 4.5 Audio Processing Pipeline

**AudioLoader** (audio_loader.py):
- Validates audio files
- Loads audio as numpy arrays
- Provides metadata (duration, sample rate, channels)
- Segments audio by time

**AudioPreprocessor** (audio_preprocessor.py):
- Noise reduction (stationary/progressive)
- LUFS loudness normalization (-23 LUFS target)
- Pre-emphasis filtering
- Edge trimming (top_db threshold)

### 4.6 Text Formatting (text_formatter.py)

Supports multiple formatting styles:
- `auto` - Smart paragraph breaks
- `paragraphs` - Every 3 sentences
- `minimal` - Every 5 sentences
- `bullets` - Bullet point format
- `thinking_session` - Thinking session format
- `meeting_notes` - Meeting notes format
- `study_notes` - Study notes format

---

## 5. Batch Processing

### 5.1 Batch Processor (batch_processor.py)

**Purpose**: Process multiple audio files concurrently

**Design**:
- ThreadPoolExecutor or ProcessPoolExecutor
- Automatic worker count optimization via ResourceManager
- CUDA-aware (uses threads when GPU available)

**Features**:
- Resume capability (BatchState persistence)
- Retry mechanism (default: 2 retries)
- Progress callbacks
- Batch summary generation

**Worker Flow**:
```
BatchTranscriber
├── transcribe_batch(files)
│   ├── Initialize BatchState
│   ├── Submit to Executor
│   ├── For each completed:
│   │   ├── Check success/failure
│   │   ├── Retry if failed (up to max_retries)
│   │   └── Update progress
│   └── Generate summary
```

### 5.2 Batch State Manager (batch_state_manager.py)

**Purpose**: Track batch processing state for resume capability

**States per File**:
- `pending` - Not yet processed
- `in_progress` - Currently being processed
- `success` - Completed successfully
- `failed` - Permanently failed

---

## 6. Realtime Transcription

### 6.1 RealtimeTranscriber (realtime_transcriber.py)

**Purpose**: Live audio transcription from microphone input

**Key Features**:
- Continuous audio capture
- Voice Activity Detection (VAD)
- Streaming transcription
- Audio level visualization
- Recording save (WAV format)

**Buffer Configuration**:
- `buffer_duration_seconds`: 30
- `chunk_duration_seconds`: 5
- `stride_seconds`: 1
- `silence_threshold`: 0.015
- `silence_duration`: 0.5

---

## 7. Presentation Layer

### 7.1 GUI (app/gui/main_window.py)

**Framework**: CustomTkinter (modern Tkinter wrapper)

**Architecture**: Component-based with responsive layout

**Main Components**:
```
InsightronGUI
├── Header
├── TabView
│   ├── Single File Tab
│   │   ├── FileSelector
│   │   └── TranscribeButton
│   ├── Batch Tab
│   │   ├── FileSelector
│   │   └── ProcessButton
│   └── Realtime Tab
│       ├── AudioVisualizer
│       ├── MicSelector
│       └── RecordButton
├── SettingsPanel
├── ProgressPanel
└── ResultsPanel
```

**Key Features**:
- Responsive layout (adapts to window size)
- Dark theme (CustomTkinter Dark mode)
- Async service initialization
- Threaded transcription (non-blocking UI)

---

## 8. UI Components

### 8.1 Component Architecture

All UI components follow a common pattern:
- Wrapper class that encapsulates CTk widgets
- `get_widget()` method to access the root widget
- ResponsiveManager integration for adaptive layouts

**Core Components**:
- `Header` - Application header with branding
- `FileSelector` - File/folder selection (single/multiple)
- `SettingsPanel` - Model, language, formatting controls
- `ProgressPanel` - Progress indication
- `ResultsPanel` - Output log display
- `AudioVisualizer` - Audio level visualization
- `SettingsPanel` - Configuration options

### 8.2 Theme System

**ThemeManager**:
- Singleton theme provider
- Design tokens (colors, spacing, typography)
- Layout modes (STANDARD, COMPACT, WIDE)

**Design Tokens**:
- Colors: background, surface, primary, accent, text_*, border
- Spacing: xs, sm, md, lg, xl
- Typography: font sizes by level
- Corner radius: by component size

---

## 9. Configuration Flow

### 9.1 Startup Sequence

```
1. run_insightron.py
   └── insightron/app/main.py
       ├── ConfigManager.__init__()
       │   └── Load config.yaml
       ├── Create UI/Start Web/Run Batch
       └── (Lazy) ModelManager.load_model()
           └── WhisperModel initialization
```

### 9.2 Configuration Priority

1. Default values (hardcoded in dataclasses)
2. config.yaml file values
3. Runtime overrides (if any)

---

## 10. Key Design Patterns

### 10.1 Singleton Patterns

- **ConfigManager**: Single configuration instance
- **ModelManager**: Single model instance per process
- **ResourceManager**: Single resource monitor

### 10.2 Factory Patterns

- **LLMProviderFactory**: Creates LLM providers (local/cloud)
- **ThemeManager**: Provides theme objects

### 10.3 Strategy Patterns

- **TextFormatter**: Multiple formatting strategies
- **BatchProcessor**: Thread/process execution strategies

### 10.4 Observer Patterns

- **ResponsiveManager**: Layout change notifications
- **Progress callbacks**: Progress updates

---

## 11. Data Flow Examples

### 11.1 Single File Transcription

```
User selects file
    ↓
AudioTranscriber.transcribe_file(path)
    ↓
AudioLoader.load_signal(path)
    ↓
ModelManager.transcribe(audio)
    ↓
faster_whisper.WhisperModel.transcribe()
    ↓
TextFormatter.format(segments)
    ↓
ResultHandler.save_result()
    ↓
Output file (.md)
```

### 11.2 Multi-Pass Transcription

```
AudioFile
    ↓
MultiPassTranscriber.transcribe_multipass()
    ├── Pass 1: TranscriptionEngine.process_signal_single_pass()
    │       └── BaseTranscriber → ModelManager → Whisper
    ├── Pass 2: llm_provider.restore_text()
    │       └── Local/Cloud LLM
    └── Pass 3: emotion_analyzer.analyze_chunks()
            └── Emotion markers injection
    ↓
FormattedOutput
```

### 11.3 Batch Processing

```
Input: List[AudioFiles]
    ↓
batch_transcribe_files(files)
    ↓
BatchTranscriber.transcribe_batch()
    ├── BatchState initialization
    └── Executor.submit() for each file
        ├── Worker: AudioTranscriber.transcribe_file()
        └── Result → BatchState.update()
    ↓
Results + Summary
```

---

## 12. Extension Points

### 12.1 Adding New Transcription Modes

1. Implement transcriber class inheriting from `BaseTranscriber`
2. Add entry point in `main.py`
3. Configure in `config.yaml`

### 12.2 Adding New LLM Providers

1. Implement provider class with `restore_text()` method
2. Register in `LLMProviderFactory`
3. Configure in `config.yaml`

### 12.3 Adding New Formatting Styles

1. Implement formatter class
2. Register in TextFormatter
3. Add to FORMATTING_STYLES in config

---

## 13. Dependencies

### 13.1 Core Dependencies

- **faster-whisper**: Whisper inference (3-4x faster, 50% less memory)
- **customtkinter**: Modern GUI framework
- **numpy**: Audio processing
- **librosa**: Audio analysis
- **pyyaml**: Configuration

### 13.2 Optional Dependencies

- **pyannote.audio**: Speaker diarization
- **transformers**: Local LLM support
- **openai**: Cloud LLM support
- **psutil**: Resource monitoring

---

## 14. Configuration Reference

### 14.1 Model Configuration

```yaml
model:
  name: medium              # tiny/base/small/medium/large/large-v2/large-v3
  compute_type: int8        # float16/int8_float16/int8/float32
  device: auto             # auto/cpu/cuda
  quality_mode: balanced    # high/balanced/fast
  enable_vad: true
  enable_retry: true
  decode:
    beam_size: 5
    temperature: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    word_timestamps: true
```

### 14.2 Audio Preprocessing

```yaml
audio_preprocess:
  enabled: true
  noise_reduction:
    enabled: true
    stationary: true
    prop_decrease: 0.75
  loudness:
    enabled: true
    target_lufs: -23.0
```

### 14.3 Multi-Pass Configuration

```yaml
multi_pass:
  enabled: true
  chunk_duration: 30
  chunk_overlap: 2
  contextual_restoration:
    enabled: true
    provider: local  # local/api
    local_model:
      model_name: Qwen/Qwen2.5-3B-Instruct
      quantization: 4bit
  emotion_mapping:
    enabled: false
    enabled_emotions: [cheerful, urgent, calm, excited, serious]
```

---

## 16. Performance Considerations

### 16.1 Speed Optimizations

- **Distil-Whisper**: 6x faster than base Whisper
- **Dynamic Chunking**: Process long audio in chunks
- **Model Warmup**: First inference optimization
- **Adaptive Beam**: Lower beam for short audio

### 16.2 Memory Optimizations

- **int8 Quantization**: 50% memory reduction
- **Lazy Loading**: Models loaded on-demand
- **Streaming**: For very large files

### 16.3 Concurrency

- **CPU**: ProcessPoolExecutor with auto worker count
- **GPU**: ThreadPoolExecutor (avoids VRAM thrashing)

---

## 17. Error Handling

### 17.1 Retry Strategy

1. **Attempt 1**: Full quality (config beam_size)
2. **Attempt 2**: Reduced quality (beam_size=3, simplified temperature)
3. **Attempt 3**: Fast fallback (beam_size=1, VAD disabled)

### 17.2 Resource Constraints

- Pre-flight resource check before batch
- Graceful degradation on memory pressure
- Warning on high CPU/memory usage

---

## Appendix: Key File Locations

| File | Purpose |
|------|---------|
| `insightron/app/main.py` | Main entry point |
| `insightron/core/config.py` | Configuration management |
| `insightron/core/model_manager.py` | Whisper model management |
| `insightron/services/transcription/transcribe.py` | Main transcription orchestrator |
| `insightron/services/transcription/multi_pass_transcriber.py` | Multi-pass pipeline |
| `insightron/services/batch/batch_processor.py` | Batch processing |
| `insightron/app/gui/main_window.py` | GUI application |
| `config.toml` | Application configuration |

---

*Generated for Insightron v4.1.1*
