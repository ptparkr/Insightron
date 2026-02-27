# Insightron Codebase Explorer

Welcome to the Insightron codebase! This document serves as a comprehensive guide for developers to understand the structure, concepts, and integration of the Insightron project. Whether you're a seasoned engineer or a newbie, this guide will help you navigate and iterate on the code.

## 🏗️ High-Level Architecture

Insightron is built with a modular, layered architecture that separates core logic from the user interface and external services.

```mermaid
graph TD
    subgraph App Layer
        A[main.py] --> G[GUI Layer]
        A --> C[CLI Layer]
    end

    subgraph Service Layer
        G --> MP[Multi-Pass Transcriber]
        C --> MP
        MP --> TE[Transcription Engine]
        MP --> LLM[LLM Provider]
        MP --> EA[Emotion Analyzer]
    end

    subgraph Core Layer
        TE --> MM[Model Manager]
        TE --> RM[Resource Manager]
        MM --> CFG[Config/Settings]
        RM --> CFG
    end

    subgraph Utilities
        TF[Text Formatter]
        RH[Result Handler]
        AL[Audio Loader]
    end

    MP --> TF
    MP --> RH
    TE --> AL
```

---

## 📁 Directory Breakdown

### 1. `insightron/app/`
The entry point of the application. It orchestrates the startup process and handles both GUI and CLI interfaces.

- **`main.py`**:
  - **Use**: Main entry point for the application.
  - **Concept**: Initializes configurations, checks dependencies, and launches either the GUI or CLI batch processor.
  - **Integration**: Imports `InsightronGUI` from `app.gui` and `batch_transcribe_files` from `services.batch`.

### 2. `insightron/core/`
The backbone of the application, managing system resources, models, and configurations.

- **`config.py`**:
  - **Use**: Centralized configuration management.
  - **Concept**: Loads `config.yaml` and provides access to global settings.
  - **Integration**: Used by almost every other module to fetch parameters.
- **`model_manager.py`**:
  - **Use**: Manages the lifecycle of AI models (Whisper, etc.).
  - **Concept**: Handles model downloading, loading into memory (CPU/GPU), and unloading.
  - **Integration**: Called by `TranscriptionEngine` to get model instances.
- **`resource_manager.py`**:
  - **Use**: Monitors and optimizes system resource usage.
  - **Concept**: Ensures the application doesn't exceed memory limits, especially on low-spec machines.
  - **Integration**: Interacts with `ModelManager` to trigger garbage collection or model offloading.
- **`vad.py`**:
  - **Use**: Voice Activity Detection.
  - **Concept**: Filters out silence or non-speech segments before transcription to save compute.
  - **Integration**: Used by `TranscriptionEngine` for efficient processing.

### 3. `insightron/services/`
Contains the business logic for transcription and post-processing.

- **`transcription/multi_pass_transcriber.py`**:
  - **Use**: Orchestrates the 3-pass transcription pipeline.
  - **Concept**:
    - **Pass 1**: Raw detection using Whisper (`TranscriptionEngine`).
    - **Pass 2**: Contextual restoration using an LLM (`LLMProvider`).
    - **Pass 3**: Emotion mapping (`EmotionAnalyzer`) and optional speaker/structure passes.
  - **Integration**: Coordinates `TranscriptionEngine`, `LLMProvider`, `EmotionAnalyzer`, `TextFormatter`, and `ResultHandler`.
- **`transcription/transcription_engine.py`**:
  - **Use**: Low-level interface for the Whisper model.
  - **Concept**: Handles signal processing and single-pass inference, chunking, and device/model selection.
  - **Integration**: Used by `MultiPassTranscriber` for Pass 1 and by single-pass flows.
- **`transcription/llm_provider.py`**:
  - **Use**: Unified interface for local and cloud LLMs.
  - **Concept**: Wraps providers (e.g. OpenAI, local Qwen) with strict, non‑hallucinating prompts focused on restoration.
