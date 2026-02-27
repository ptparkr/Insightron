---
name: insightron-product-roadmap
overview: Multi-phase roadmap to evolve Insightron from an advanced Python project into a polished, offline-first Windows transcription product with optional paid add-ons and minimal resource usage while matching online transcription speed and UX.
todos:
  - id: personas-and-vision
    content: Define target personas, usage scenarios, and document Insightron product vision.
    status: pending
  - id: windows-packaging
    content: Design and implement Windows EXE packaging and installer with shortcuts and versioning.
    status: pending
  - id: performance-profiles
    content: Implement hardware-aware performance profiles and model presets in config and UI.
    status: pending
  - id: job-and-history
    content: Add robust job management, resume, and transcription history UI.
    status: pending
  - id: premium-layer
    content: Design and implement optional premium feature layer with accounts and licensing.
    status: pending
  - id: ecosystem-automation
    content: Expand integrations, CLI, and automation support for advanced users.
    status: pending
isProject: false
---

# Insightron Product & Technical Roadmap

## 1. Vision & Constraints

- **Vision**: Insightron becomes a **Windows-first, offline-capable transcription app** that feels like a polished commercial product, while remaining **fast, privacy-friendly, and mostly free**. Optional **paid add-ons** (cloud LLMs, premium models, productivity features) help sustain development.
- **Key constraints**:
  - **Offline-first**: Core transcription (Whisper/faster-whisper) runs locally, no account required.
  - **Low resource usage**: Runs well on mid-range Windows laptops (integrated GPU or CPU-only) with careful model choices and configuration.
  - **Speed parity**: Match or beat typical online services for common workloads via **distil models, dynamic chunking, GPU/CPU tuning, and batch optimizations**.
  - **Windows UX**: Native-feeling installer, desktop shortcut, tray integration, and crash resilience.

---

## 2. Current State (v3.1.0 Summary)

Based on `[README.md](README.md)` and `[docs/README.md](docs/README.md)`, Insightron already has:

- **Core engine**
  - `faster-whisper` backend with CTranslate2
  - Support for **distil-whisper** models (up to 6x faster)
  - Batch processing, realtime transcription, multi-language support
  - Multi-pass pipeline with local/cloud LLMs and emotion mapping
- **User interfaces**
  - **Python GUI** with dark theme and tabs (Single File, Batch, Realtime)
  - **CLI** (`cli.py`) for power users and automation
- **Dev tooling & structure**
  - Organized `insightron/` package (`app/`, `core/`, `services/`, `ui/`)
  - Tests, benchmarking tool, troubleshooting scripts
  - Cross-platform installers and `config.yaml` runtime configuration

This is already beyond a “weekend project”, but still feels like **developer-centric tooling** rather than a **consumer-grade Windows application**.

---

## 3. Roadmap Overview (Phases)

- **Phase 0 – Productization Foundations (1–2 weeks)**
  - Clarify **target personas** and usage scenarios
  - Stabilize **configuration, presets, and defaults** for performance vs. quality
  - Tighten **error handling and telemetry hooks** (local-only by default)
- **Phase 1 – Windows Desktop Experience (2–4 weeks)**
  - Ship a **one-click Windows installer** (MSI/EXE) that bundles Python and models as needed
  - Make the GUI feel like a **native Windows app** (window behavior, shortcuts, theming)
  - Implement robust **auto-update** and **crash recovery** flows
- **Phase 2 – Performance & Resource Optimization (2–4 weeks)**
  - Systematic **profiling and optimization** for CPU/GPU, RAM, and disk I/O
  - Smart **model presets** ("Laptop Safe", "Blazing Fast", "Studio Quality")
  - Further **batch/realtime tuning** and memory safeguards on Windows
- **Phase 3 – Reliability, Offline-First & UX Polish (3–5 weeks)**
  - Harden pipeline against edge cases, interruptions, and OS quirks
  - Improve **file management**, local history, and preview UX
  - Create **guided flows** for common tasks (meeting transcription, lectures, voice memos)
