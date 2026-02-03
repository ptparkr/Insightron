#!/usr/bin/env python3
"""
Multi-Pass Transcriber for Insightron
Orchestrates the three-pass transcription pipeline:
- Pass 1: Detection (base model)
- Pass 2: Contextual Restoration (LLM)
- Pass 3: Emotion Mapping (sentiment analysis)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from insightron.core.config import get_config
from insightron.services.transcription.audio_loader import AudioLoader
from insightron.services.transcription.transcription_engine import TranscriptionEngine
from insightron.services.transcription.llm_provider import LLMProviderFactory
from insightron.services.transcription.emotion_analyzer import EmotionAnalyzer
from insightron.services.transcription.text_formatter import TextFormatter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MultiPassResult:
    """Result from multi-pass transcription"""
    pass1_raw_text: str
    pass2_restored_text: str
    pass3_final_text: str
    segments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_times: Dict[str, float]


class BatchChunker:
    """Handles audio chunking with overlap for batch processing"""
    
    def __init__(self, chunk_duration: float = 30.0, overlap: float = 2.0):
        """
        Initialize batch chunker.
        
        Args:
            chunk_duration: Chunk size in seconds
            overlap: Overlap between chunks in seconds
        """
        self.chunk_duration = chunk_duration
        self.overlap = overlap
        self.audio_loader = AudioLoader()
    
    def should_chunk(self, duration: float) -> bool:
        """
        Determine if audio should be chunked.
        
        Args:
            duration: Audio duration in seconds
            
        Returns:
            True if chunking is beneficial
        """
        return duration > self.chunk_duration
    
    def create_chunks_from_segments(self, segments: List[Dict], total_duration: float) -> List[List[Dict]]:
        """
        Group segments into time-based chunks.
        
        Args:
            segments: List of transcription segments
            total_duration: Total audio duration
            
        Returns:
            List of segment chunks
        """
        if not segments:
            return []
        
        chunks = []
        current_chunk = []
        chunk_start_time = 0
        
        for segment in segments:
            segment_start = segment.get('start', 0)
            segment_end = segment.get('end', 0)
            
            # Check if segment should start a new chunk
            if segment_start >= chunk_start_time + self.chunk_duration and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                # Account for overlap
                chunk_start_time = segment_start - self.overlap
            
            current_chunk.append(segment)
        
        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Created {len(chunks)} chunks from {len(segments)} segments")
        return chunks
    
    def merge_chunk_texts(self, chunk_texts: List[str]) -> str:
        """
        Merge text from multiple chunks, handling overlap.
        
        Args:
            chunk_texts: List of text strings from chunks
            
        Returns:
            Merged text
        """
        if not chunk_texts:
            return ""
        
        if len(chunk_texts) == 1:
            return chunk_texts[0]
        
        # Simple merge - just concatenate with spacing
        # In a more sophisticated version, we could deduplicate overlapping words
        merged = " ".join(chunk_texts)
        return merged


class MultiPassTranscriber:
    """
    Orchestrates the multi-pass transcription pipeline.
    
    Pass 1: Detection - Uses base Whisper model for raw transcription
    Pass 2: Contextual Restoration - Uses LLM to add punctuation and fix errors
    Pass 3: Emotion Mapping - Analyzes text to inject emotion markers
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize multi-pass transcriber.
        
        Args:
            config: Optional config dict, otherwise loads from global config
        """
        if config is None:
            multi_pass_config = get_config('multi_pass', {})
        else:
            multi_pass_config = config
        
        self.multi_pass_config = multi_pass_config
        
        # Extract sub-configs
        self.chunk_duration = multi_pass_config.get('chunk_duration', 30)
        self.chunk_overlap = multi_pass_config.get('chunk_overlap', 2)
        
        restoration_config = multi_pass_config.get('contextual_restoration', {})
        self.pass2_enabled = restoration_config.get('enabled', True)
        
        emotion_config = multi_pass_config.get('emotion_mapping', {})
        self.pass3_enabled = emotion_config.get('enabled', True)
        
        # Initialize components
        self.audio_loader = AudioLoader()
        self.transcription_engine = TranscriptionEngine()
        self.chunker = BatchChunker(self.chunk_duration, self.chunk_overlap)
        
        # Lazy-initialized components
        self.llm_provider = None
        self.emotion_analyzer = None
        self.text_formatter = TextFormatter()
        
        logger.info(f"MultiPassTranscriber initialized (Pass2: {self.pass2_enabled}, Pass3: {self.pass3_enabled})")
    
    def _init_llm_provider(self):
        """Lazy initialize LLM provider"""
        if self.llm_provider is None and self.pass2_enabled:
            try:
                self.llm_provider = LLMProviderFactory.create_from_config(self.multi_pass_config)
                if not self.llm_provider.is_available():
                    logger.warning("LLM provider not available, disabling Pass 2")
                    self.pass2_enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize LLM provider: {e}")
                self.pass2_enabled = False
    
    def _init_emotion_analyzer(self):
        """Lazy initialize emotion analyzer"""
        if self.emotion_analyzer is None and self.pass3_enabled:
            emotion_config = self.multi_pass_config.get('emotion_mapping', {})
            self.emotion_analyzer = EmotionAnalyzer(emotion_config)
    
    def pass1_detect(
        self,
        audio_path: str,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[List[Dict], Any]:
        """
        Pass 1: Detect raw text using base model.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (segments, transcription_info)
        """
        if progress_callback:
            progress_callback("Pass 1/3: Detecting speech with base model...")
        
        logger.info("=== Pass 1: Detection ===")
        
        # 1. Resource Validation
        self.transcription_engine.literal_transcriber.validate_resources()
        
        # 2. Signal Intake
        self.audio_loader.validate_audio_file(audio_path)
        metadata = self.audio_loader.get_audio_metadata(audio_path)
        signal = self.audio_loader.load_signal(audio_path)
        
        # 3. Deterministic Chunking (aligning with AudioTranscriber)
        chunks = self.audio_loader.segment_by_time(signal, segment_seconds=30.0)
        
        all_segments = []
        num_chunks = len(chunks)
        
        # 4. Transcribe Loop
        for i, chunk in enumerate(chunks):
            if progress_callback:
                progress_callback(f"Pass 1/3: Processing chunk {i+1}/{num_chunks}...")
            
            chunk_segments = self.transcription_engine.process_signal_single_pass(
                chunk["signal"],
                language=language,
                offset_time=chunk["start_time"]
            )
            all_segments.extend(chunk_segments)
        
        # Build a dummy info object for compatibility
        from dataclasses import dataclass
        @dataclass
        class Info:
            language: str
            duration: float
        
        info = Info(language=language or "auto", duration=metadata.get('duration', 0))
        
        logger.info(f"Pass 1 complete: {len(all_segments)} segments detected")
        return all_segments, info
    
    def pass2_restore(
        self,
        segments: List[Dict],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Dict]:
        """
        Pass 2: Restore punctuation and fix errors using LLM with v2 philosophy.
        """
        if not self.pass2_enabled:
            logger.info("Pass 2 disabled, skipping restoration")
            return segments
        
        if progress_callback:
            progress_callback("Pass 2/3: Restoring text with v2 Quality Engine...")
        
        logger.info("=== Pass 2: Contextual Restoration (v2) ===")
        
        self._init_llm_provider()
        
        if self.llm_provider is None:
            logger.warning("LLM provider unavailable, skipping Pass 2")
            return segments
        
        # Group segments into chunks
        total_duration = max(seg.get('end', 0) for seg in segments) if segments else 0
        chunk_groups = self.chunker.create_chunks_from_segments(segments, total_duration)
        
        restored_segments = []
        prev_clean = None
        
        num_chunks = len(chunk_groups)
        for i, chunk in enumerate(chunk_groups):
            if progress_callback:
                progress_callback(f"Pass 2/3: Restoring chunk {i+1}/{num_chunks}...")
            
            # Combine current chunk text
            chunk_text = " ".join(seg.get('text', '') for seg in chunk)
            
            # Lookahead: get next chunk text if available
            next_raw = None
            if i + 1 < num_chunks:
                next_raw = " ".join(seg.get('text', '') for seg in chunk_groups[i+1])
            
            # Restore with LLM using v2 philosophy
            result = self.llm_provider.restore_text(chunk_text, prev_clean, next_raw)
            
            if result.success:
                # Distribute restored text back to segments
                restored_chunk = self._distribute_restored_text(chunk, result.restored_text)
                
                # Add flags and stitched status to segments for tracking
                for seg in restored_chunk:
                    seg['quality_flags'] = result.flags
                    seg['stitched'] = result.stitched
                
                restored_segments.extend(restored_chunk)
                
                # Update prev_clean for next iteration
                prev_clean = result.restored_text
            else:
                logger.warning(f"Restoration failed for chunk {i+1}: {result.error}")
                restored_segments.extend(chunk)
        
        logger.info(f"Pass 2 complete: Restored {len(restored_segments)} segments")
        return restored_segments
    
    def _distribute_restored_text(self, original_segments: List[Dict], restored_text: str) -> List[Dict]:
        """
        Distribute restored text back to original segments.
        
        Args:
            original_segments: Original segment list
            restored_text: Restored text from LLM
            
        Returns:
            Updated segments with restored text
        """
        # Simple approach: proportionally distribute text by word count
        # More sophisticated: use word-level alignment
        
        restored_segments = []
        words = restored_text.split()
        total_original_words = sum(len(seg.get('text', '').split()) for seg in original_segments)
        
        if total_original_words == 0:
            return original_segments
        
        word_idx = 0
        
        for seg in original_segments:
            original_words = len(seg.get('text', '').split())
            proportion = original_words / total_original_words
            target_words = max(1, int(len(words) * proportion))
            
            # Extract words for this segment
            segment_words = words[word_idx:word_idx + target_words]
            word_idx += target_words
            
            # Update segment
            updated_seg = seg.copy()
            updated_seg['text'] = ' '.join(segment_words)
            restored_segments.append(updated_seg)
        
        return restored_segments
    
    def pass3_map_emotions(
        self,
        segments: List[Dict],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Dict]:
        """
        Pass 3: Analyze and inject emotion markers.
        
        Args:
            segments: Segments from Pass 2
            progress_callback: Optional progress callback
            
        Returns:
            Segments with emotion markers
        """
        if not self.pass3_enabled:
            logger.info("Pass 3 disabled, skipping emotion mapping")
            return segments
        
        if progress_callback:
            progress_callback("Pass 3/3: Mapping emotions...")
        
        logger.info("=== Pass 3: Emotion Mapping ===")
        
        self._init_emotion_analyzer()
        
        # Convert segments to chunks for emotion analysis
        chunks = []
        for i, seg in enumerate(segments):
            chunks.append({
                'text': seg.get('text', ''),
                'start': seg.get('start', 0),
                'end': seg.get('end', 0),
                'id': seg.get('id', i)
            })
        
        # Analyze emotions
        analyzed_chunks = self.emotion_analyzer.analyze_chunks(chunks)
        
        # Update original segments
        emotion_segments = []
        for i, seg in enumerate(segments):
            if i < len(analyzed_chunks):
                updated_seg = seg.copy()
                updated_seg['text'] = analyzed_chunks[i]['text']
                updated_seg['emotion_metrics'] = analyzed_chunks[i].get('emotion_metrics')
                emotion_segments.append(updated_seg)
            else:
                emotion_segments.append(seg)
        
        logger.info(f"Pass 3 complete: Analyzed {len(emotion_segments)} segments")
        return emotion_segments
    
    def transcribe_multipass(
        self,
        audio_path: str,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> MultiPassResult:
        """
        Execute full multi-pass transcription pipeline.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            progress_callback: Optional progress callback
            
        Returns:
            MultiPassResult with all pass outputs
        """
        start_time = datetime.now()
        processing_times = {}
        
        # Pass 1: Detection
        pass1_start = datetime.now()
        segments1, info = self.pass1_detect(audio_path, language, progress_callback)
        processing_times['pass1_detection'] = (datetime.now() - pass1_start).total_seconds()
        
        pass1_text = " ".join(seg.get('text', '') for seg in segments1)
        
        # Pass 2: Restoration
        pass2_start = datetime.now()
        segments2 = self.pass2_restore(segments1, progress_callback)
        processing_times['pass2_restoration'] = (datetime.now() - pass2_start).total_seconds()
        
        pass2_text = " ".join(seg.get('text', '') for seg in segments2)
        
        # Pass 3: Emotion Mapping
        pass3_start = datetime.now()
        segments3 = self.pass3_map_emotions(segments2, progress_callback)
        processing_times['pass3_emotion'] = (datetime.now() - pass3_start).total_seconds()
        
        pass3_text = " ".join(seg.get('text', '') for seg in segments3)
        
        # Total time
        processing_times['total'] = (datetime.now() - start_time).total_seconds()
        
        # Build metadata
        metadata = {
            'language': info.language if hasattr(info, 'language') else 'unknown',
            'duration': info.duration if hasattr(info, 'duration') else 0,
            'num_segments': len(segments3),
            'passes_completed': {
                'detection': True,
                'restoration': self.pass2_enabled,
                'emotion': self.pass3_enabled
            }
        }
        
        logger.info(f"Multi-pass transcription complete in {processing_times['total']:.2f}s")
        
        return MultiPassResult(
            pass1_raw_text=pass1_text,
            pass2_restored_text=pass2_text,
            pass3_final_text=pass3_text,
            segments=segments3,
            metadata=metadata,
            processing_times=processing_times
        )