- **`transcription/emotion_analyzer.py`**:
  - **Use**: Computes emotion markers (e.g. `[Cheerful]`, `[Urgent]`).
  - **Concept**: Uses speech rate, lexical cues, and configuration thresholds.
- **`transcription/text_formatter.py`**:
  - **Use**: Deterministic formatting (paragraphs, bullets, views).
  - **Concept**: Implements the “typesetter” role from note‑shaping docs.
- **`transcription/result_handler.py` & `markdown_renderer.py`**:
  - **Use**: Turn results into Markdown/other artifacts and write them safely.
  - **Concept**: Atomic writes, frontmatter, and view selection.
- **`transcription/segment_analyzer.py`, `quality_metrics.py`, `metrics_calculator.py`**:
  - **Use**: Advanced quality metrics and adaptive segment merging.
  - **Concept**: Compute confidence tiers, degradation detection, and per‑segment stats.
- **`transcription/audio_loader.py` & `audio_preprocessor.py`**:
  - **Use**: Robust loading, normalization, and preprocessing for all supported formats.
- **`transcription/diarization.py` & `speaker_attribution.py`**:
  - **Use**: Speaker‑aware processing (where enabled).
- **`batch/batch_processor.py`**:
  - **Use**: Handles processing of multiple files in parallel.
  - **Concept**: Uses thread/process pools plus state/resume support (`batch_state_manager.py`, `progress_tracker.py`).
  - **Integration**: Used by the CLI and GUI for "Batch Mode".

### 4. `insightron/ui/`
The presentation layer built with `CustomTkinter`.

- **`components/`**: Modular UI elements like `SettingsPanel`, `FileSelector`, and `ResultsPanel`.
- **`responsive.py`**: Utilities for creating a UI that adapts to different window sizes.
- **`themes/`**: Styling definitions for a premium, modern look.

---

## 🔄 The Multi-Pass Pipeline

The magic of Insightron happens in the **Multi-Pass Pipeline**. Here's how a raw audio file becomes a high-quality transcript:

1.  **Signal Intake**: `AudioLoader` loads the file and converts it to the required sample rate.
2.  **Pass 1 (Detection)**: `TranscriptionEngine` uses Whisper to get raw text with timestamps.
3.  **Pass 2 (Restoration)**: `LLMProvider` takes the raw text and "cleans it up" (e.g., "i am going... to the store" → "I am going to the store.").
4.  **Pass 3 (Emotion)**: `EmotionAnalyzer` adds metadata about the speaker's tone.
5.  **Output**: `TextFormatter` turns the data into readable paragraphs or bullet points, and `ResultHandler` saves it to disk.

---

## 🚀 Guide for Newbie Engineers

### How to Iterate and Build

#### 1. Adding a new "Pass" to the pipeline
If you want to add a "Pass 4" (e.g., Automatic Translation):
1.  Create a new service in `insightron/services/`.
2.  Modify `MultiPassTranscriber.transcribe_multipass` in `insightron/services/transcription/multi_pass_transcriber.py`.
3.  Inject the new service's output into the `MultiPassResult` dataclass.

#### 2. Modifying the UI
1.  Find the relevant component in `insightron/ui/components/`.
2.  If you add a new widget, ensure it uses the `responsive.py` utilities to maintain layout integrity on resize.
3.  Test your changes by running `python insightron.py`.

#### 3. Updating Configurations
1.  Add the new key to `config.yaml`.
2.  Update `insightron/core/config.py` to expose the new parameter.
3.  Add a UI control in `insightron/ui/components/settings_panel.py` if the user needs to change it.

### Best Practices
- **Single Responsibility**: Each module should do one thing well (e.g., `vad.py` only handles voice detection).
- **Resource Efficiency**: Always use `ResourceManager` when loading large models or processing long files.
- **Type Hinting**: Use Python type hints for better IDE support and fewer bugs.

---

*Happy Coding! If you have questions, refer to the [README.md](file:///c:/Users/mshan/Downloads/Developer%20Mode/Insightron/README.md) for installation and basic usage.*