- **Phase 4 – Optional Paid Features & Accounts (4–6 weeks)**
  - Non-intrusive **account system** (optional, only for premium features)
  - Paid add-ons: cloud LLMs, advanced analytics, team features
  - Respect **offline-only** users: no lock-in, no forced login for core features
- **Phase 5 – Ecosystem, Automation & Pro Power Features (ongoing)**
  - Integrations (e.g. Obsidian already, later Notion/OneNote via export)
  - Scripting/automation hooks, templates, and presets per workflow
  - Enterprise/team deployment options

Below each phase is broken down with concrete tasks and suggested code touchpoints.

---

## 4. Phase 0 – Productization Foundations

### 4.1 Clarify personas & usage modes

- **Primary persona**: Individual Windows user with local files (students, researchers, knowledge workers) wanting **private, fast transcription**.
- **Secondary persona**: Power users automating workflows (CLI + batch + Obsidian integration).
- **Usage modes**:
  - **Single file** (ad hoc usage)
  - **Batch** (podcasts, lecture archives)
  - **Realtime** (meeting notes, dictation)

Document these in `docs/PRODUCT_VISION.md` and reference in main docs.

### 4.2 Configuration hardening & presets

- In `config.yaml` and related loader logic (likely under `insightron/core` or `insightron/services`):
  - Add **named profiles**:
    - `performance_profile: "laptop_safe" | "balanced" | "maximum_quality"`
    - Each profile pre-sets model, compute type, batch size, and multi-pass options.
  - Ensure **sane defaults** for Windows:
    - Prefer `distil-medium.en` for English-only as default where appropriate.
    - Use `device: "auto"` but detect and **cap GPU VRAM usage** or switch to CPU if necessary.
  - Add **validation** with clear error messages if config is invalid or incompatible.

### 4.3 Logging & local telemetry

- Consolidate logging in a `logging` or `metrics` helper (e.g. `insightron/core/logging.py`):
  - Standardize log levels and formats used by GUI and CLI.
  - Add **local-only metrics** (e.g. processing time, RAM peak) written to rotating log files.
- Prepare for potential opt-in **anonymous usage metrics** later (Phase 4) but keep disabled by default.

---

## 5. Phase 1 – Windows Desktop Experience

### 5.1 Windows packaging & distribution

- Choose a **packaging strategy**:
  - **Option A: PyInstaller / Nuitka**
    - Create a single EXE bundling Python and dependencies.
    - Provide models as optional downloads on first run (to keep installer size reasonable).
  - **Option B: `pipx` + helper installer** (lighter, more “developer” oriented; likely secondary).
- Implementation steps:
  - Create `automation/windows/build_exe.py` that:
    - Uses PyInstaller spec to package `insightron.py` and necessary resources.
    - Includes icons and version metadata.
  - Create `automation/windows/create_installer.nsi` (NSIS) or use a modern builder (e.g. Inno Setup, WiX) to:
    - Install EXE + assets to `Program Files\Insightron`.
    - Add **Start Menu shortcut** and optional **desktop shortcut**.
    - Register **file associations** for `.insightronproj` or config-like project files (optional).

### 5.2 Native-feeling GUI on Windows

- Review `insightron/ui` implementation (e.g. Tkinter, PyQt, custom framework) and:
  - Ensure **high DPI awareness** on Windows.
  - Fix window behaviors (minimize to tray support, remember window size/position in `user_settings.json`).
  - Add **standard keyboard shortcuts**:
    - `Ctrl+O` open file
    - `Ctrl+Shift+O` open folder (batch)
    - `Ctrl+R` start/stop realtime recording
    - `Ctrl+,` open settings
- Add a **Settings dialog** separate from raw `config.yaml` editing:
  - UI fields bound to config values (model selection, language, performance profile, save paths).
  - “Restore defaults” button.

### 5.3 Updater & versioning

- Implement a **version check** mechanism:
  - On startup (or manually), app queries GitHub Releases or a hosted JSON for **latest version info**.
  - For offline-only users, make this check **opt-in** and non-blocking.
- For Windows EXE:
  - Offer **in-app link** to “Download latest version” (opens browser) or integrate auto-updater if using an updater framework.
