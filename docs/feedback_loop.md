## Compounding feedback loop (text + LLM)

The goal is to make improvements **small, testable, and cumulative**.

### Weekly loop (15 minutes)

- Pick 3 recent transcripts you actually used.
- For each, write down **one** friction point:
  - “Paragraph breaks feel wrong here”
  - “Bullets should have started at X”
  - “The model ‘fixed’ a technical term incorrectly”
  - “The note should feel more like meeting notes”

### Translate friction → micro-change

Map each item to exactly one change:

- **Paragraph/bullet issue** → update `TextFormatter._indicates_long_pause` starter phrases or FormattingView sentence limits.
- **Wrong term repair** → tighten `llm_provider.py` prompt profile instructions (bias toward "leave unchanged + flag").
- **Style mismatch** → switch `post_processing.formatting_profile` or `multi_pass.contextual_restoration.prompt_profile` (see `thinking_session`, `meeting_notes`, `study_notes`).

### A/B test on one file

Use one representative audio file and run:

- `--format thinking_session` vs `--format meeting_notes`
- `--profile balanced` vs `--profile deep`

Keep the output that you *actually prefer to reread*, then make it the default in `config.yaml`.

### Artifact trail (so it compounds)

- Batch runs produce `*_summary.json` in your transcription folder (easy to analyze later).
- Multi-pass restoration flags are surfaced in Markdown under “Restoration Notes” when present.

