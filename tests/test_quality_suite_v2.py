#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import yaml
import logging
import json
import pytest

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

pytestmark = [pytest.mark.llm, pytest.mark.slow]


def test_quality_suite_v2(pytestconfig: pytest.Config):
    if not bool(pytestconfig.getoption("--run-llm")) and os.getenv("INSIGHTRON_RUN_LLM_TESTS") != "1":
        pytest.skip("Use --run-llm or set INSIGHTRON_RUN_LLM_TESTS=1 to run LLM tests.")

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)

    # Load config
    config_path = root_dir / "config.yaml"
    if not config_path.exists():
        pytest.skip("config.yaml not found at project root; LLM tests require local config.")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    multi_pass_config = config.get('multi_pass', {})
    
    print("\n" + "="*60)
    print(" TRANSCRIPTION QUALITY SUITE V2 TEST")
    print("="*60)

    try:
        from insightron.services.transcription.llm_provider import LLMProviderFactory
        
        print("\n[1/3] Creating LLM provider (v2)...")
        provider = LLMProviderFactory.create_from_config(multi_pass_config)
        
        # Mock inputs for 5-stage testing
        prev_clean = "We discussed the first law of thermodynamics."
        raw_chunk = "um so the next part is basically ten power minus three and and we need to solve for x minus b plus minus root"
        next_raw = "of b squared minus four a c divided by two a"
        
        print(f"\n[2/3] Running v2 restoration...")
        print(f"      Prev Clean: '{prev_clean}'")
        print(f"      Raw Chunk:  '{raw_chunk}'")
        print(f"      Next Raw:   '{next_raw}'")
        print("      (This may take a minute on CPU...)")
        
        # Run in offline mode since we know model is cached
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        
        result = provider.restore_text(raw_chunk, prev_clean, next_raw)
        
        print(f"\n[3/3] Results:")
        print("-" * 50)
        
        assert result.success, f"Quality suite failed: {result.error}"
        assert isinstance(result.restored_text, str) and result.restored_text.strip()

        print(f"STATUS: SUCCESS")
        print(f"FLAGS: {result.flags}")
        print(f"STITCHED: {result.stitched}")
        print(f"\nRESTORED TEXT:\n{result.restored_text}")
        print("-" * 50)
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    raise SystemExit("Run via pytest (this is an opt-in test).")
    sys.exit(0 if success else 1)
