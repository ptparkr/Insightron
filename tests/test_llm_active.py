"""
Opt-in integration tests for Multi-Pass LLM transcription.

These tests can be expensive (GPU/CPU time) and may require local model caches
or additional optional dependencies. They are marked `llm` and skipped by
default unless explicitly enabled.
"""

import logging
import os
import sys
import time
from pathlib import Path

import pytest
import yaml

# Add the project root to sys.path (parent of tests folder)
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

pytestmark = [pytest.mark.llm, pytest.mark.slow]


def _llm_opt_in(pytestconfig: pytest.Config) -> bool:
    return bool(pytestconfig.getoption("--run-llm")) or os.getenv("INSIGHTRON_RUN_LLM_TESTS") == "1"


def test_llm_restoration(pytestconfig: pytest.Config):
    """Test LLM provider text restoration independently"""
    if not _llm_opt_in(pytestconfig):
        pytest.skip("Use --run-llm or set INSIGHTRON_RUN_LLM_TESTS=1 to run LLM tests.")

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)

    # Load config
    config_path = root_dir / "config.yaml"
    if not config_path.exists():
        pytest.skip("config.yaml not found at project root; LLM tests require local config.")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    multi_pass_config = config.get('multi_pass', {})
    local_config = multi_pass_config.get('contextual_restoration', {}).get('local_model', {})
    
    print("\n" + "="*60)
    print(" MULTI-PASS LLM TRANSCRIPTION TEST")
    print("="*60)
    print(f"\nModel: {local_config.get('model_name', 'Not configured')}")
    print(f"Device: {local_config.get('device', 'auto')}")
    print(f"Quantization: {local_config.get('quantization', '4bit')}")
    print("="*60)
    
    try:
        from insightron.services.transcription.llm_provider import LLMProviderFactory

        print("\n[1/4] Creating LLM provider...")
        provider = LLMProviderFactory.create_from_config(multi_pass_config)

        print("[2/4] Checking provider availability...")
        if not provider.is_available():
            pytest.skip(
                "LLM provider dependencies not available. Install with: "
                "pip install -e .[llm] (or install transformers/torch/etc)."
            )
        print("      Dependencies verified!")
        
        # Test text that needs restoration
        test_text = "hello i am here at the office today and i want to see if this thing is working or not because it is very important for the meeting tomorrow we need to discuss the budget"
        
        print(f"\n[3/4] Testing text restoration...")
        print(f"      Input: '{test_text[:60]}...'")
        print("      (Loading model, this may take a minute on first run...)")
        
        start_time = time.time()
        result = provider.restore_text(test_text)
        elapsed = time.time() - start_time
        
        print(f"\n[4/4] Results:")
        print("-" * 50)
        
        assert result.success, f"LLM restoration failed: {result.error}"
        assert isinstance(result.restored_text, str) and result.restored_text.strip()

        print(f"STATUS: SUCCESS")
        print(f"TIME: {elapsed:.2f}s")
        print(f"TOKENS: {result.tokens_used}")
        print(f"MODEL: {result.model_name}")
        print(f"\nORIGINAL:\n  {test_text}")
        print(f"\nRESTORED:\n  {result.restored_text}")
        print("-" * 50)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

def test_full_multipass(pytestconfig: pytest.Config):
    """Test full multi-pass transcription with sample audio"""
    if not _llm_opt_in(pytestconfig):
        pytest.skip("Use --run-llm or set INSIGHTRON_RUN_LLM_TESTS=1 to run LLM tests.")

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("\n" + "="*60)
    print(" FULL MULTI-PASS TRANSCRIPTION TEST")
    print("="*60)
    
    audio_path = root_dir / "tests" / "benchmarks" / "benchmark_test.wav"
    
    if not audio_path.exists():
        pytest.skip(f"Sample audio not found at {audio_path}")
    
    print(f"\nAudio file: {audio_path}")
    
    try:
        from insightron.services.transcription.multi_pass_transcriber import MultiPassTranscriber
        
        print("\n[1/3] Initializing MultiPassTranscriber...")
        transcriber = MultiPassTranscriber()
        
        print("[2/3] Running 3-pass transcription pipeline...")
        print("      (This will take some time...)")
        
        def progress_cb(msg):
            print(f"      {msg}")
        
        result = transcriber.transcribe_multipass(str(audio_path), progress_callback=progress_cb)
        
        print(f"\n[3/3] Results:")
        print("-" * 50)
        print(f"Pass 1 (Raw):      '{result.pass1_raw_text[:100]}...'")
        print(f"Pass 2 (Restored): '{result.pass2_restored_text[:100]}...'")
        print(f"Pass 3 (Final):    '{result.pass3_final_text[:100]}...'")
        print(f"\nProcessing Times:")
        for key, val in result.processing_times.items():
            print(f"  {key}: {val:.2f}s")
        print("-" * 50)
        assert result.pass1_raw_text is not None
        assert result.pass3_final_text is not None
        
    except Exception as e:
        raise

if __name__ == "__main__":
    raise SystemExit("Run via pytest (these are tests, not a CLI script).")
    