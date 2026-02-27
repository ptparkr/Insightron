# Legacy Structure - Deprecated

## ⚠️ Important Notice

The following folders are **legacy** and have been replaced by the new structure under the `insightron/` package:

- `core/` → Now in `insightron/core/`
- `gui/` → Now in `insightron/app/gui/` and `insightron/ui/components/`
- `realtime/` → Now in `insightron/services/realtime/`
- `transcription/` → Now in `insightron/services/transcription/` and `insightron/services/batch/`

## Migration Status

✅ **New structure is active** under the `insightron/` package
⚠️ **Old folders kept for reference** - can be removed after verification

## What to Do

1. **Verify** the new structure works: `python -m insightron.app.main`
2. **Test** all functionality
3. **Remove** old folders once confirmed working:
   - `core/`
   - `gui/`
   - `realtime/`
   - `transcription/`

## New Entry Points

- **Console script (recommended)**: `insightron`
- **Main module**: `python -m insightron.app.main`
- **CLI module**: `python -m insightron.app.cli.cli`
- **Legacy wrappers**: `insightron.py` and `cli.py` in the project root