- Standardize versioning in a single source (e.g. `insightron/__init__.py`) and display in About dialog.

### 5.4 Crash resilience

- Wrap main GUI launch in robust try/except layers:
  - Log stack traces to a dedicated `logs/` folder.
  - On next startup, detect last crash and **offer to send anonymized crash report** (opt-in, Phase 4) or at least show a friendly message.

---

## 6. Phase 2 – Performance & Resource Optimization

### 6.1 Systematic benchmarking on Windows

- Extend `benchmark_insightron.py`:
  - Add **Windows-specific system info** (CPU model, RAM, GPU, storage type).
  - Benchmark several **profiles**:
    - `tiny`, `small`, `distil-medium.en`, `medium` on CPU vs GPU where available.
  - Produce human-friendly **HTML/Markdown reports** summarizing trade-offs.
- Use real-world sample workloads:
  - 5-min podcast, 60-min lecture, 20-min meeting.

### 6.2 Adaptive model & profile selection

- Implement a **hardware-detection** module (e.g. `insightron/core/hardware.py`):
  - Check available RAM, CPU cores, GPU presence/VRAM.
- On first run:
  - Suggest a **default profile**:
    - Low RAM (<= 8 GB) → `laptop_safe` (e.g. `tiny`/`base` or `distil-medium.en`).
    - Dedicated GPU → `balanced` with larger model.
- In UI, present **simple choices**:
  - “Optimize for **Speed** / **Balance** / **Accuracy**” with tooltips.

### 6.3 Memory management & streaming

- For batch and realtime services (likely under `insightron/services/transcription`):
  - Ensure audio is processed in **streaming chunks** to avoid large memory spikes.
  - Implement configurable **max concurrent jobs** to avoid oversubscribing CPU/GPU.
  - Add **graceful fallback** when memory is low (reduce batch size, switch to smaller model).

### 6.4 Disk & model management

- Implement a **Model Manager** UI and service:
  - List available models, their sizes, locations.
  - Allow **download/remove** to manage disk usage.
  - Offer **recommended sets** (“Core pack” vs “Full pack”).

---

## 7. Phase 3 – Reliability, Offline-First & UX Polish

### 7.1 Job management & resume

- Introduce a concept of **jobs/transcription projects**:
  - Each job has an ID, status (queued, processing, done, failed), metadata, and output paths.
  - Store job metadata in a lightweight local DB (SQLite) or JSON in `~/.insightron/jobs/`.
- For batch processing:
  - Allow **resume** of partially completed jobs (already partially supported at low level, expose clearly in UI).
  - Show **per-file status** and aggregate progress.

### 7.2 Robust interruption handling

- Handle scenarios:
  - App crash or forced quit during transcription.
  - Laptop sleep/hibernate.
  - Disk full or permission issues.
- Implement **transactional writes** (already mentioned for atomic writes, ensure consistent usage):
  - Write to temp file then move/rename.

### 7.3 UX for common workflows

- Add **guided workflows** in the GUI:
  - “Transcribe a meeting” (with realtime + auto-save + meeting template).
  - “Transcribe a lecture” (batch for long single files, recommended settings).
  - “Quick voice note” (short realtime/recording pipeline with shortcut).
- Provide **templates/presets** for output formatting (e.g. “Meeting Minutes”, “Podcast Transcript”, “Lecture Notes”).

### 7.4 Local history & search

- Implement a **History** tab:
  - Shows recent transcripts, durations, models used, and status.
  - Allows quick **open in folder** / **open in editor**.
- Optional: add **local full-text search** over transcripts using a simple index (can be deferred).

---

## 8. Phase 4 – Optional Paid Features & Accounts

### 8.1 Product boundaries (what stays free)

- **Free forever (offline)**:
  - All core transcription with local Whisper/faster-whisper models.
  - Local multi-pass using local LLMs (assuming user manages models themselves or via local download).
  - Obsidian integration, batch processing, realtime, history.
