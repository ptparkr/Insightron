## Note-shaping roles (Insightron)

This document codifies the boundary between **literal ground truth**, **mechanical formatting**, and **semantic restoration** so you always know which knob to turn.

### First principles

- **Segments are truth**: everything starts as timestamped ASR segments.
- **Ground truth is literal**: the raw transcription preserves all verbal artifacts.
- **Single-pass refinement is light**: obvious ASR fixes only, no rewriting.
- **Formatting is typesetting**: it improves readability without changing meaning.
- **Restoration is repair**: it fixes obvious ASR artifacts with strict anti-hallucination constraints.

### BaseTranscriber = camera (ground truth)

**Location**: `insightron/services/base_transcriber.py`

**Allowed**:

- Raw literal transcription with word timestamps
- Resource validation before transcription
- Preserving hesitations, repetitions, and uncertainty

**Not allowed**:

- Any cleanup, formatting, or guessing
- Modifying the literal output in any way

### TranscriptionEngine = single-pass brain (light refinement)

**Location**: `insightron/services/transcription/transcription_engine.py`

**Allowed**:

- Resolving obvious ASR artifacts (infinite repeats, boundary whitespace)
- Adjusting timestamps by chunk offset
- Filtering extreme low-confidence segments

**Not allowed**:

- Looking ahead multiple times
- Rewriting stylistically
- Summarizing

### TextFormatter = typesetter (deterministic)

**Location**: `insightron/services/transcription/text_formatter.py`

**Allowed**:

- Spacing, casing, punctuation normalization
- Paragraph/bullet layout via FormattingViews
- Conservative filler removal (only strict non-lexical fillers)
- Safe LaTeX substitutions when unambiguous (mode-dependent)
- Per-view sentence limits and break sensitivity

**Not allowed**:

- Adding new information
- Rewriting ideas for style
- "Summarizing" or compressing meaning

### LLM restoration = repair (semantic, constrained)

**Location**: `insightron/services/transcription/llm_provider.py` (used by `MultiPassTranscriber.pass2_restore`)

**Allowed**:

- Fixing obvious ASR mis-hearings using **local context**
- Stitching chunk boundaries when a sentence is cut mid-thought
- Flagging uncertainty (must not guess silently)
- Using prompt profiles to bias restoration style

**Not allowed**:

- Hallucinating missing facts
- Introducing headings, bullet formatting, or Markdown structure (leave this to `TextFormatter`)

### ResultHandler = contract (artifact output)

**Location**: `insightron/services/transcription/result_handler.py`

**Responsibility**:

- Choose the formatting view (style) and generate the final note artifacts
- Resolve formatting profile from config and CLI overrides
- Generate dashboard or classic reports via `MarkdownRenderer`
- Integrate diarization results and speaker attribution
- Persist artifacts deterministically (Markdown + processed audio)
- Surface quality/risk, restoration flags, and metrics so you can iterate safely
