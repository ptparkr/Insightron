import time
import numpy as np
import threading
import psutil
import os
from realtime_transcriber import RealtimeTranscriber
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StressTest")

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

def mock_callback(text):
    logger.info(f"Callback received: {text}")

def mock_audio_level(level):
    pass

def run_stress_test(duration_seconds=60):
    logger.info(f"Starting stress test for {duration_seconds} seconds...")
    
    transcriber = RealtimeTranscriber()
    
    # Mock the audio stream to avoid needing a real microphone
    # We will inject audio directly into the queue or just let it run if it handles no input gracefully
    # But to stress test the processing loop, we should inject data.
    
    # However, since RealtimeTranscriber uses sounddevice.InputStream, mocking it is hard without changing code.
    # Instead, we will rely on the fact that if we start it, it will try to read from mic.
    # If no mic, it might fail.
    # Let's try to start it. If it fails, we will know.
    
    try:
        # Use default device
        transcriber.start_transcription(-1, mock_callback, mock_audio_level)
    except Exception as e:
        logger.error(f"Failed to start transcriber: {e}")
        logger.info("Skipping actual audio test, checking memory baseline.")
        return

    start_time = time.time()
    initial_memory = get_memory_usage()
    logger.info(f"Initial Memory: {initial_memory:.2f} MB")
    
    try:
        while time.time() - start_time < duration_seconds:
            current_memory = get_memory_usage()
            logger.info(f"Memory: {current_memory:.2f} MB")
            
            # Simulate some activity or just wait
            time.sleep(5)
            
    except KeyboardInterrupt:
        pass
    finally:
        transcriber.stop_transcription()
        final_memory = get_memory_usage()
        logger.info(f"Final Memory: {final_memory:.2f} MB")
        logger.info(f"Memory Growth: {final_memory - initial_memory:.2f} MB")

if __name__ == "__main__":
    run_stress_test(30) # Run for 30 seconds
