#!/usr/bin/env python3
"""
Test script for Multi-Pass LLM Transcription
Tests the LLM text restoration (Pass 2) with Qwen2.5-3B-Instruct
"""
import pytest
import sys
import os
from pathlib import Path
import yaml
import logging
import time

# Add the project root to sys.path (parent of tests folder)
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_llm_restoration():
    """Test LLM provider text restoration independently"""
    if os.getenv("INSIGHTRON_RUN_LLM_TESTS") != "1":
        pytest.skip("Set INSIGHTRON_RUN_LLM_TESTS=1 to run local LLM tests.")

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)

    # Load config
    config_path = root_dir / "config.yaml"
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
            print("ERROR: LLM provider dependencies not available!")
            print("Install with: pip install transformers torch accelerate bitsandbytes")
            return False
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
        
        if result.success:
            print(f"STATUS: SUCCESS")
            print(f"TIME: {elapsed:.2f}s")
            print(f"TOKENS: {result.tokens_used}")
            print(f"MODEL: {result.model_name}")
            print(f"\nORIGINAL:\n  {test_text}")
            print(f"\nRESTORED:\n  {result.restored_text}")
            print("-" * 50)
            return True
        else:
            print(f"STATUS: FAILED")
            print(f"ERROR: {result.error}")
            print("-" * 50)
            return False
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_multipass():
    """Test full multi-pass transcription with sample audio"""
    if os.getenv("INSIGHTRON_RUN_LLM_TESTS") != "1":
        pytest.skip("Set INSIGHTRON_RUN_LLM_TESTS=1 to run local LLM tests.")

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("\n" + "="*60)
    print(" FULL MULTI-PASS TRANSCRIPTION TEST")
    print("="*60)
    
    audio_path = root_dir / "tests" / "benchmarks" / "benchmark_test.wav"
    
    if not audio_path.exists():
        print(f"ERROR: Sample audio not found at {audio_path}")
        return False
    
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
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Multi-Pass LLM Transcription")
    parser.add_argument("--full", action="store_true", help="Run full transcription test")
    args = parser.parse_args()
    
    if args.full:
        success = test_full_multipass()
    else:
        success = test_llm_restoration()
    
    sys.exit(0 if success else 1)
    