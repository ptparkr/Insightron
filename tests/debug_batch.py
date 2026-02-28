
import sys
import os
import shutil
import numpy as np
import soundfile as sf
from pathlib import Path
from datetime import datetime

# Add project root to python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from insightron.services.batch.batch_processor import batch_transcribe_files
from insightron.core.config import TRANSCRIPTION_FOLDER

def debug_batch():
    test_dir = Path("debug_audio_batch")
    test_dir.mkdir(exist_ok=True)
    audio_files = []
    
    # Create 1 dummy audio file
    sr = 16000
    data = np.zeros(sr)
    file_path = test_dir / "debug_audio_0.wav"
    sf.write(file_path, data, sr)
    audio_files.append(str(file_path))
    
    print("Starting batch transcription...")
    try:
        results = batch_transcribe_files(
            audio_files=audio_files,
            model_size="tiny",
            language="en",
            use_multiprocessing=True,
            max_workers=1
        )
        
        print("\nResults:")
        print(f"Total: {results['total_files']}")
        print(f"Completed: {results['completed']}")
        print(f"Failed Count: {results['failed_count']}")
        
        if results['failed']:
            print("\nFailures:")
            for f in results['failed']:
                print(f"File: {f['file']}")
                print(f"Error: {f['error']}")
                
        if results['successful']:
            print("\nSuccesses:")
            for s in results['successful']:
                print(f"File: {s['file']}")
                print(f"Output: {s['output']}")
                
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    debug_batch()
