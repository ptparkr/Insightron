#!/usr/bin/env python3
"""
Emotion Analyzer for Insightron Multi-Pass Transcription
Analyzes text characteristics to inject emotional markers like [Cheerful], [Urgent], etc.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from insightron.core.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmotionMetrics:
    """Container for emotion analysis metrics"""
    word_density: float  # Words per second
    exclamation_count: int
    question_count: int
    avg_sentence_length: float
    sentence_length_variance: float
    energy_keywords: int  # Count of high-energy words
    calm_keywords: int  # Count of calm/thoughtful words
    detected_emotion: Optional[str] = None


class EmotionAnalyzer:
    """
    Analyzes text characteristics to detect and inject emotional markers.
    
    Uses metrics like word density, punctuation patterns, and keyword analysis
    to classify the emotional tone of transcribed speech.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the emotion analyzer with configurable thresholds.
        
        Args:
            config: Optional config dict, otherwise loads from global config
        """
        if config is None:
            config = {}
            
        # Load thresholds from config with defaults
        thresholds = config.get('thresholds', {})
        self.high_energy_wps = thresholds.get('high_energy_wps', 3.5)
        self.low_energy_wps = thresholds.get('low_energy_wps', 2.0)
        self.min_exclamations = thresholds.get('min_exclamations', 2)
        self.serious_sentence_length = thresholds.get('serious_sentence_length', 20)
        
        # Enabled emotions
        enabled = config.get('enabled_emotions', [
            'cheerful', 'urgent', 'calm', 'excited', 'serious'
        ])
        self.enabled_emotions = set(enabled)
        
        # High-energy keywords
        self.energy_keywords = {
            'amazing', 'awesome', 'fantastic', 'incredible', 'wonderful',
            'excited', 'thrilled', 'energized', 'pumped', 'fired up',
            'love', 'adore', 'passion', 'enthusiastic', 'dynamic',
            'quick', 'fast', 'rapid', 'immediately', 'urgently',
            'critical', 'crucial', 'vital', 'essential', 'important',
            'must', 'need to', 'have to', 'got to', 'gotta'
        }
        
        # Calm/thoughtful keywords
        self.calm_keywords = {
            'consider', 'reflect', 'ponder', 'contemplate', 'think',
            'understand', 'realize', 'comprehend', 'grasp', 'appreciate',
            'peaceful', 'calm', 'serene', 'tranquil', 'quiet',
            'mindful', 'aware', 'conscious', 'deliberate', 'intentional',
            'perhaps', 'maybe', 'possibly', 'potentially', 'likely',
            'thoughtful', 'careful', 'measured', 'balanced', 'steady'
        }
        
        # Pre-compiled patterns
        self._sentence_split = re.compile(r'[.!?]+')
        self._word_pattern = re.compile(r'\b\w+\b')
        
        logger.info(f"EmotionAnalyzer initialized with enabled emotions: {self.enabled_emotions}")
    
    def analyze_text(self, text: str, duration_seconds: float) -> EmotionMetrics:
        """
        Analyze text to extract emotion metrics.
        
        Args:
            text: Transcribed text to analyze
            duration_seconds: Duration of the audio in seconds
            
        Returns:
            EmotionMetrics object with all calculated metrics
        """
        if not text or not text.strip():
            return EmotionMetrics(
                word_density=0.0,
                exclamation_count=0,
                question_count=0,
                avg_sentence_length=0.0,
                sentence_length_variance=0.0,
                energy_keywords=0,
                calm_keywords=0,
                detected_emotion=None
            )
        
        # Calculate word density
        words = self._word_pattern.findall(text)
        word_count = len(words)
        word_density = word_count / duration_seconds if duration_seconds > 0 else 0.0
        
        # Count punctuation
        exclamation_count = text.count('!')
        question_count = text.count('?')
        
        # Analyze sentences
        sentences = [s.strip() for s in self._sentence_split.split(text) if s.strip()]
        sentence_lengths = [len(self._word_pattern.findall(s)) for s in sentences]
        
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0.0
        
        # Calculate variance
        if sentence_lengths:
            mean = avg_sentence_length
            variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
            sentence_length_variance = variance ** 0.5  # Standard deviation
        else:
            sentence_length_variance = 0.0
        
        # Keyword analysis
        text_lower = text.lower()
        energy_keywords = sum(1 for keyword in self.energy_keywords if keyword in text_lower)
        calm_keywords = sum(1 for keyword in self.calm_keywords if keyword in text_lower)
        
        metrics = EmotionMetrics(
            word_density=word_density,
            exclamation_count=exclamation_count,
            question_count=question_count,
            avg_sentence_length=avg_sentence_length,
            sentence_length_variance=sentence_length_variance,
            energy_keywords=energy_keywords,
            calm_keywords=calm_keywords
        )
        
        # Classify emotion
        metrics.detected_emotion = self._classify_emotion(metrics)
        
        return metrics
    
    def _classify_emotion(self, metrics: EmotionMetrics) -> Optional[str]:
        """
        Classify emotion based on a weighted scoring system.
        Calculates confidence scores for each emotion and returns the strongest one.
        """
        scores = {}
        
        # 1. Excited Score
        if 'excited' in self.enabled_emotions:
            score = 0
            if metrics.word_density >= self.high_energy_wps: score += 40
            score += min(metrics.exclamation_count * 20, 40)
            score += min(metrics.energy_keywords * 15, 30)
            if metrics.question_count > 0: score += 10
            scores['Excited'] = score
            
        # 2. Urgent Score
        if 'urgent' in self.enabled_emotions:
            score = 0
            if metrics.word_density >= self.high_energy_wps: score += 30
            score += min(metrics.energy_keywords * 25, 50)
            if metrics.avg_sentence_length < 10: score += 20 # Short, punchy sentences
            scores['Urgent'] = score
            
        # 3. Cheerful Score
        if 'cheerful' in self.enabled_emotions:
            score = 0
            if metrics.word_density >= self.high_energy_wps: score += 20
            score += min(metrics.energy_keywords * 20, 40)
            if metrics.exclamation_count >= 1: score += 20
            if metrics.sentence_length_variance > 5: score += 20 # Varied, lively speech
            scores['Cheerful'] = score
            
        # 4. Serious Score
        if 'serious' in self.enabled_emotions:
            score = 0
            if metrics.avg_sentence_length >= self.serious_sentence_length: score += 40
            if metrics.word_density < self.high_energy_wps: score += 20
            if metrics.exclamation_count == 0: score += 30
            if metrics.calm_keywords >= 1: score += 10
            scores['Serious'] = score
            
        # 5. Calm Score
        if 'calm' in self.enabled_emotions:
            score = 0
            if metrics.word_density <= self.low_energy_wps: score += 40
            score += min(metrics.calm_keywords * 25, 40)
            if metrics.exclamation_count == 0: score += 20
            scores['Calm'] = score
            
        # Select best emotion if it exceeds threshold (e.g., 60)
        best_emotion = None
        max_score = 60 # Minimum confidence threshold
        
        for emotion, score in scores.items():
            if score >= max_score:
                max_score = score
                best_emotion = emotion
                
        return best_emotion
    
    def inject_emotion_marker(self, text: str, emotion: str) -> str:
        """
        Inject emotion marker at the beginning of text.
        
        Args:
            text: Text to modify
            emotion: Emotion label (e.g., 'Cheerful')
            
        Returns:
            Text with emotion marker
        """
        if not emotion:
            return text
        
        marker = f"[{emotion}]"
        
        # Add marker at the start if not already present
        if not text.strip().startswith('['):
            return f"{marker} {text.strip()}"
        
        return text
    
    def analyze_and_inject(self, text: str, duration_seconds: float) -> tuple[str, EmotionMetrics]:
        """
        Analyze text and inject emotion marker if detected.
        
        Args:
            text: Transcribed text
            duration_seconds: Audio duration in seconds
            
        Returns:
            Tuple of (modified_text, metrics)
        """
        metrics = self.analyze_text(text, duration_seconds)
        
        if metrics.detected_emotion:
            modified_text = self.inject_emotion_marker(text, metrics.detected_emotion)
            logger.info(f"Detected emotion: {metrics.detected_emotion} (WPS: {metrics.word_density:.2f})")
        else:
            modified_text = text
            logger.debug(f"No emotion detected (WPS: {metrics.word_density:.2f})")
        
        return modified_text, metrics
    
    def analyze_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Analyze multiple text chunks and inject emotion markers.
        
        Args:
            chunks: List of dicts with 'text', 'start', 'end' keys
            
        Returns:
            List of chunks with emotion markers injected
        """
        results = []
        
        for chunk in chunks:
            text = chunk.get('text', '')
            start = chunk.get('start', 0)
            end = chunk.get('end', 0)
            duration = end - start
            
            modified_text, metrics = self.analyze_and_inject(text, duration)
            
            result_chunk = chunk.copy()
            result_chunk['text'] = modified_text
            result_chunk['emotion_metrics'] = metrics
            
            results.append(result_chunk)
        
        return results
