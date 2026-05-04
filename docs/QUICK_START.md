# Insightron v4.1.1 - Quick Start Guide

## 🚀 What's New in v4.1.1

Insightron v4.1.1 introduces the **Minimal Architecture** with refined single-phase engine, improved quality metrics, and streamlined pipeline.

### Key Improvements

✅ **Single-Phase Engine** - Layered pipeline: Ground Truth → Brain → Typesetter → Contract
✅ **Dashboard Reports** - Rich quality metrics, speaker timelines, low-confidence flags
✅ **Audio Preprocessing** - Noise reduction, LUFS normalization, pre-emphasis, trimming
✅ **Speaker Diarization** - pyannote-powered speaker identification
✅ **FormattingViews** - Named views (thinking_session, meeting_notes, study_notes) with LaTeX
✅ **Typed Contracts** - Frozen dataclasses for type-safe data flow
✅ **v2 LLM Restoration** - Prompt profiles, JSON response contract, quality flags
✅ **Dynamic Chunking** - Smart audio processing that adapts to hardware capabilities

---

## 📊 Performance Gains

**Your System:** 12 cores, 15.73GB RAM

- **Single File**: Standard performance with adaptive segment merging
- **Batch (Thread Pool)**: 2-3x faster for multiple files with resume capability
- **Batch (Process Pool)**: Up to 2x faster for CPU-intensive text processing
- **Quality Metrics**: Enhanced accuracy with weighted confidence scoring
- **Memory Safety**: Automatic OOM prevention during large batch operations

---

## 🎯 Quick Start - Batch Processing

### Method 1: Command Line (Recommended)

```bash
# Batch process multiple files (auto-detects optimal workers)
python cli.py audio1.mp3 audio2.mp3 audio3.mp3

# Batch process all MP3 files in directory
python cli.py *.mp3 -b

# Use 8 workers with medium model
python cli.py *.wav -b -w 8 -m medium

# Use process pool for better CPU utilization
python cli.py *.mp3 -b --use-processes

# Batch with 4 workers and custom settings
python cli.py audio*.mp3 -b -w 4 -m medium -l en

# Batch with resume capability (automatically resumes if interrupted)
# State is saved in .batch_state/ directory
python cli.py *.mp3 -b --enable-resume

# Create bulleted lists from speech
python cli.py meeting_notes.wav -f bullets
```

### Method 2: Python API

```python
from insightron.services.batch.batch_processor import batch_transcribe_files

# Simple batch transcription
results = batch_transcribe_files(
    ["audio1.mp3", "audio2.mp3", "audio3.mp3"],
    model_size="medium",
    max_workers=4  # Uses 4 parallel workers
)

print(f"Completed: {results['completed']}/{results['total_files']}")
print(f"Throughput: {results['statistics']['throughput']:.2f} files/sec")
```

### Method 3: Advanced API with Progress

```python
from insightron.services.batch.batch_processor import BatchTranscriber

def progress_callback(completed, total, filename):
    print(f"[{completed}/{total}] Processing: {filename}")

# Create batch transcriber
transcriber = BatchTranscriber(
    model_size="medium",
    max_workers=8,
    use_multiprocessing=False  # Use thread pool (default)
)

# Transcribe batch
results = transcriber.transcribe_batch(
    audio_files,
    progress_callback=progress_callback,
    formatting_style="auto"
)

# Check results
for success in results['successful']:
    print(f"✓ {success['file']} -> {success['output']}")
```

---

## 🔧 Configuration Options

## Single-Phase Engine (Dashboard + Preprocessing + Diarization)

### Dashboard report (recommended)

```yaml
report:
  style: "dashboard"   # or "classic"
```

### Audio preprocessing

```yaml
audio_preprocess:
  enabled: true
  noise_reduction:
    enabled: true
  loudness:
    enabled: true
    target_lufs: -23.0
  pre_emphasis:
    enabled: true
  trim:
    enabled: true
    top_db: 20
```

### Speaker diarization (optional)

```yaml
diarization:
  enabled: true
  pipeline_id: "pyannote/speaker-diarization@2.1"
  hf_token: ""   # or set HF_TOKEN env var
```

If you use diarization, you must accept the Hugging Face model conditions and provide an access token.

### Worker Count

| Setting | Description | Best For |
|---------|-------------|----------|
| `None` (auto) | Auto-detects based on CPU cores | Most cases |
| `4` | Use 4 workers | Balanced performance |
| `8` | Use 8 workers | High-end systems |
| `cpu_count * 2` | Maximum for thread pool | I/O-bound tasks |

### Thread Pool vs Process Pool

