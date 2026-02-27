## Note-shaping roles (Insightron)

This document codifies the boundary between **mechanical formatting** and **semantic restoration** so you always know which knob to turn.

### First principles

- **Segments are truth**: everything starts as timestamped ASR segments.
- **Formatting is typesetting**: it improves readability without changing meaning.
- **Restoration is repair**: it fixes obvious ASR artifacts with strict anti-hallucination constraints.

### TextFormatter = typesetter (deterministic)

**Location**: `insightron/services/transcription/text_formatter.py`

**Allowed**:

- Spacing, casing, punctuation normalization
- Paragraph/bullet layout
- Conservative filler removal (only strict non-lexical fillers)
- Safe LaTeX substitutions when unambiguous (profile-dependent)

**Not allowed**:

- Adding new information
- Rewriting ideas for style
- “Summarizing” or compressing meaning

### LLM restoration = repair (semantic, constrained)

**Location**: `insightron/services/transcription/llm_provider.py` (used by `MultiPassTranscriber.pass2_restore`)

**Allowed**:

- Fixing obvious ASR mis-hearings using **local context**
- Stitching chunk boundaries when a sentence is cut mid-thought
- Flagging uncertainty (must not guess silently)

**Not allowed**:

- Hallucinating missing facts
- Introducing headings, bullet formatting, or Markdown structure (leave this to `TextFormatter`)

### ResultHandler = contract (artifact output)

**Location**: `insightron/services/transcription/result_handler.py`

**Responsibility**:

- Choose the formatting view (style) and generate the final note artifacts
- Persist artifacts deterministically (Markdown + processed audio)
- Surface quality/risk and restoration flags so you can iterate safely

