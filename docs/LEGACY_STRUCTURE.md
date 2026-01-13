# Legacy Structure - Deprecated

## ⚠️ Important Notice

The following folders are **legacy** and have been replaced by the new structure in `src/`:

- `core/` → Now in `src/core/`
- `gui/` → Now in `src/app/gui/` and `src/ui/components/`
- `realtime/` → Now in `src/services/realtime/`
- `transcription/` → Now in `src/services/transcription/` and `src/services/batch/`

## Migration Status

✅ **New structure is active** in `src/`
⚠️ **Old folders kept for reference** - can be removed after verification

## What to Do

1. **Verify** the new structure works: `python src/app/main.py`
2. **Test** all functionality
3. **Remove** old folders once confirmed working:
   - `core/`
   - `gui/`
   - `realtime/`
   - `transcription/`

## New Entry Points

- **Main**: `src/app/main.py` or `insightron.py` (legacy wrapper)
- **CLI**: `src/app/cli/cli.py`
