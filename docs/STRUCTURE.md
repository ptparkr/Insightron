# Insightron Codebase Structure

## Overview

Insightron has been restructured into a modern, professional application architecture with clear separation of concerns and modular design.

## Directory Structure

```
Insightron/
├── insightron/                   # Main package (formerly src)
│   ├── app/                      # Application entry points
│   │   ├── main.py               # Main entry point (GUI + CLI logic)
│   │   ├── gui/                  # GUI application
│   │   │   └── main_window.py    # Main GUI window
│   │   └── cli/                  # CLI components
│   │       └── cli.py             # CLI application logic
│   ├── core/                     # Core functionality
│   │   ├── config.py             # Configuration management
│   │   ├── model_manager.py      # Whisper model management
│   │   ├── settings_manager.py   # User settings persistence
│   │   ├── utils.py              # Utility functions
│   │   ├── memory_monitor.py     # Memory monitoring
│   │   ├── resource_manager.py   # Efficiency Layer (CPU/RAM management)
│   │   └── vad.py                # Voice Activity Detection
│   ├── services/                 # Business logic services
│   │   ├── base_transcriber.py   # Ground Truth Layer (literal transcription)
│   │   ├── transcription/        # Transcription services
│   │   │   ├── transcribe.py     # Legacy wrapper (backward compat)
│   │   │   ├── transcription_engine.py # Single-Pass Brain
│   │   │   ├── audio_loader.py   # Audio loading & preprocessing
│   │   │   ├── audio_preprocessor.py # Audio preprocessing pipeline
│   │   │   ├── contracts.py      # Typed data contracts
│   │   │   ├── result_handler.py # Result formatting & saving
│   │   │   ├── markdown_renderer.py # Dashboard report renderer
│   │   │   ├── metrics_calculator.py # Word-level quality metrics
│   │   │   ├── text_formatter.py # FormattingView-based typesetter
│   │   │   ├── quality_metrics.py # Risk/quality scoring
│   │   │   ├── segment_analyzer.py # Adaptive segment merging
│   │   │   ├── diarization.py    # Speaker diarization (pyannote)
│   │   │   ├── speaker_attribution.py # Speaker labeling
│   │   │   ├── multi_pass_transcriber.py # Multi-pass orchestrator
│   │   │   ├── llm_provider.py   # LLM provider abstraction
│   │   │   └── emotion_analyzer.py # Emotion detection
│   │   ├── batch/                # Batch processing
│   │   │   ├── batch_processor.py
│   │   │   ├── batch_state_manager.py
│   │   │   └── progress_tracker.py
│   │   └── realtime/             # Real-time transcription
│   │       └── realtime_transcriber.py
│   └── ui/                       # UI components
│       ├── components/           # Reusable UI components (header, panels)
│       └── themes/               # Theme management
├── automation/                   # Automation scripts
│   ├── setup/                    # Installers (setup.py, install.py)
│   └── scripts/                  # Utilities (benchmark, troubleshooting)
├── tests/                        # Test suite and benchmarks
├── docs/                         # Documentation
├── config.yaml                   # Configuration file
├── insightron.py                 # Root GUI/App entry point
└── cli.py                        # Root CLI entry point
```

## Module Purposes

### `insightron/app/`
**Purpose**: Application entry points and main application logic.
- **`main.py`**: Initializes the application context and validation.
- **`gui/`**: Contains the CustomTkinter GUI logic.
- **`cli/`**: Contains the argparse CLI logic.

### `insightron/core/`
**Purpose**: Core functionality and foundational components.
- **`config.py`**: Typesafe configuration management using `ConfigManager`.
- **`model_manager.py`**: Central singleton for model loading and inference.
- **`resource_manager.py`**: Handles dynamic resource allocation and constraints.
- **`vad.py`**: Configurable Voice Activity Detection logic.

### `insightron/services/`
**Purpose**: Pure business logic, independent of UI.
- **`base_transcriber.py`**: Ground Truth Layer — camera-like literal transcription with resource validation.
- **`transcription/`**:
    - **`transcription_engine.py`**: Single-Pass Brain — refines literal output into a usable first draft.
    - **`audio_loader.py`**: Robust audio loading with format conversion.
    - **`audio_preprocessor.py`**: 4-stage audio preprocessing (noise reduction, LUFS, pre-emphasis, trim).
    - **`contracts.py`**: Typed frozen dataclasses for pipeline data (`SegmentData`, `TranscriptionMetrics`, etc.).
    - **`result_handler.py`**: Manages output generation with formatting profiles and dashboard/classic reports.
    - **`markdown_renderer.py`**: Dashboard-style Markdown reports with quality metrics and speaker timelines.
    - **`metrics_calculator.py`**: Word-level and temporal quality metrics computation.
    - **`text_formatter.py`**: FormattingView-based typesetter with named views and LaTeX support.
    - **`diarization.py`**: pyannote speaker diarization wrapper.
    - **`speaker_attribution.py`**: Overlap-based speaker labeling for segments and words.
    - **`llm_provider.py`**: v2 LLM restoration with prompt profiles and JSON response contract.
    - **`emotion_analyzer.py`**: Emotion detection with configurable thresholds.
- **`batch/`**: Manages multi-processing/threading for bulk files.
- **`realtime/`**: Audio stream capturing and live transcription.

## Import Patterns

All imports now use absolute paths rooted at the `insightron` package:

### Core Modules
```python
from insightron.core.config import ConfigManager, get_config_manager
from insightron.core.model_manager import ModelManager
```

### Services
```python
from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.batch.batch_processor import batch_transcribe_files
```

## Running the Application

### GUI Mode
```bash
python insightron.py
```

### CLI Mode
```bash
python cli.py --help
```

## Migration Notes (v4.0.0)

- The `src` directory has been renamed to `insightron` to be a proper Python package.
- All `from src...` imports have been updated to `from insightron...`.
- Legacy root folders (`core`, `transcription`, etc.) have been merged into `insightron`.
- New modules added: `base_transcriber.py`, `contracts.py`, `audio_preprocessor.py`, `markdown_renderer.py`, `metrics_calculator.py`, `diarization.py`, `speaker_attribution.py`.
- `TranscriptionEngine` refactored to Single-Pass Brain with `process_signal_single_pass()`.
- `TextFormatter` now uses `FormattingView` dataclass with named views.
- `ResultHandler` supports dashboard/classic report styles and formatting profiles.
