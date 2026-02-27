import os
import sys
import shutil
import unittest
import numpy as np
import soundfile as sf
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from insightron.services.batch.batch_processor import batch_transcribe_files
from insightron.core.config import TRANSCRIPTION_FOLDER


@pytest.mark.integration
@pytest.mark.batch
class TestBatchIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_audio_batch")
        self.test_dir.mkdir(exist_ok=True)
        self.audio_files = []
        
        # Create 3 dummy audio files (1 second of silence)
        sr = 16000
        data = np.zeros(sr)
        
        for i in range(3):
            file_path = self.test_dir / f"test_audio_{i}.wav"
            sf.write(file_path, data, sr)
            self.audio_files.append(str(file_path))
            
    def tearDown(self):
        # Clean up audio files
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            
        # Clean up transcription files
        for i in range(3):
            md_file = TRANSCRIPTION_FOLDER / f"test_audio_{i}.md"
            if md_file.exists():
                md_file.unlink()

    def test_batch_processing(self):
        """
        Integration-style test of the batch orchestration layer.

        We **mock the per-file transcription** to keep this test reliable on
        CPU-only machines and to avoid downloading/initializing models.
        """
        from unittest.mock import patch

        test_dir = self.test_dir

        def _fake_transcribe_single_file_threaded(_batch_self, audio_file: str, formatting_style: str):
            out_path = test_dir / (Path(audio_file).stem + ".md")
            out_path.write_text("# dummy transcription\n", encoding="utf-8")
            return {
                "output_path": str(out_path),
                "duration": 1.0,
                "language": "en",
                "processing_time": 0.0,
                "status": "success",
            }

        with patch(
            "insightron.services.batch.batch_processor.BatchTranscriber._transcribe_single_file_threaded",
            new=_fake_transcribe_single_file_threaded,
        ):
            results = batch_transcribe_files(
                audio_files=self.audio_files,
                model_size="tiny",
                language="en",
                use_multiprocessing=False,
                max_workers=2,
            )
        
        # Manually move expected outputs to test_dir for verification logic below if they were written there
        # Actually simplest is to verify files in self.test_dir since we redirected output there.
        
        # Verify results
        self.assertEqual(results['total_files'], 3)
        self.assertEqual(results['completed'], 3)
        self.assertEqual(len(results['successful']), 3)
        self.assertEqual(len(results['failed']), 0)
        
        for success in results['successful']:
            # The output path in result should be valid
            self.assertTrue(os.path.exists(success['output']))

if __name__ == "__main__":
    unittest.main()
