# Root Directory Organization

## 📁 Clean Root Structure

The root directory now contains only **essential files** for running and configuring Insightron.

### ✅ Files in Root (Keep These)

```
Insightron/
├── pyproject.toml         # Project metadata and dependencies
├── config.yaml            # User configuration file
├── insightron.py          # Legacy GUI entry point (still supported)
├── cli.py                 # Legacy CLI entry point (still supported)
├── pytest.ini             # Test configuration
├── user_settings.json     # User preferences (auto-generated)
├── .gitignore             # Git ignore rules
└── README.md              # Top-level project summary
```

### 📂 Organized Folders

```
Insightron/
├── insightron/            # Main source code package
├── docs/                  # All documentation
│   ├── README.md
│   ├── STRUCTURE.md
│   ├── QUICK_START.md
│   ├── RESTRUCTURE_SUMMARY.md
│   ├── BATCH_PROCESSING.md
│   ├── CHANGELOG.md
│   └── PERFORMANCE_UPGRADE.md
├── tests/                 # Test suite (including benchmarks/)
│   └── benchmarks/
│       ├── benchmark_insightron.py
│       └── benchmark_test.wav
├── automation/            # Installation + utility scripts
│   ├── setup/             # Installers (requirements, platform installers)
│   └── scripts/           # Utility / maintenance scripts
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

### Benchmarks → `tests/benchmarks/`
- Benchmark scripts
- Benchmark results
- Test audio files for benchmarking

### Source Code → `insightron/`
- All application code
- Organized by module type

### Tests → `tests/`
- All test files
- Test configuration

### Setup → `automation/setup/`
- Installation scripts
- Requirements files

### Scripts → `automation/scripts/`
- Utility scripts
- Development tools

## 🗑️ Legacy Folders (Can Be Removed)

After verifying the new structure works:
- `core/` → Replaced by `insightron/core/`
- `gui/` → Replaced by `insightron/app/gui/` and `insightron/ui/`
- `realtime/` → Replaced by `insightron/services/realtime/`
- `transcription/` → Replaced by `insightron/services/transcription/` and `insightron/services/batch/`

## 🎯 Result

**Before**: 20+ files in root  
**After**: ~5 essential files in root

Clean, organized, professional! ✨
