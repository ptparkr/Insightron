"""
Script to update all import statements after code reorganization.
This script will update imports in all Python files to use the new module paths.
"""

import re
from pathlib import Path

# Root directory
root = Path(r"d:\Developer Mode\Insightron")

# Import mappings
import_mappings = [
    # Core modules
    (r'from model_manager import', 'from core.model_manager import'),
    (r'from config import', 'from core.config import'),
    (r'from utils import', 'from core.utils import'),
    (r'from settings_manager import', 'from core.settings_manager import'),
    
    # Transcription modules
    (r'from transcribe import', 'from transcription.transcribe import'),
    (r'from batch_processor import', 'from transcription.batch_processor import'),
    (r'from text_formatter import', 'from transcription.text_formatter import'),
    
    # Real-time module
    (r'from realtime_transcriber import', 'from realtime.realtime_transcriber import'),
    
    # GUI module
    (r'from gui import', 'from gui.gui import'),
]

def update_file_imports(file_path):
    """Update imports in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Apply all mappings
        for old_pattern, new_import in import_mappings:
            content = re.sub(old_pattern, new_import, content)
        
        # Only write if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"[OK] Updated: {file_path.relative_to(root)}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Error updating {file_path}: {e}")
        return False

# Files to update
files_to_update = [
    # Transcription module
    root / "transcription" / "batch_processor.py",
    root / "transcription" / "text_formatter.py",
    
    # Real-time module
    root / "realtime" / "realtime_transcriber.py",
    
    # GUI module
    root / "gui" / "gui.py",
    
    # Core modules (in case they import each other)
    root / "core" / "model_manager.py",
    
    # Test files
    root / "tests" / "test_batch_integration.py",
    root / "tests" / "test_config.py",
    root / "tests" / "test_formatting.py",
    root / "tests" / "test_model_manager.py",
    root / "tests" / "test_text_formatter_performance.py",
    root / "tests" / "test_transcribe.py",
    
    # Setup files
    root / "setup" / "setup.py",
    
    # Benchmark
    root / "benchmark_insightron.py",
]

# Run updates
print("Updating import statements across all files...")
print("=" * 60)

updated_count = 0
for file_path in files_to_update:
    if file_path.exists():
        if update_file_imports(file_path):
            updated_count += 1
    else:
        print(f"⚠ File not found: {file_path.relative_to(root)}")

print("=" * 60)
print(f"\nCompleted! Updated {updated_count} files.")
