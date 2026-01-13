# Root Directory Organization

## 📁 Clean Root Structure

The root directory now contains only **essential files** for running and configuring Insightron.

### ✅ Files in Root (Keep These)

```
Insightron/
├── insightron.py          # Main entry point (backward compatible)
├── config.yaml            # User configuration file
├── pytest.ini            # Test configuration
├── user_settings.json     # User preferences (auto-generated)
├── .gitignore            # Git ignore rules
└── README.md             # Main documentation (moved to docs/)
```

### 📂 Organized Folders

```
Insightron/
├── src/                   # Main source code
├── docs/                  # All documentation
│   ├── README.md
│   ├── STRUCTURE.md
│   ├── QUICK_START.md
│   ├── RESTRUCTURE_SUMMARY.md
│   ├── BATCH_PROCESSING.md
│   ├── CHANGELOG.md
│   └── PERFORMANCE_UPGRADE.md
├── benchmarks/            # Benchmarking tools
│   ├── benchmark_insightron.py
│   ├── benchmark_results.json
│   └── benchmark_test.wav
├── tests/                 # Test suite
├── setup/                 # Installation scripts
├── scripts/               # Utility scripts
└── [legacy folders]       # Old structure (can be removed)
```

## 📋 File Organization Rules

### Root Directory
**Only keep:**
- Entry point scripts (`insightron.py`)
- Configuration files (`config.yaml`, `pytest.ini`)
- User data files (`user_settings.json`)
- Essential documentation (`README.md` - if needed)

### Documentation → `docs/`
- All `.md` files go here
- README, CHANGELOG, guides, etc.

### Benchmarks → `benchmarks/`
- Benchmark scripts
- Benchmark results
- Test audio files for benchmarking

### Source Code → `src/`
- All application code
- Organized by module type

### Tests → `tests/`
- All test files
- Test configuration

### Setup → `setup/`
- Installation scripts
- Requirements files

### Scripts → `scripts/`
- Utility scripts
- Development tools

## 🗑️ Legacy Folders (Can Be Removed)

After verifying the new structure works:
- `core/` → Replaced by `src/core/`
- `gui/` → Replaced by `src/app/gui/` and `src/ui/`
- `realtime/` → Replaced by `src/services/realtime/`
- `transcription/` → Replaced by `src/services/transcription/` and `src/services/batch/`

## 🎯 Result

**Before**: 20+ files in root  
**After**: ~5 essential files in root

Clean, organized, professional! ✨
