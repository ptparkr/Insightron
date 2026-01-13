import collections
import sounddevice as sd
import numpy as np
import threading
import queue
import logging
import time
from typing import Optional, Callable, List, Dict, Any
from core.model_manager import ModelManager
from core.config import (
    REALTIME_BUFFER_SECONDS, 
    REALTIME_SILENCE_THRESHOLD,
    DEFAULT_LANGUAGE,
    get_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeTranscriber:
    """
    Realtime Audio Transcriber using sounddevice and faster-whisper.
    Uses a ring buffer and producer-consumer architecture for smooth transcription.
    """
    
    def __init__(self):
        self.is_running = False
        self.result_callback = None
        self.audio_level_callback = None
        self.stream = None
        
        # Audio parameters
        self.sample_rate = get_config('realtime.sample_rate', 16000)
        self.channels = 1
        self.dtype = 'float32'
        self.block_size = 4096
        
        # Ring Buffer Configuration
        self.buffer_duration = REALTIME_BUFFER_SECONDS
        self.buffer_size = int(self.sample_rate * self.buffer_duration)
        self.ring_buffer = np.zeros(self.buffer_size, dtype=self.dtype)
        self.write_index = 0
        
        # Processing parameters
        self.chunk_duration = get_config('realtime.chunk_duration_seconds', 5)
        self.stride = get_config('realtime.stride_seconds', 1)
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)
        self.stride_samples = int(self.sample_rate * self.stride)
        
        # Silence detection
        self.silence_threshold = REALTIME_SILENCE_THRESHOLD
        self.silence_duration = get_config('realtime.silence_duration', 0.5)
        self.last_speech_time = 0
        
        # Threading
        self.capture_thread = None
        self.process_thread = None
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # State
        self.full_audio_buffer = [] # Keep for saving recording
        self.transcribed_text = ""
        self.language = get_config('transcription.language', DEFAULT_LANGUAGE)
        self.model_size = get_config('model.name', 'medium')  # Default model size
        self.transcribed_segments = []  # Store all transcribed segments
        self.detected_language = None  # Store detected language
        
        # Model Manager
        self.model_manager = ModelManager()

    def get_microphones(self) -> List[Dict[str, any]]:
        """Get list of available microphones."""
        devices = []
        try:
            # Filter for input devices
            all_devices = sd.query_devices()
            for i, dev in enumerate(all_devices):
                if dev['max_input_channels'] > 0:
                    devices.append({
                        'index': i,
                        'name': dev['name'],
                        'host_api': dev['hostapi'],
                        'samplerate': dev['default_samplerate']
                    })
        except Exception as e:
            logger.error(f"Error listing microphones: {e}")
            devices.append({'index': -1, 'name': 'Default Microphone'})
        return devices

    def start_transcription(self, device_index: int, callback: Callable[[str], None], 
                           audio_level_callback: Optional[Callable[[float], None]] = None):
        """Start realtime transcription."""
        if self.is_running:
            return

        self.result_callback = callback
        self.audio_level_callback = audio_level_callback
        self.is_running = True
        self.stop_event.clear()
        
        # Reset buffers
        self.ring_buffer.fill(0)
        self.write_index = 0
        self.full_audio_buffer = []
        self.transcribed_text = ""
        self.transcribed_segments = []
        self.detected_language = None
        self.last_speech_time = time.time()
        
        # Clear queue
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

        # Start threads
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        try:
            self.stream = sd.InputStream(
                device=device_index if device_index >= 0 else None,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.block_size,
                callback=self._audio_callback
            )
            self.stream.start()
            logger.info(f"Started recording on device {device_index}")
        except Exception as e:
            self.is_running = False
            self.stop_event.set()
            logger.error(f"Failed to start stream: {e}")
            raise e

    def stop_transcription(self):
        """Stop realtime transcription."""
        self.is_running = False
        self.stop_event.set()
        
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing stream: {e}")
            self.stream = None
            
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
            self.process_thread = None
            
        logger.info("Stopped transcription")

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice."""
        if status:
            logger.warning(f"Audio status: {status}")
            
        if not self.is_running:
            return

        # 1. Update Audio Level
        rms = np.sqrt(np.mean(indata**2))
        if self.audio_level_callback:
            try:
                # Normalize for UI (0.0 - 1.0)
                level = min(rms / 0.15, 1.0)
                self.audio_level_callback(level)
            except Exception:
                pass

        # 2. Write to Ring Buffer
        # Handle wrapping if needed (though we just overwrite in a circular manner)
        # For simplicity in this version, we'll just push to a queue for the processor 
        # to handle the ring buffer logic safely off the audio thread.
        # BUT, to keep the callback fast, we just copy.
        self.audio_queue.put(indata.copy())
        
        # 3. Store for saving
        self.full_audio_buffer.append(indata.copy())

    def _process_loop(self):
        """Consumer thread: reads audio, updates ring buffer, runs inference."""
        logger.info("Processing thread started")
        
        # Local buffer to accumulate small chunks from callback until we have enough for stride
        accumulated_samples = 0
        
        while not self.stop_event.is_set():
            try:
                # Get data from queue
                try:
                    data = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Update Ring Buffer
                num_samples = len(data)
                
                # Check for buffer overflow/wrap-around
                if self.write_index + num_samples > self.buffer_size:
                    # Wrap around
                    diff = self.buffer_size - self.write_index
                    self.ring_buffer[self.write_index:] = data[:diff, 0] # data is (samples, 1)
                    self.ring_buffer[:num_samples - diff] = data[diff:, 0]
                    self.write_index = num_samples - diff
                else:
                    self.ring_buffer[self.write_index:self.write_index + num_samples] = data[:, 0]
                    self.write_index += num_samples
                
                accumulated_samples += num_samples
                
                # Check if we have enough new data to run inference (stride)
                if accumulated_samples >= self.stride_samples:
                    self._run_inference()
                    accumulated_samples = 0 # Reset stride counter (approximate)
                    
            except Exception as e:
                logger.error(f"Error in process loop: {e}")
                
    def _run_inference(self):
        """Run Whisper inference on the latest chunk from ring buffer."""
        # Extract latest chunk
        # We want the last 'chunk_samples' ending at 'write_index'
        
        if self.write_index >= self.chunk_samples:
            audio_chunk = self.ring_buffer[self.write_index - self.chunk_samples : self.write_index]
        else:
            # Wrap around case: take end of buffer + start of buffer
            part2 = self.ring_buffer[:self.write_index]
            part1 = self.ring_buffer[-(self.chunk_samples - len(part2)):]
            audio_chunk = np.concatenate((part1, part2))
            
        # Check for silence
        rms = np.sqrt(np.mean(audio_chunk**2))
        if rms < self.silence_threshold:
            # Too silent, skip inference to save compute
            return

        try:
            # Transcribe with optimized parameters for real-time
            # Convert 'auto' to None for faster-whisper compatibility
            lang = None if self.language == 'auto' else self.language
            
            # Use optimized real-time parameters: beam_size=1 for speed, but with VAD for quality
            segments, info = self.model_manager.transcribe(
                audio_chunk,
                language=lang,
                beam_size=1,   # Fast for realtime
                best_of=1,     # Single candidate for speed
                temperature=[0.0],  # Deterministic for consistency
                vad_filter=True,
                condition_on_previous_text=False  # Disable for faster inference
            )
            
            # Collect text efficiently
            segment_list = list(segments)
            if not segment_list:
                return
            
            # Optimized text assembly
            text = " ".join(s.text.strip() for s in segment_list if s.text.strip()).strip()
            
            # Track detected language from first inference
            if self.detected_language is None and info:
                self.detected_language = info.language
            
            if text:
                # Store segments for note saving (optimized)
                current_time = time.time()
                for seg in segment_list:
                    self.transcribed_segments.append({
                        'start': seg.start,
                        'end': seg.end,
                        'text': seg.text.strip()
                    })
                
                # Deduplication: Skip if text is very similar to last segment (reduces flicker)
                if self.transcribed_segments:
                    last_text = self.transcribed_segments[-1].get('text', '')
                    # Simple similarity check: if >80% overlap, skip
                    if last_text and len(text) > 0:
                        similarity = len(set(text.lower().split()) & set(last_text.lower().split())) / max(len(text.split()), len(last_text.split()))
                        if similarity > 0.8 and len(text) < len(last_text) * 1.2:
                            return  # Skip duplicate/very similar text
                
                # Send result
                if self.result_callback:
                    self.result_callback(text)
                    
        except Exception as e:
            logger.error(f"Inference error: {e}")

    def save_recording(self, output_path: str):
        """Save the recorded audio to WAV file."""
        import wave
        
        if not self.full_audio_buffer:
            return None
            
        try:
            full_audio = np.concatenate(self.full_audio_buffer)
            # Flatten
            if full_audio.ndim > 1:
                full_audio = full_audio.flatten()
                
            # Convert to int16
            audio_int16 = np.int16(full_audio * 32767)
            
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
                
            return output_path
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return None

    def get_transcription_data(self):
        """Get transcription data for saving notes."""
        # Combine all transcribed text
        all_text = " ".join([seg['text'] for seg in self.transcribed_segments]).strip()
        
        return {
            'text': all_text,
            'language': self.detected_language or self.language,
            'segments': self.transcribed_segments
        }



