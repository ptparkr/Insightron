# Insightron – Full Product & Technical Roadmap

> **Version:** 1.0 | **Base:** v3.1.0 | **Last updated:** February 2026
>
> **North Star:** Insightron becomes the go-to Windows-first, offline-capable transcription tool that feels like a polished commercial product — fast, private, and mostly free — with optional paid add-ons to sustain development.

---

## Table of Contents

1. [Product Vision & Constraints](#1-product-vision--constraints)
2. [Target Personas](#2-target-personas)
3. [Current State (v3.1.0)](#3-current-state-v310)
4. [Architecture Overview](#4-architecture-overview)
5. [Phase 0 – Productization Foundations](#5-phase-0--productization-foundations-weeks-12)
6. [Phase 1 – Windows Desktop Experience](#6-phase-1--windows-desktop-experience-weeks-36)
7. [Phase 2 – Performance & Resource Optimization](#7-phase-2--performance--resource-optimization-weeks-710)
8. [Phase 3 – Reliability, Offline-First & UX Polish](#8-phase-3--reliability-offline-first--ux-polish-weeks-1115)
9. [Phase 4 – Optional Paid Features & Accounts](#9-phase-4--optional-paid-features--accounts-weeks-1621)
10. [Phase 5 – Ecosystem, Automation & Pro Features](#10-phase-5--ecosystem-automation--pro-features-ongoing)
11. [Milestone Summary](#11-milestone-summary)
12. [Definition of Done Checklist](#12-definition-of-done-checklist)

---

## 1. Product Vision & Constraints

### Vision

Insightron evolves from a capable developer tool into a **polished, consumer-grade Windows transcription product**. Core transcription stays offline and free. Optional paid tiers — cloud LLMs, curated model packs, and team features — sustain development without alienating the privacy-first audience.

### Guiding Constraints

| Constraint | What it means in practice |
|---|---|
| **Offline-first** | Core Whisper transcription runs fully locally. No account, no internet required for core features. |
| **Low resource usage** | Runs well on mid-range Windows laptops (integrated GPU or CPU-only). No assumption of high-end hardware. |
| **Speed parity with online services** | Match or beat web-based transcription for common file types via distil models, dynamic chunking, and tuned batch processing. |
| **Native Windows UX** | One-click installer, desktop shortcut, DPI awareness, tray support, crash recovery. Feels like it shipped on Windows, not ported to it. |
| **Free core, non-intrusive premium** | Premium features are clearly marked and accessible. Core users face zero nagging or forced login. |

---

## 2. Target Personas

Document these in `docs/PRODUCT_VISION.md`.

### Persona A – The Knowledge Worker (Primary)

- **Who:** Student, researcher, journalist, freelancer on Windows
- **Needs:** Transcribe lectures, interviews, meetings privately and quickly
- **Pain points:** Cloud tools feel risky (privacy), slow on large files, require constant internet
- **How they use Insightron:** GUI, single file or batch, occasional realtime
- **Success metric:** "It just worked, faster than uploading to an online tool"

### Persona B – The Power User / Automator (Secondary)

- **Who:** Developer, productivity enthusiast, podcast editor
- **Needs:** CLI integration, batch pipelines, Obsidian/Notion export, scriptable automation
- **Pain points:** GUI-only tools can't be scripted; most transcription apps have no headless mode
- **How they use Insightron:** CLI + batch + integrations
- **Success metric:** "I automated my entire interview-to-notes pipeline"

### Persona C – The Team Buyer (Future / Phase 4+)

- **Who:** Small team lead, content ops manager
- **Needs:** Shared config, centralized history, consistent output formatting across team
- **Pain points:** Everyone has a different setup; can't standardize workflows
- **How they use Insightron:** Premium tier with shared profiles and usage analytics
- **Success metric:** "Everyone on the team transcribes the same way"

---

## 3. Current State (v3.1.0)

Insightron is already beyond a weekend project. It has:

**Core Engine**
- `faster-whisper` backend with CTranslate2
- `distil-whisper` model support (up to 6× faster than standard Whisper)
- Batch processing, realtime transcription, multi-language support
- Multi-pass pipeline with local and cloud LLM integration, emotion mapping

**User Interfaces**
- Python GUI (dark theme, tabbed: Single File / Batch / Realtime)
- CLI (`cli.py`) for power users and automation

**Dev Tooling**
- Organized `insightron/` package structure (`app/`, `core/`, `services/`, `ui/`)
- Tests, benchmarking tool, troubleshooting scripts
- Cross-platform install scripts, `config.yaml` runtime configuration

**Gap:** Despite the solid foundation, Insightron still reads as developer tooling rather than a consumer Windows product. The phases below bridge that gap systematically.

---

## 4. Architecture Overview

```
User
├── Desktop GUI (insightron/ui/)
└── CLI (cli.py)
        │
        ▼
    AppCore (insightron/app/)
    ├── ConfigManager      ← config.yaml, profiles, validation
    ├── JobManager         ← job queue, resume, status, SQLite store
    ├── ModelManager       ← download, cache, remove models
    └── HistoryStore       ← local transcript index, search
        │
        ▼
    TranscriptionService (insightron/services/)
    ├── WhisperEngine      ← faster-whisper, distil models
    └── MultiPassPipeline
        ├── LocalLLM       ← optional, user-managed
        └── CloudLLM       ← optional, premium tier

    Integrations
    ├── ObsidianExport
    ├── NotionExport (Phase 5)
    └── DocxPdfExport (Phase 5)

    Windows Layer
    ├── InstallerEXE       ← PyInstaller + NSIS/Inno Setup
    └── Updater            ← GitHub Releases version check
```

---

## 5. Phase 0 – Productization Foundations (Weeks 1–2)

**Goal:** Lock the product vision, harden config and logging, and ensure a clean development baseline before investing in packaging and UX.

---

### 5.1 Define & Document Product Vision

**Deliverable:** `docs/PRODUCT_VISION.md`

Tasks:
- Write up the three personas above with usage scenarios
- Document what is **free forever** vs. **premium add-on** (align with Phase 4 boundaries)
- State the performance baseline target: "Transcribe a 60-minute file in under 8 minutes on a mid-range CPU-only laptop"
- Commit this file — it becomes the north star for every later design decision

---

### 5.2 Configuration Hardening & Named Profiles

**Files to touch:** `insightron/core/config.py` (or wherever `config.yaml` is loaded), `config.yaml`

#### 5.2.1 Add named performance profiles

Add top-level `performance_profile` key to `config.yaml`:

```yaml
performance_profile: balanced   # laptop_safe | balanced | maximum_quality | custom
```

Implement a profile resolver that pre-sets these values:

| Profile | Model | Compute type | Batch size | Multi-pass | Notes |
|---|---|---|---|---|---|
| `laptop_safe` | `distil-small.en` | `int8` | 4 | Off | Runs on 4GB RAM, integrated GPU |
| `balanced` | `distil-medium.en` | `int8_float16` | 8 | Off | Default for most users |
| `maximum_quality` | `large-v3` | `float16` | 4 | On (local LLM) | Requires dedicated GPU |
| `custom` | (user-set) | (user-set) | (user-set) | (user-set) | Reads raw config values |

If `performance_profile` is not `custom`, profile values **override** individual settings in config. Log a warning if user has set overridden keys manually.

#### 5.2.2 Hardware detection at startup

In `insightron/core/hardware.py` (create if needed):
- Detect available CUDA devices and their VRAM
- Detect total system RAM
- Auto-suggest a profile if none is set (write suggestion to log, ask user in first-run wizard later)
- Implement `device: "auto"` logic that caps GPU VRAM to a configurable threshold (default: 80% of available VRAM) and falls back to CPU if threshold would be exceeded

#### 5.2.3 Config validation

- Add a `validate_config()` function that runs on startup
- Raise descriptive errors (not stack traces) for:
  - Invalid profile names
  - Model not found locally (offer download suggestion)
  - Conflicting settings (e.g. `batch_size > 1` with `device: cpu` for large models)
- Surface validation errors in the GUI as a dismissible banner (not a modal)

---

### 5.3 Logging & Local Telemetry

**Files to touch / create:** `insightron/core/logging.py`, `insightron/core/metrics.py`

#### 5.3.1 Standardize logging

- Single `get_logger(name)` helper used everywhere (GUI, CLI, services)
- Log levels: `DEBUG` (dev), `INFO` (normal ops), `WARNING` (recoverable issues), `ERROR` (failures)
- Log format: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [module] message`
- Rotate logs: keep last 5 files, max 5 MB each, stored in `~/.insightron/logs/`

#### 5.3.2 Local performance metrics

- After each transcription job, append to `~/.insightron/metrics.jsonl`:
  ```json
  { "ts": "...", "duration_s": 120, "audio_s": 3600, "model": "distil-medium.en",
    "device": "cuda", "peak_ram_mb": 1240, "rtf": 0.033 }
  ```
  RTF = real-time factor (processing time / audio duration). Lower is better.
- These metrics power the History tab in Phase 3 and benchmarking in Phase 2.

#### 5.3.3 Prepare opt-in anonymous telemetry hook (disabled by default)

- Create `insightron/core/telemetry.py` with a `send_event(event_name, payload)` function
- For now, the function does nothing — it just logs locally
- In Phase 4, flip the implementation to POST to a backend if user has opted in
- This keeps the interface stable so Phase 4 doesn't require refactoring callers

---

## 6. Phase 1 – Windows Desktop Experience (Weeks 3–6)

**Goal:** Ship a one-click Windows installer. Make the GUI feel native on Windows. Add versioning and crash recovery.

---

### 6.1 Windows Packaging & Distribution

**New files:** `automation/windows/build_exe.py`, `automation/windows/installer.iss` (Inno Setup) or `installer.nsi` (NSIS)

#### 6.1.1 Choose and implement packaging strategy

**Recommended approach: PyInstaller + Inno Setup**

PyInstaller spec (`insightron.spec`):
```python
a = Analysis(
    ['insightron.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('insightron/ui/assets', 'ui/assets'),
        ('config.yaml', '.'),
        ('docs/', 'docs/'),
    ],
    hiddenimports=['faster_whisper', 'ctranslate2'],
    ...
)
exe = EXE(a.pure, a.scripts, ..., name='Insightron', icon='ui/assets/icon.ico')
```

`automation/windows/build_exe.py` should:
1. Run `pyinstaller insightron.spec --clean`
2. Embed version number from `insightron/__init__.py`
3. Output to `dist/Insightron-{version}-windows-x64/`

#### 6.1.2 Installer (Inno Setup)

`automation/windows/installer.iss` should:
- Install to `{pf}\Insightron` (Program Files)
- Create Start Menu shortcut
- Offer optional Desktop shortcut (checked by default)
- Register `Insightron.exe` in Add/Remove Programs with version info
- (Optional) Register `.itranscript` file association for saved project files
- Include uninstaller

**Model bundling strategy:**
- Do NOT bundle models in the installer (would make it 1–4 GB)
- On first launch, detect no models and trigger a "First Run" wizard (see 6.2.3)

#### 6.1.3 CI build pipeline

Create `.github/workflows/build-windows.yml`:
- Trigger: push to `release/**` branch or manual dispatch
- Steps: checkout → set up Python → `pip install` deps → `pyinstaller` → build installer → upload artifact
- On tagged release: attach installer to GitHub Release

---

### 6.2 Native-Feeling GUI on Windows

**Files to touch:** everything under `insightron/ui/`

#### 6.2.1 DPI awareness & scaling

- Call `SetProcessDPIAware()` (via `ctypes`) before GUI initialization on Windows
- Test at 100%, 125%, 150%, 200% display scaling
- Ensure fonts, icons, and layout scale correctly — no blurry text, no clipped buttons

#### 6.2.2 Window state persistence

Create `~/.insightron/user_settings.json`:
```json
{
  "window": { "x": 100, "y": 100, "width": 900, "height": 600 },
  "last_tab": "single_file",
  "last_output_folder": "C:\\Users\\...",
  "theme": "dark"
}
```
- Save on window close, restore on open
- If saved position is off-screen (e.g. after monitor change), reset to center

#### 6.2.3 First-Run Wizard

Trigger when `~/.insightron/user_settings.json` does not exist:
1. **Welcome screen** – product name, one-line pitch, "Get Started" button
2. **Hardware detection screen** – show detected CPU/GPU/RAM, suggest a profile, allow override
3. **Model download screen** – show recommended model for chosen profile, size, download button
   - Download to `~/.insightron/models/`
   - Show progress bar
   - Allow "Skip for now" (user can download later from Model Manager)
4. **Done screen** – brief tip on drag-and-drop

#### 6.2.4 Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open file (Single File tab) |
| `Ctrl+Shift+O` | Open folder (Batch tab) |
| `Ctrl+R` | Start / Stop realtime recording |
| `Ctrl+,` | Open Settings |
| `Ctrl+H` | Open History |
| `Ctrl+M` | Open Model Manager |
| `Ctrl+Q` | Quit |
| `F1` | Open documentation |
| `Esc` | Cancel active transcription (with confirm dialog) |

#### 6.2.5 Settings Dialog

Replace raw `config.yaml` editing with a proper Settings dialog (`Ctrl+,`):
- **General tab:** Output folder, language default, auto-open output
- **Performance tab:** Profile picker, device selector, VRAM cap slider
- **Advanced tab:** Raw config values (for power users), "Restore defaults" button
- **About tab:** Version, links to docs and changelog, check for updates button
- Bind all fields to `config.yaml` via the ConfigManager — no direct file writes from the dialog

#### 6.2.6 System Tray Integration

- On close, offer: "Minimize to tray" or "Quit"
- Tray icon with context menu: Show / Hide, Start Realtime, Open History, Quit
- Show tray notification on job completion: "Meeting_audio.mp4 transcribed in 2m 14s"

---

### 6.3 Versioning & Auto-Update

**Files to touch:** `insightron/__init__.py`, new `insightron/services/updater.py`

- Single version source: `insightron/__init__.py` → `__version__ = "3.2.0"`
- On startup (non-blocking, background thread): check `https://api.github.com/repos/{owner}/insightron/releases/latest`
- If newer version found: show subtle banner in GUI ("Version 3.3.0 available – Download")
- Make version check **opt-in** — config key `check_for_updates: true` (default true, but respectable if toggled off)
- No auto-download or auto-install — always open browser to release page

---

### 6.4 Crash Resilience

**Files to touch:** `insightron/app/main.py`, new `insightron/core/crash_handler.py`

- Wrap top-level GUI launch in try/except
- On unhandled exception:
  1. Write full traceback to `~/.insightron/logs/crash_{timestamp}.log`
  2. Show friendly dialog: "Insightron encountered an unexpected error. [View log] [Copy error] [Close]"
- On next startup: detect crash log from last session → offer "Send crash report" (opt-in, in Phase 4, for now just show "A crash was detected. View log?")
- Implement a **job checkpoint** before any destructive operation: save current job state to `~/.insightron/jobs/{id}.checkpoint.json` so it can be resumed after crash

---

## 7. Phase 2 – Performance & Resource Optimization (Weeks 7–10)

**Goal:** Profile systematically on Windows, implement adaptive model selection, lock in memory safeguards, and deliver the Model Manager UI.

---

### 7.1 Windows Benchmarking Suite

**Files to touch:** `benchmark_insightron.py`

Extend to produce a proper benchmark report:

#### 7.1.1 System fingerprint

Capture at benchmark start:
- CPU model, core count, clock speed
- Total RAM, available RAM
- GPU model, VRAM (if present)
- Storage type (SSD/HDD via WMI or `psutil`)
- OS version, Python version, faster-whisper version

#### 7.1.2 Standardized test workloads

Maintain a small set of reference audio files in `tests/benchmarks/audio/`:

| File | Duration | Content | Why |
|---|---|---|---|
| `short_en.mp3` | 5 min | English podcast clip | Baseline for fast turnaround |
| `medium_en.mp3` | 20 min | Meeting recording | Typical use case |
| `long_en.mp3` | 60 min | Lecture | Stress test, memory pressure |
| `noisy_en.mp3` | 5 min | Noisy environment | Quality stress test |

#### 7.1.3 Report output

After each benchmark run, write `benchmark_report_{timestamp}.html` with:
- Table of RTF (real-time factor) per model × workload × device
- Memory usage charts (peak RAM, VRAM)
- Recommended profile for the tested hardware
- Side-by-side comparison with previous run if available

---

### 7.2 Adaptive Model & Profile Selection

**Files to touch:** `insightron/core/hardware.py`, `insightron/core/config.py`

#### 7.2.1 Hardware-aware default profile

At startup, if no profile is set and it's not the first run:
1. Check available VRAM
   - < 2 GB or no GPU → suggest `laptop_safe`
   - 2–4 GB VRAM → suggest `balanced`
   - > 4 GB VRAM → suggest `maximum_quality`
2. Log suggestion; don't silently override the user's existing choice

#### 7.2.2 Dynamic fallback during runtime

In `TranscriptionService`:
- Monitor RAM usage every 10 seconds during batch jobs
- If free RAM drops below 500 MB:
  1. Reduce batch size by half (minimum 1)
  2. Log warning: "Memory pressure detected, reducing batch size"
- If free RAM drops below 200 MB:
  1. Pause queue after current job
  2. Show banner: "Low memory detected. Pausing queue. [Resume] [Reduce model]"

#### 7.2.3 VRAM cap enforcement

- Before loading a model, estimate VRAM requirement: `model_size_gb * 1.3` (rough safety factor)
- If estimated requirement > (available VRAM × configured cap percentage):
  - Auto-switch `device` to `cpu` for this job
  - Log: "VRAM insufficient for {model} on GPU, falling back to CPU"

---

### 7.3 Batch & Realtime Tuning

**Files to touch:** `insightron/services/transcription.py`, `insightron/services/realtime.py`

#### 7.3.1 Streaming chunks for large files

- For files > 30 minutes, process in chunks of configurable duration (default: 10 minutes)
- Maintain a sliding context window across chunk boundaries to avoid cut-word artifacts
- Stream output to file incrementally — don't hold entire transcript in memory

#### 7.3.2 Configurable job concurrency

Add to config:
```yaml
max_concurrent_jobs: 2   # 1 = sequential, 2+ = parallel (requires more RAM)
```
Default to `1` on `laptop_safe` profile, `2` on `balanced`, `3` on `maximum_quality`.

#### 7.3.3 Realtime latency tuning

- Expose `realtime_chunk_duration_ms` in config (default: 500ms)
- On `laptop_safe` profile, increase to 1000ms to reduce CPU pressure
- Show latency in realtime status bar: "~600ms delay"

---

### 7.4 Model Manager UI

**New:** `insightron/ui/model_manager.py`, `insightron/services/model_manager.py`

The Model Manager is accessible via `Ctrl+M` or the menu.

#### Service layer (`insightron/services/model_manager.py`)

- `list_local_models()` → list of `{name, size_gb, path, last_used}`
- `list_available_models()` → fetch from hosted JSON or hard-coded manifest
- `download_model(name, on_progress)` → streams download, calls progress callback
- `remove_model(name)` → deletes from disk, updates config if it was the active model
- `get_recommended_pack(hardware_profile)` → returns a list of model names

#### UI layer

Display a two-panel layout:
- **Left panel:** Installed models (name, size on disk, last used date, [Remove] button)
- **Right panel:** Available models (name, size to download, quality rating, [Download] button)
- Bottom bar: total disk used by models / disk free
- "Core Pack" and "Full Pack" quick-install buttons

---

## 8. Phase 3 – Reliability, Offline-First & UX Polish (Weeks 11–15)

**Goal:** Harden the pipeline against real-world edge cases, deliver job history, and add guided workflows for non-technical users.

---

### 8.1 Job Management & Resume

**New:** `insightron/services/job_manager.py`, `insightron/core/job_store.py`

#### 8.1.1 Job data model

Each job has:
```python
@dataclass
class Job:
    id: str                    # UUID
    created_at: datetime
    updated_at: datetime
    status: str                # queued | processing | done | failed | cancelled
    job_type: str              # single | batch | realtime
    input_paths: list[str]
    output_paths: list[str]
    model: str
    profile: str
    total_files: int
    completed_files: int
    failed_files: int
    error_message: str | None
    duration_audio_s: float
    duration_processing_s: float
    checksum: str              # hash of input files, for dedup
```

#### 8.1.2 Persistence

Store in SQLite at `~/.insightron/history.db`:
- Table `jobs` — one row per job
- Table `job_files` — one row per file in a batch job (for per-file status)
- Table `transcripts` — links job → output path → word count → language detected

#### 8.1.3 Resume logic

On batch job start:
1. Compute checksum of input folder / file list
2. Check `history.db` for a previous job with the same checksum and status `processing` or `failed_partial`
3. If found: offer "Resume previous job?" dialog showing progress (e.g. "47/120 files completed")
4. If resumed: skip files that are in `job_files` with status `done`

---

### 8.2 Robust Interruption Handling

#### 8.2.1 Transactional output writes

All output file writes must be atomic:
```python
import tempfile, shutil, os

def write_transcript(content: str, target_path: str):
    dir_ = os.path.dirname(target_path)
    with tempfile.NamedTemporaryFile('w', dir=dir_, delete=False, suffix='.tmp') as f:
        f.write(content)
        tmp_path = f.name
    shutil.move(tmp_path, target_path)  # atomic on same filesystem
```

Never write directly to the final output path — a crash mid-write would leave a corrupted file.

#### 8.2.2 Signal handling

Register handlers for:
- `SIGINT` / `Ctrl+C` in CLI: finish current segment, flush output, exit cleanly
- `WM_QUERYENDSESSION` (Windows shutdown): save job checkpoint, flush logs

#### 8.2.3 Disk space pre-check

Before starting a job:
- Estimate output size: `input_audio_duration_s * 150` (bytes, rough estimate for text output)
- Check free disk space
- If free space < estimated output × 2: show warning dialog, do not start job silently

#### 8.2.4 Permission error handling

Wrap all file I/O in try/except `PermissionError` and `OSError`:
- Surface as clear error message: "Cannot write to [path]. Check that the folder exists and is not read-only."
- Log full traceback at DEBUG level

---

### 8.3 Guided Workflows

Add a **Workflows** menu (or quick-launch panel on the home screen) with three pre-configured flows:

#### Workflow 1: Transcribe a Meeting

1. User selects audio/video file (or starts realtime recording)
2. Auto-selects `balanced` profile with speaker diarization enabled
3. Output template: "Meeting Minutes" (speaker labels, timestamps, action items section)
4. Auto-saves to `~/Documents/Insightron/Meetings/YYYY-MM-DD/`
5. Option: open in Obsidian when done

#### Workflow 2: Transcribe a Lecture

1. User selects file or folder (supports multi-file lecture series)
2. Auto-selects `maximum_quality` or `balanced` based on hardware
3. Long-file chunking enabled automatically
4. Output template: "Lecture Notes" (headings for each 10-min segment, summary footer)
5. Auto-names files: `Lecture_{source_filename}_{date}.md`

#### Workflow 3: Quick Voice Note

1. One-click from tray or `Ctrl+Shift+R` global hotkey
2. Starts realtime recording immediately (no setup dialog)
3. Auto-selects `laptop_safe` for speed
4. On stop: auto-saves to `~/Documents/Insightron/VoiceNotes/` and copies text to clipboard
5. Tray notification: "Voice note saved (42 words)"

---

### 8.4 Output Templates

**New:** `insightron/services/template_engine.py`, `~/.insightron/templates/`

Built-in templates (stored as `.j2` Jinja2 files in `insightron/assets/templates/`):

| Template | Variables | Output |
|---|---|---|
| `plain.txt.j2` | `{transcript}` | Raw transcript text |
| `timestamped.txt.j2` | `{segments}` | `[00:01:23] Text...` |
| `meeting_minutes.md.j2` | `{segments}`, `{speakers}`, `{date}` | Markdown with speaker labels and action items section |
| `lecture_notes.md.j2` | `{segments}`, `{source_file}` | Markdown with 10-min section headings |
| `podcast_transcript.md.j2` | `{segments}`, `{speakers}` | Clean dialogue format |

User can add custom templates to `~/.insightron/templates/` — these appear in the template picker alongside built-ins.

---

### 8.5 History Tab & Local Search

**New:** `insightron/ui/history_tab.py`

The History tab (`Ctrl+H`) shows:
- Table: Filename | Date | Duration | Model | Status | RTF
- Filters: date range picker, status filter, model filter
- Per-row actions: Open output folder, Open in editor, Re-transcribe, Delete record
- Search bar: searches transcript text (if stored) or just metadata
- Export: "Export history as CSV"

For local full-text search (Phase 3 stretch goal):
- On job completion, index the transcript text using SQLite FTS5
- Search bar queries FTS index: results highlight matching segments

---

## 9. Phase 4 – Optional Paid Features & Accounts (Weeks 16–21)

**Goal:** Add a non-intrusive account system and premium feature layer. Core features must remain fully functional with zero account interaction.

---

### 9.1 Product Tier Boundaries

**Free forever (no account required):**
- All local transcription (all Whisper/distil-whisper models)
- Local multi-pass pipeline with user-managed local LLMs
- All export formats and templates
- Obsidian integration, batch processing, realtime, history, all workflows
- CLI and automation features

**Premium add-ons (account required):**
- One-click curated model bundles (pre-configured, auto-updated, professionally tested packs)
- Cloud LLM integrations: OpenAI, Anthropic, Gemini, Azure — for summaries, topic extraction, action items, Q&A over transcripts
- Priority support
- Team features (Phase 4+): shared config profiles, team history dashboard, usage analytics

**Design rule:** Every premium feature must degrade gracefully. If user is offline or license lapses, premium features disappear but core features continue working without error.

---

### 9.2 Account System

**New:** `insightron/services/auth.py`, `insightron/ui/account_dialog.py`

#### 9.2.1 Account UI

Accessible via menu: Account → Sign In / Manage Account.
- Never shown unprompted unless user clicks a premium feature
- Login form: email + password or "Continue with Google" (OAuth2 via browser)
- Stores refresh token encrypted in system keychain (`keyring` library on Windows)
- Account section shows: current plan, expiry, manage subscription link (opens browser)

#### 9.2.2 License/entitlement check

- On login, fetch entitlements JSON from backend and cache locally with expiry
- On premium feature use: check cached entitlements
- If cache expired and offline: use last known entitlements (grace period: 7 days)
- If grace period expired: disable premium features with message "Could not verify license. Connect to internet to continue using premium features."
- Never block core features regardless of entitlement state

#### 9.2.3 Offline license keys (alternative for one-time buyers)

- Support `license_key` in `config.yaml`
- Validate via asymmetric signature (app holds public key, backend signs license)
- Works fully offline after initial activation

---

### 9.3 Premium Features Implementation

#### 9.3.1 Cloud LLM integration

Extend `MultiPassPipeline` to support cloud LLM providers:
- Provider config in `config.yaml`:
  ```yaml
  cloud_llm:
    provider: openai   # openai | anthropic | gemini | azure
    api_key: "..."     # stored encrypted in keychain, not plain yaml
    model: gpt-4o-mini
  ```
- Premium actions available post-transcription:
  - **Summarize** (1-paragraph summary)
  - **Extract action items** (returns structured list)
  - **Extract topics** (returns tag list)
  - **Ask a question** (free-form Q&A over transcript text)
- Results appended to transcript output as a separate section, never replacing the transcript

#### 9.3.2 Model packs

Premium model packs are pre-configured bundles sold as one-time purchases:
- **Accuracy Pack:** `large-v3`, `medium.en`, configured for maximum accuracy
- **Speed Pack:** optimized `distil-large-v3` with tuned batch settings
- **Multilingual Pack:** models + language-specific config for 10+ languages

Model pack download is handled by the Model Manager (Phase 2) with entitlement check added.

---

### 9.4 Premium UX Guidelines

- Mark premium features with a subtle `★ Pro` badge — no flashing, no popups
- When a free user clicks a `★ Pro` feature: show a single non-intrusive tooltip: "This is a premium feature. [Learn more]" — opens a browser page
- After 3 such clicks: offer a non-modal in-app banner (once, dismissible forever)
- Zero upsell in core transcription flow — no "upgrade to get more" overlays during transcription

---

### 9.5 Opt-in Anonymous Telemetry

Now implement the telemetry hook from Phase 0:
- On first launch after account system ships, ask once: "Help improve Insightron by sharing anonymous usage data? [Yes, send data] [No thanks]"
- If yes: `telemetry.py` sends events (job completed, model used, RTF, error type) to backend — no audio, no transcript content, no personal data
- Telemetry preference stored in `user_settings.json`, changeable in Settings → Privacy

---

## 10. Phase 5 – Ecosystem, Automation & Pro Features (Ongoing)

**Goal:** Grow the power-user and team ecosystem. Make Insightron a platform, not just an app.

---

### 10.1 Integration Expansions

**Extend beyond Obsidian:**

| Integration | Mechanism | Priority |
|---|---|---|
| **Obsidian** (existing) | File write + frontmatter | Done |
| **Notion** | Notion API or markdown export | High |
| **OneNote** | Markdown + `.docx` export | Medium |
| **Export as .docx** | `python-docx` or `pandoc` | High |
| **Export as .pdf** | `pandoc` or headless Chrome | Medium |
| **Zapier/Make webhook** | POST to user-configured URL | Low |

For each integration, the export is triggered post-transcription (either automatically or via right-click → Export As in History tab).

---

### 10.2 CLI Hardening & Documentation

**Goal:** Every GUI feature has a CLI equivalent. Power users can build full pipelines.

Ensure these CLI flags exist and are documented:
```
insightron transcribe <file> [--profile balanced] [--model distil-medium.en]
                              [--language en] [--template meeting_minutes]
                              [--output ./out/] [--format md|txt|json]

insightron batch <folder> [--recursive] [--resume] [--concurrency 2]

insightron realtime [--duration 60] [--template voice_note] [--copy-clipboard]

insightron models list
insightron models download <model-name>
insightron models remove <model-name>

insightron history list [--limit 20] [--format json]
insightron history search "query"

insightron serve [--port 8765]   # local HTTP API mode (see 10.3)
```

Provide PowerShell example scripts in `docs/examples/powershell/`:
- `auto-transcribe-watch-folder.ps1` — watches a folder, auto-transcribes new audio files
- `batch-lecture-series.ps1` — transcribes a numbered lecture series in order
- `meeting-to-obsidian.ps1` — transcribes and exports to Obsidian vault

---

### 10.3 Local HTTP API Mode

`insightron --serve` starts a local HTTP server on `localhost:8765`:

```
POST /transcribe        { "path": "...", "profile": "...", "template": "..." }
GET  /jobs              → list all jobs
GET  /jobs/{id}         → job status and output paths
POST /jobs/{id}/cancel
GET  /models            → installed models
POST /models/download   { "name": "..." }
GET  /history           → recent transcripts
```

This enables integration from any language, not just Python. Document with curl examples.

---

### 10.4 Teams & Collaboration

*(Deferred until premium tier is validated)*

- Shared configuration profiles via Dropbox/OneDrive sync folder (user-configured sync path)
- Team dashboard (browser-based, hosted, premium) showing:
  - Total hours transcribed per team member
  - Models used, average RTF
  - Export formats most used
- Team admin can push config profiles to team members via a shared JSON URL
- All team features respect offline-first: local app works independently even if team backend is unreachable

---

## 11. Milestone Summary

| Milestone | Phase | Target completion | Key deliverable |
|---|---|---|---|
| **M0 – Vision locked** | 0 | Week 1 | `docs/PRODUCT_VISION.md`, named profiles, logging standardized |
| **M1 – Windows installer** | 1 | Week 5 | One-click EXE installer, first-run wizard, keyboard shortcuts |
| **M2 – Native UX** | 1 | Week 6 | Settings dialog, tray integration, crash recovery, auto-update check |
| **M3 – Benchmarked & tuned** | 2 | Week 9 | Benchmark report on 3 hardware tiers, adaptive profiles, memory safeguards |
| **M4 – Model Manager** | 2 | Week 10 | Download/remove models in-app, recommended packs |
| **M5 – Reliable jobs** | 3 | Week 13 | SQLite job store, batch resume, atomic writes, interruption handling |
| **M6 – UX polish** | 3 | Week 15 | Guided workflows, output templates, History tab with search |
| **M7 – Premium layer** | 4 | Week 20 | Account system, entitlements, cloud LLM features, model packs |
| **M8 – Telemetry & feedback** | 4 | Week 21 | Opt-in telemetry, crash reporting, feedback button |
| **M9 – Ecosystem** | 5 | Ongoing | CLI parity, local API, Notion/docx export, PowerShell examples |
| **M10 – Teams** | 5 | Ongoing | Shared profiles, team dashboard (premium) |

---

## 12. Definition of Done Checklist

Every milestone is not done until it passes this checklist:

### Code quality
- [ ] No new `TODO` / `FIXME` comments without a linked issue
- [ ] All new functions have docstrings
- [ ] Type hints on all new public functions
- [ ] New features have at least one integration test

### Windows UX
- [ ] Tested at 100%, 125%, 150% DPI
- [ ] No hardcoded paths — all paths via `pathlib.Path` and config
- [ ] Tested on a machine with no GPU (CPU-only fallback)
- [ ] Keyboard shortcuts work from all tabs
- [ ] Installer creates/removes Start Menu shortcut cleanly

### Reliability
- [ ] Tested with mid-transcription `Ctrl+C` — job resumes cleanly
- [ ] Tested with a full disk — error message shown, no crash
- [ ] Tested with a missing/deleted input file — error handled gracefully
- [ ] Logging produces readable output at `INFO` level

### Performance
- [ ] RTF ≤ 0.15 on a mid-range CPU-only laptop for `balanced` profile (60-min file in ≤ 9 min)
- [ ] Peak RAM ≤ 2 GB for `laptop_safe` profile on a 60-min file
- [ ] No memory leak detected in a 3-hour continuous realtime session

### Premium features (Phase 4+)
- [ ] All core features work with zero account interaction
- [ ] Premium badge visible but non-intrusive
- [ ] Grace period logic tested (offline after license check)
- [ ] No API keys stored in plain `config.yaml` — keychain only

---

*End of Insightron Expanded Product Roadmap*
