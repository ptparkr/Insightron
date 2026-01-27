import logging
from typing import Optional, Dict, Any, Tuple, Iterator
from faster_whisper import WhisperModel
from faster_whisper.transcribe import TranscriptionInfo, Segment
from insightron.core.config import get_config_manager
from insightron.core.resource_manager import ResourceManager
# from insightron.services.transcription.quality_metrics import QualityMetricsCalculator  <-- Removed to avoid circular import
import numpy as np
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """
    Quality-optimized Whisper model manager using faster-whisper v1.2.1.
    
    Features:
    - 3-4x faster than transformers backend
    - 50% lower memory usage  
    - Optimized for maximum accuracy and stability
    - Enhanced VAD for cleaner segments
    - Intelligent retry mechanism
    - Confidence tracking for quality assurance
    - Uses importlib.metadata (no pkg_resources warnings)
    
    Quality Optimizations:
    - Optimal beam_size for accuracy vs speed
    - Temperature fallback for difficult audio
    - VAD filtering to remove silence/noise
    - Segment confidence tracking
    - Graceful degradation on errors
    
    Returns API:
        transcribe() returns tuple: (segments_iterator, TranscriptionInfo)
        - segments: Iterator of Segment with .text, .start, .end, .id, .avg_logprob
        - info: TranscriptionInfo with .language, .language_probability, .duration
    """
    _instance = None
    _model = None
    _loaded_model_size = None  # Track which model is currently loaded

    # Performance-optimized default parameters with dynamic tuning
    DEFAULT_PARAMS = {
        "beam_size": 5,  # Accuracy priority (1=fastest, 5=balanced, 10=best)
        "best_of": 5,  # Number of candidates for beam search
        "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],  # Fallback temperatures
        "condition_on_previous_text": True,  # Use context for better accuracy
        "compression_ratio_threshold": 2.4,  # Detect repetition/failures
        "log_prob_threshold": -1.0,  # Filter low-confidence segments
        "no_speech_threshold": 0.6,  # Detect silence/non-speech
        "patience": 1.0,  # Beam search patience (faster convergence)
        "length_penalty": 1.0,  # Length penalty for beam search
    }
    
    # Enhanced VAD parameters for cleaner segments (optimized for accuracy)
    VAD_PARAMS = {
        "threshold": 0.5,  # Speech detection confidence (0.0-1.0)
        "min_speech_duration_ms": 250,  # Ignore very short utterances
        "min_silence_duration_ms": 2000,  # Merge segments with short gaps
        "speech_pad_ms": 400,  # Padding around detected speech
    }
    
    # Performance cache for model warm-up
    _model_warmup_done = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Get configuration
        config = get_config_manager()
        self.model_size = config.model.name
        self.compute_type = config.model.compute_type
        
        # Device selection
        device_setting = config.model.device
        self.device = "auto" if device_setting == "auto" else device_setting
        
        # Quality mode configuration
        self.quality_mode = config.get('model.quality_mode', 'balanced')  # high|balanced|fast
        self.enable_vad = config.get('model.enable_vad', True)
        self.enable_retry = config.get('model.enable_retry', True)
        self.max_retries = config.get('model.max_retries', 2)
        
        # Adaptive VAD: dynamically adjust threshold based on audio characteristics
        self.adaptive_vad = config.get('model.adaptive_vad', False)
        self.batch_size = config.get('model.batch_size', 1)  # Batch inference support
        
        
        # Initialize ResourceManager
        self.resource_manager = ResourceManager()
        
        # Override compute_type if resources are constrained
        recommended_quantization = self.resource_manager.recommend_quantization()
        
        if self.compute_type not in ["int8", "int8_float16"] and recommended_quantization == "int8":
             logger.warning(f"Low memory detected. Downgrading compute_type from {self.compute_type} to int8")
             self.compute_type = "int8"

        # Performance optimizations
        self.enable_model_warmup = config.get('model.enable_warmup', True)
        self.enable_dynamic_beam = config.get('model.enable_dynamic_beam', True)
        self.audio_analysis_cache = {}  # Cache for audio characteristics
        
        # Use QualityMetricsCalculator for consistency - local import to avoid circular dependency
        from insightron.services.transcription.quality_metrics import QualityMetricsCalculator
        self.quality_metrics_calculator = QualityMetricsCalculator()
        
        # Adjust parameters based on quality mode
        self._configure_quality_mode()
        
        logger.info(f"ModelManager initialized: Model={self.model_size}, Device={self.device}, "
                   f"Quality={self.quality_mode}, VAD={self.enable_vad}, AdaptiveVAD={self.adaptive_vad}, "
                   f"Warmup={self.enable_model_warmup}, DynamicBeam={self.enable_dynamic_beam}")

    def _configure_quality_mode(self):
        """Configure parameters based on quality mode."""
        if self.quality_mode == "high":
            # Maximum accuracy - slower but best results
            self.default_beam_size = 5
            self.default_best_of = 5
        elif self.quality_mode == "balanced":
            # Balance speed and accuracy
            self.default_beam_size = 3
            self.default_best_of = 3
        else:  # fast
            # Speed priority - faster but lower accuracy
            self.default_beam_size = 1
            self.default_best_of = 1

    def load_model(self) -> WhisperModel:
        """
        Loads the faster-whisper WhisperModel if not already loaded or if model size changed.
        Includes model warm-up for better first-inference performance.
        
        Returns:
            WhisperModel: Loaded model instance
        """
        # Always check current config in case it changed
        config = get_config_manager()
        current_model_size = config.model.name
        
        # Check if we need to reload: model not loaded or model size changed
        if self._model is None or ModelManager._loaded_model_size != current_model_size:
            # If model size changed, clear the old model
            if self._model is not None and ModelManager._loaded_model_size != current_model_size:
                logger.info(f"Model size changed from '{ModelManager._loaded_model_size}' to '{current_model_size}'. Reloading model...")
                
                # Check system health before reloading
                health = self.resource_manager.check_health()
                if health['status'] == 'constrained':
                     logger.warning(f"System constrained during model reload: {health['warnings']}")
                     # We proceed but warn

                # Clean up old model if possible
                try:
                    del self._model
                except:
                    pass
                self._model = None
                ModelManager._model_warmup_done = False  # Reset warmup flag for new model
            
            # Update instance model_size to match current config
            self.model_size = current_model_size
            
            logger.info(f"Loading faster-whisper v1.2.1: {self.model_size} on {self.device}...")
            print(f"🔄 Loading Whisper model: {self.model_size}")
            print("   (This may take a moment - downloading model files if needed...)")
            print("   (First-time download can take 1-5 minutes depending on model size)")
            
            try:
                # Map model names for compatibility
                model_name = self.model_size
                
                # Handle transformers-style naming
                if model_name.startswith("openai/whisper-"):
                    model_name = model_name.replace("openai/whisper-", "")
                    logger.info(f"Mapped model name: {self.model_size} -> {model_name}")
                
                # Check if model needs download
                import os
                from pathlib import Path
                cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
                model_cache = cache_dir / f"models--guillaumekln--faster-whisper-{model_name}"
                
                if not model_cache.exists():
                    print(f"   📥 Downloading model '{model_name}' (this may take several minutes)...")
                    print("   💡 Tip: Model download happens once and is cached for future use")
                else:
                    print(f"   ✓ Model found in cache, loading...")
                
                self._model = WhisperModel(
                    model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=None,
                    local_files_only=False
                )
                ModelManager._loaded_model_size = self.model_size  # Track loaded model size
                logger.info(f"✓ Model loaded successfully: {model_name}")
                print(f"   ✅ Model '{model_name}' loaded successfully!")
                
                # Warm up the model for better first-inference performance
                if self.enable_model_warmup and not ModelManager._model_warmup_done:
                    self._warmup_model()
                    ModelManager._model_warmup_done = True
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to load model: {error_msg}")
                
                # Provide helpful error messages
                if "download" in error_msg.lower() or "connection" in error_msg.lower():
                    print(f"\n❌ Error downloading model '{model_name}':")
                    print("   This could be due to:")
                    print("   - Slow or unstable internet connection")
                    print("   - Firewall blocking the download")
                    print("   - Hugging Face servers being temporarily unavailable")
                    print("\n   💡 Solutions:")
                    print("   1. Check your internet connection")
                    print("   2. Try again in a few minutes")
                    print("   3. Manually download the model from:")
                    print(f"      https://huggingface.co/guillaumekln/faster-whisper-{model_name}")
                    raise RuntimeError(f"Could not download model '{self.model_size}': {error_msg}")
                else:
                    print(f"\n❌ Error loading model '{model_name}': {error_msg}")
                    raise RuntimeError(f"Could not load model '{self.model_size}': {error_msg}")
        return self._model
    
    def _warmup_model(self):
        """Warm up the model with a dummy inference to optimize first real inference."""
        try:
            logger.info("Warming up model for optimal performance...")
            # Create a small dummy audio array (1 second of silence at 16kHz)
            dummy_audio = np.zeros(16000, dtype=np.float32)
            start_time = time.time()
            
            # Run a quick warmup inference
            segments, _ = self._model.transcribe(
                dummy_audio,
                beam_size=1,
                language=None,
                task="transcribe",
                vad_filter=False
            )
            # Consume the iterator to actually run inference
            list(segments)
            
            warmup_time = time.time() - start_time
            logger.info(f"✓ Model warmup completed in {warmup_time:.2f}s")
        except Exception as e:
            logger.warning(f"Model warmup failed (non-critical): {e}")

    def transcribe(
        self,
        audio,
        language: Optional[str] = None,
        task: str = "transcribe",
        **kwargs
    ) -> Tuple[Iterator[Segment], TranscriptionInfo]:
        """
        High-quality transcription with optimal parameters and retry mechanism.
        
        Args:
            audio: Audio file path (str) or numpy array (float32, 16kHz mono)
            language: Language code ('en', 'es', etc.) or None for auto-detect
            task: 'transcribe' or 'translate'
            **kwargs: Override default parameters
                - beam_size: Beam search width
                - temperature: Sampling temperature(s)
                - vad_filter: Enable VAD
                - condition_on_previous_text: Use context
                
        Returns:
            tuple: (segments_iterator, TranscriptionInfo)
                - segments: Iterator of Segment objects with .text, .start, .end, .avg_logprob
                - info: TranscriptionInfo with .language, .language_probability, .duration
        """
        model = self.load_model()
        
        # Merge default quality parameters with user overrides (pass audio for optimization)
        params = self._build_transcription_params(language, task, audio=audio, **kwargs)
        
        # Attempt transcription with retry mechanism
        if self.enable_retry:
            return self._transcribe_with_retry(model, audio, params)
        else:
            return self._transcribe_once(model, audio, params)

    def _build_transcription_params(
        self,
        language: Optional[str],
        task: str,
        audio: Any = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build optimized transcription parameters with dynamic tuning."""
        # Get base parameters
        beam_size = kwargs.pop("beam_size", self.default_beam_size)
        best_of = kwargs.pop("best_of", self.default_best_of)
        
        # Dynamic beam size adjustment based on audio characteristics
        if self.enable_dynamic_beam and audio is not None:
            beam_size, best_of = self._optimize_beam_size(audio, beam_size, best_of)
        
        params = {
            "language": language,
            "task": task,
            "beam_size": beam_size,
            "best_of": best_of,
            "temperature": kwargs.pop("temperature", self.DEFAULT_PARAMS["temperature"]),
            "condition_on_previous_text": kwargs.pop(
                "condition_on_previous_text",
                self.DEFAULT_PARAMS["condition_on_previous_text"]
            ),
            "compression_ratio_threshold": kwargs.pop(
                "compression_ratio_threshold",
                self.DEFAULT_PARAMS["compression_ratio_threshold"]
            ),
            "log_prob_threshold": kwargs.pop(
                "log_prob_threshold",
                self.DEFAULT_PARAMS["log_prob_threshold"]
            ),
            "no_speech_threshold": kwargs.pop(
                "no_speech_threshold",
                self.DEFAULT_PARAMS["no_speech_threshold"]
            ),
            "patience": kwargs.pop("patience", self.DEFAULT_PARAMS.get("patience", 1.0)),
            "length_penalty": kwargs.pop("length_penalty", self.DEFAULT_PARAMS.get("length_penalty", 1.0)),
            "vad_filter": kwargs.pop("vad_filter", self.enable_vad),
        }
        
        # Add VAD parameters if enabled (with adaptive tuning)
        if params["vad_filter"]:
            vad_params = self.VAD_PARAMS.copy()
            if self.adaptive_vad and audio is not None:
                vad_params = self._optimize_vad_params(audio, vad_params)
            params["vad_parameters"] = kwargs.pop("vad_parameters", vad_params)
        
        # Include any additional kwargs
        params.update(kwargs)
        
        return params
    
    def _optimize_beam_size(self, audio: Any, default_beam: int, default_best_of: int) -> Tuple[int, int]:
        """
        Dynamically optimize beam size based on audio characteristics.
        For longer/complex audio, use higher beam size for accuracy.
        For shorter/simple audio, use lower beam size for speed.
        Refined logic for better granularity.
        """
        try:
            # Analyze audio if it's a numpy array
            if isinstance(audio, np.ndarray):
                duration = len(audio) / 16000  # Assume 16kHz
                
                # Refined logic:
                # < 5s: very short, speed is key (beam=1)
                # 5-30s: short, balanced (beam=default-1)
                # 30-120s: medium, default (beam=default)
                # > 120s: long, accuracy is key (beam=default+2)
                
                if duration < 5.0:
                    return 1, 1
                elif duration < 30.0:
                    return max(2, default_beam - 1), max(2, default_best_of - 1)
                elif duration > 120.0:
                    return min(10, default_beam + 2), min(10, default_best_of + 2)
                    
            # For file paths, use default (analysis would require loading)
            return default_beam, default_best_of
        except Exception as e:
            logger.debug(f"Beam size optimization failed: {e}, using defaults")
            return default_beam, default_best_of
    
    def _optimize_vad_params(self, audio: Any, base_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adaptively optimize VAD parameters based on audio characteristics.
        Adjusts threshold based on estimated noise level.
        Refined to be less aggressive on quiet speech.
        """
        try:
            if isinstance(audio, np.ndarray):
                # Estimate noise level from audio RMS
                # Use a more robust noise estimation if possible, but RMS is fast
                rms = np.sqrt(np.mean(audio**2))
                
                # Adjust threshold:
                # Very quiet (rms < 0.005): Lower threshold significantly to catch whispers
                # Quiet (rms < 0.02): Lower threshold slightly
                # Normal: Keep default
                # Loud/Noisy (rms > 0.1): Raise threshold to avoid noise
                
                if rms < 0.005:  # Very quiet audio
                    base_params["threshold"] = max(0.2, base_params["threshold"] - 0.2)
                elif rms < 0.02: # Quiet audio
                    base_params["threshold"] = max(0.3, base_params["threshold"] - 0.1)
                elif rms > 0.1:  # Loud/noisy audio
                    base_params["threshold"] = min(0.7, base_params["threshold"] + 0.1)
                    
            return base_params
        except Exception as e:
            logger.debug(f"VAD optimization failed: {e}, using defaults")
            return base_params

    def _transcribe_once(
        self,
        model: WhisperModel,
        audio,
        params: Dict[str, Any]
    ) -> Tuple[Iterator[Segment], TranscriptionInfo]:
        """Perform single transcription attempt."""
        try:
            segments, info = model.transcribe(audio, **params)
            return segments, info
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _transcribe_with_retry(
        self,
        model: WhisperModel,
        audio,
        params: Dict[str, Any]
    ) -> Tuple[Iterator[Segment], TranscriptionInfo]:
        """
        Transcribe with intelligent retry and fallback strategies.
        
        Strategy:
        - Attempt 1: Best quality (beam_size from config)
        - Attempt 2: Reduced quality (beam_size=3, simpler temperature)
        - Attempt 3: Minimal quality (beam_size=1, basic temperature)
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Adjust parameters for each retry
                if attempt == 1:
                    # Second attempt: reduce quality slightly
                    params["beam_size"] = 3
                    params["best_of"] = 3
                    params["temperature"] = [0.0, 0.2]
                    logger.warning(f"Retry {attempt}: Using balanced quality parameters")
                elif attempt == 2:
                    # Third attempt: minimum quality for speed
                    params["beam_size"] = 1
                    params["best_of"] = 1
                    params["temperature"] = [0.0]
                    params["vad_filter"] = False  # Disable VAD to be more permissive
                    logger.warning(f"Retry {attempt}: Using fast fallback parameters")
                
                segments, info = model.transcribe(audio, **params)
                
                if attempt > 0:
                    logger.info(f"✓ Transcription successful on retry {attempt}")
                
                return segments, info
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt == self.max_retries:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
                    raise RuntimeError(
                        f"Transcription failed after {self.max_retries + 1} attempts: {last_error}"
                    )
        
        # Should never reach here, but for type safety
        raise RuntimeError(f"Unexpected error in retry logic: {last_error}")

    def get_quality_metrics(self, segments: list) -> Dict[str, Any]:
        """
        Calculate quality metrics for transcribed segments.
        Uses QualityMetricsCalculator for consistency.
        
        Args:
            segments: List of Segment objects from faster-whisper
            
        Returns:
            Dictionary with quality metrics
        """
        if not segments:
            return {
                "avg_confidence": 0.0,
                "low_confidence_count": 0,
                "total_segments": 0
            }
        
        # Convert Segment objects to dict format for QualityMetricsCalculator
        segment_dicts = []
        for seg in segments:
            segment_dict = {
                'start': seg.start,
                'end': seg.end,
                'text': seg.text
            }
            if hasattr(seg, 'avg_logprob'):
                segment_dict['confidence'] = seg.avg_logprob
            segment_dicts.append(segment_dict)
        
        # Use QualityMetricsCalculator
        metrics = self.quality_metrics_calculator.calculate_metrics(segment_dicts)
        
        # Return backward-compatible format
        confidences = [seg.avg_logprob for seg in segments if hasattr(seg, 'avg_logprob')]
        return {
            "avg_confidence": metrics['confidence_simple_avg'],
            "low_confidence_count": sum(1 for c in confidences if c < -0.5),
            "total_segments": metrics['segment_count'],
            "min_confidence": min(confidences) if confidences else 0.0,
            "max_confidence": max(confidences) if confidences else 0.0,
            "quality_tier": metrics['quality_tier'],
            "degradation_detected": metrics['degradation_detected']
        }