**Thread Pool (default):**
- ✅ Better for I/O-bound tasks (file reading, transcription)
- ✅ Lower overhead
- ✅ Recommended for most users
- Command: `python cli.py *.mp3 -b`

**Process Pool:**
- ✅ Better for CPU-bound tasks (text formatting)
- ✅ Bypasses Python's GIL
- ✅ True parallel execution
- Command: `python cli.py *.mp3 -b --use-processes`

---

## 📈 Benchmark Results

Run the benchmark to see performance on your system:

```bash
python tests/benchmarks/benchmark_insightron.py
```

**Sample Output:**
```
🔄 Concurrent Operations:
  1_threads: 246.67 ops/sec
  2_threads: 251.62 ops/sec
  4_threads: 255.82 ops/sec
  8_threads: 213.35 ops/sec

💡 OPTIMIZATION RECOMMENDATIONS:
  1. Limited threading speedup (1.07x). ✅ FIXED: Use batch_processor.py with ProcessPoolExecutor for CPU-bound tasks.
  2. System has 12 cores. Use batch_processor.py to leverage parallel processing.
```

---

## 💡 Usage Recommendations

### For Your 12-Core System

1. **Small Batch (2-5 files):**
   ```bash
   python cli.py audio1.mp3 audio2.mp3 audio3.mp3
   ```

2. **Medium Batch (5-20 files):**
   ```bash
   python cli.py *.mp3 -b -w 8
   ```

3. **Large Batch (20+ files):**
   ```bash
   python cli.py *.mp3 -b -w 12 --use-processes
   ```

4. **Maximum Performance:**
   ```bash
   python cli.py *.mp3 -b -w 12 --use-processes -m tiny
   ```

---

## 🎨 Examples

### Example 1: Transcribe All Recordings in a Folder

```bash
cd /path/to/recordings
python cli.py *.mp3 -b -w 8 -m medium
```

### Example 2: Batch with Custom Output

```python
from insightron.services.batch.batch_processor import batch_transcribe_files
from pathlib import Path

# Get all MP3 files
audio_files = list(Path("recordings").glob("*.mp3"))

# Batch transcribe
results = batch_transcribe_files(
    [str(f) for f in audio_files],
    model_size="medium",
    max_workers=8
)

# Print statistics
print(f"Success rate: {results['statistics']['success_rate']:.1f}%")
print(f"Throughput: {results['statistics']['throughput']:.2f} files/sec")
```

### Example 3: Progress Bar Integration

```python
from insightron.services.batch.batch_processor import batch_transcribe_files
from tqdm import tqdm

audio_files = ["audio1.mp3", "audio2.mp3", "audio3.mp3"]

pbar = tqdm(total=len(audio_files), desc="Transcribing")

def progress_callback(completed, total, filename):
    pbar.update(1)
    pbar.set_postfix({"file": filename})

results = batch_transcribe_files(
    audio_files,
    max_workers=4,
    progress_callback=progress_callback
)

pbar.close()
```

---

## 🐛 Troubleshooting

### Issue: "Can't pickle local object"

**Solution:** This is expected when using `--use-processes` with nested functions. The `batch_processor.py` handles this correctly. If you see this error, use thread pool instead:

```bash
python cli.py *.mp3 -b  # Without --use-processes
```

### Issue: Performance not improving

**Checklist:**
1. ✅ Check CPU usage - if already at 100%, more workers won't help
2. ✅ For transcription (I/O-bound), use thread pool
3. ✅ For text formatting (CPU-bound), use process pool
4. ✅ Run benchmark to identify bottlenecks: `python -m insightron.tests.benchmarks.benchmark_insightron`

### Issue: Out of memory

**Solution:** Reduce number of workers:

```bash
python cli.py *.mp3 -b -w 4  # Use fewer workers
```

---

## 📚 Additional Resources

- **[BATCH_PROCESSING.md](BATCH_PROCESSING.md)** - Comprehensive documentation
- **[batch_processor.py](../insightron/services/batch/batch_processor.py)** - Source code
- **[benchmark_insightron.py](../tests/benchmarks/benchmark_insightron.py)** - Performance testing

---

## ✅ Summary

**Before (v4.0.0):**
- Everything in v4.0.0 (single-phase engine, dashboard, audio preprocessing, diarization)

**After (v4.1.1):**
- ✅ **Everything in v4.0.0 plus:**
- ✅ **Minimal Architecture**: Refined pipeline with optimized data flow
- ✅ **Enhanced Quality Metrics**: Improved confidence scoring and degradation detection
- ✅ **Better Memory Efficiency**: Optimized resource management for large batches

**Get Started:**
```bash
# Try it now!
python cli.py *.mp3 -b --enable-resume
```

Enjoy smarter transcriptions! 🚀