- **Potential paid add-ons**:
  - Convenient **bundled local LLMs** and curated models (one-click download, pre-configured, managed updates).
  - Cloud LLM integrations: OpenAI, Anthropic, Gemini, etc. with added features (summaries, topic extraction, action items).
  - Team features (shared config, job history, usage analytics) for small orgs.

### 8.2 Account & licensing layer (opt-in)

- Implement a lightweight **account system**:
  - Login/register UI (email + password, or OAuth) in a separate **"Account"** section.
  - Local encryption for stored tokens/keys.
- Licensing checks:
  - All checks should be **non-blocking** for offline users; only premium features should depend on them.
  - Graceful degradation when offline (premium falls back to free equivalents where possible).

### 8.3 Subscription & billing integration

- Use an external billing provider (Stripe, Lemon Squeezy, etc.):
  - Manage subscriptions externally, app just validates entitlements via token or license key.
- Consider **offline license keys** for one-time purchases if subscription is undesirable.

### 8.4 Premium feature UX

- In GUI, clearly mark premium features with **subtle badges**, no dark patterns.
- Allow full use of the app in **free mode** without nagging, except for clear upsell points when user tries premium-only features.

---

## 9. Phase 5 – Ecosystem, Automation & Pro Features

### 9.1 Integration expansions

- Extend beyond Obsidian via **export profiles**:
  - OneNote/Notion templates (via markdown + frontmatter conventions).
  - Simple `Export as .docx` / `.pdf` via optional converters.

### 9.2 Automation & scripting

- Stabilize and document CLI for scripting:
  - Ensure all major GUI features have **CLI equivalents** (multi-pass, profiles, templates).
  - Provide **PowerShell examples** for Windows automation.
- Optional: add a **local HTTP API mode** (e.g. `insightron --serve`) for advanced users.

### 9.3 Teams & collaboration (later stage)

- Shared configuration profiles via synced folders or cloud storage.
- Team dashboards (if premium tier exists) showing aggregated usage, but always respecting privacy.

---

## 10. High-Level Architecture Diagram

```mermaid

User
DesktopGUI
CLI
AppCore
JobManager
ConfigManager
ModelManager
TranscriptionService
WhisperEngine
MultiPassPipeline
LocalLLM
CloudLLM
ObsidianIntegration
HistoryStore
WindowsPackaging
InstallerEXE
Updaterflowchart TD
  user[User] --> gui[DesktopGUI]
  user --> cli[CLI]

  gui --> appCore[AppCore]
  cli --> appCore

  appCore --> jobs[JobManager]
  appCore --> config[ConfigManager]
  appCore --> modelMgr[ModelManager]

  jobs --> transSvc[TranscriptionService]
  transSvc --> whisper[WhisperEngine]
  transSvc --> multiPass[MultiPassPipeline]

  multiPass --> localLLM[LocalLLM]
  multiPass --> cloudLLM[CloudLLM]

  appCore --> obsidian[ObsidianIntegration]
  appCore --> history[HistoryStore]

  appCore --> winPack[WindowsPackaging]
  winPack --> installer[InstallerEXE]
  winPack --> updater[Updater]
```



---

## 11. Suggested Implementation Order (Milestones)

1. **M1 – Solidify core & presets**
  - Add performance profiles and hardware detection.
  - Clean up config validation and logging.
2. **M2 – Windows packaging & UX**
  - Build EXE + installer, add shortcuts, fix DPI and basic Windows UX details.
3. **M3 – Performance tuning**
  - Run benchmarks, adjust defaults, add Model Manager and memory safeguards.
4. **M4 – Reliability & polish**
  - Implement job management, history, and robust interruption handling.
5. **M5 – Optional premium layer**
  - Add account system, entitlements, and clearly bounded premium features.
6. **M6 – Ecosystem & automation**
  - Expand integrations, improve CLI/docs, and consider local API/teams.

---

## 12. High-Level Todos

- **Define product personas and document vision.**
- **Design and implement Windows packaging pipeline (EXE + installer).**
- **Introduce performance profiles and hardware-aware defaults.**
- **Implement job/history management and crash-resilient workflows.**
- **Design optional premium feature set and non-intrusive account/licensing layer.**
- **Expand integrations and automation paths for power users.**

