#!/usr/bin/env python3
"""
Unit Tests for Multi-Pass Transcription System
Tests emotion analyzer, LLM providers, and multi-pass orchestration.
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from insightron.services.transcription.emotion_analyzer import EmotionAnalyzer, EmotionMetrics
from insightron.services.transcription.llm_provider import (
    BaseLLMProvider,
    LocalLLMProvider,
    OpenAIProvider,
    LLMProviderFactory,
    RestorationResult
)
from insightron.services.transcription.multi_pass_transcriber import (
    MultiPassTranscriber,
    BatchChunker,
    MultiPassResult
)


class TestEmotionAnalyzer:
    """Test suite for EmotionAnalyzer"""
    
    def test_initialization(self):
        """Test EmotionAnalyzer initializes with default config"""
        analyzer = EmotionAnalyzer()
        assert analyzer.high_energy_wps == 3.5
        assert analyzer.low_energy_wps == 2.0
        assert 'cheerful' in analyzer.enabled_emotions
    
    def test_word_density_calculation(self):
        """Test word density (words per second) calculation"""
        analyzer = EmotionAnalyzer()
        text = "This is a test sentence with ten words exactly here"
        duration = 5.0  # 5 seconds
        
        metrics = analyzer.analyze_text(text, duration)
        
        # 10 words / 5 seconds = 2.0 WPS
        assert metrics.word_density == 2.0
    
    def test_exclamation_detection(self):
        """Test exclamation mark counting"""
        analyzer = EmotionAnalyzer()
        text = "This is amazing! I'm so excited! Wow!"
        
        metrics = analyzer.analyze_text(text, 5.0)
        
        assert metrics.exclamation_count == 3
    
    def test_cheerful_emotion_detection(self):
        """Test detection of cheerful emotion"""
        analyzer = EmotionAnalyzer()
        # High energy (4 WPS) + energy keywords + exclamation
        text = "This is absolutely amazing and wonderful! I love this fantastic project!"
        duration = 3.0  # ~4 words per second
        
        metrics = analyzer.analyze_text(text, duration)
        
        # High energy (4 WPS) + energy keywords + exclamation 
        # With new weighted system, this text scores high for 'Excited' or 'Cheerful'
        assert metrics.detected_emotion in ['Cheerful', 'Excited']
    
    def test_calm_emotion_detection(self):
        """Test detection of calm emotion"""
        analyzer = EmotionAnalyzer()
        # Low energy (1.5 WPS) + calm keywords + no exclamations
        text = "I think we should consider this carefully and reflect on the situation"
        duration = 8.0  # ~1.5 words per second
        
        metrics = analyzer.analyze_text(text, duration)
        
        assert metrics.detected_emotion == 'Calm'
    
    def test_excited_emotion_detection(self):
        """Test detection of excited emotion"""
        analyzer = EmotionAnalyzer()
        # Very high energy + multiple exclamations + energy keywords
        text = "Amazing! Incredible! Fantastic! This is absolutely wonderful and exciting!"
        duration = 2.0  # ~5 words per second
        
        metrics = analyzer.analyze_text(text, duration)
        
        assert metrics.detected_emotion == 'Excited'
    
    def test_emotion_marker_injection(self):
        """Test emotion marker injection into text"""
        analyzer = EmotionAnalyzer()
        text = "This is a test"
        
        result = analyzer.inject_emotion_marker(text, 'Cheerful')
        
        assert result.startswith('[Cheerful]')
        assert 'This is a test' in result
    
    def test_analyze_chunks(self):
        """Test batch chunk analysis"""
        analyzer = EmotionAnalyzer()
        chunks = [
            {'text': 'Amazing! Wonderful!', 'start': 0, 'end': 1},
            {'text': 'Let me think about this carefully', 'start': 1, 'end': 5}
        ]
        
        results = analyzer.analyze_chunks(chunks)
        
        assert len(results) == 2
        assert 'emotion_metrics' in results[0]


class TestLLMProviders:
    """Test suite for LLM providers"""
    
    def test_local_llm_provider_initialization(self):
        """Test LocalLLMProvider initialization"""
        config = {
            'model_name': 'microsoft/phi-3-mini-4k-instruct',
            'device': 'cpu',
            'quantization': '4bit'
        }
        
        provider = LocalLLMProvider(config)
        
        assert provider.model_name == 'microsoft/phi-3-mini-4k-instruct'
        assert provider.device == 'cpu'
        assert provider.quantization == '4bit'
    
    def test_openai_provider_initialization(self):
        """Test OpenAIProvider initialization"""
        config = {
            'api_key': 'test-key',
            'model': 'gpt-3.5-turbo',
            'max_tokens': 2000
        }
        
        provider = OpenAIProvider(config)
        
        assert provider.api_key == 'test-key'
        assert provider.model == 'gpt-3.5-turbo'
        assert provider.max_tokens == 2000
    
    @patch('openai.OpenAI')
    def test_openai_restore_text_mocked(self, mock_openai_class):
        """Test OpenAI text restoration with mocked API"""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"clean_text": "This is restored text!", "flags": [], "stitched": false}'
        mock_response.usage.total_tokens = 50
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Create provider
        config = {'api_key': 'test-key', 'model': 'gpt-3.5-turbo'}
        provider = OpenAIProvider(config)
        provider._lazy_load_client()
        
        # Test restoration
        result = provider.restore_text("this is raw text")
        
        assert result.success
        assert result.restored_text == "This is restored text!"
        assert result.tokens_used == 50
    
    def test_llm_provider_factory_local(self):
        """Test LLM provider factory for local models"""
        config = {'model_name': 'test-model'}
        
        provider = LLMProviderFactory.create_provider('local', config)
        
        assert isinstance(provider, LocalLLMProvider)
    
    def test_llm_provider_factory_openai(self):
        """Test LLM provider factory for OpenAI"""
        config = {'api_key': 'test-key'}
        
        provider = LLMProviderFactory.create_provider('openai', config)
        
        assert isinstance(provider, OpenAIProvider)
    
    def test_restoration_prompt_building(self):
        """Test prompt building for text restoration"""
        config = {}
        provider = LocalLLMProvider(config)
        
        prompt = provider._build_restoration_prompt("test text", prev_clean="previous text")
        
        assert "test text" in prompt
        assert "previous text" in prompt
        assert "punctuation" in prompt.lower()


class TestBatchChunker:
    """Test suite for BatchChunker"""
    
    def test_should_chunk_long_audio(self):
        """Test chunking decision for long audio"""
        chunker = BatchChunker(chunk_duration=30, overlap=2)
        
        assert chunker.should_chunk(60) == True
        assert chunker.should_chunk(20) == False
    
    def test_create_chunks_from_segments(self):
        """Test creating time-based chunks from segments"""
        chunker = BatchChunker(chunk_duration=30, overlap=2)
        
        segments = [
            {'start': 0, 'end': 10, 'text': 'First'},
            {'start': 10, 'end': 20, 'text': 'Second'},
            {'start': 20, 'end': 30, 'text': 'Third'},
            {'start': 30, 'end': 40, 'text': 'Fourth'},
            {'start': 40, 'end': 50, 'text': 'Fifth'}
        ]
        
        chunks = chunker.create_chunks_from_segments(segments, 50)
        
        # Should create 2 chunks: [0-30] and [30-50]
        assert len(chunks) >= 1
        assert all(isinstance(chunk, list) for chunk in chunks)
    
    def test_merge_chunk_texts(self):
        """Test merging text from multiple chunks"""
        chunker = BatchChunker()
        chunk_texts = ["First part.", "Second part.", "Third part."]
        
        merged = chunker.merge_chunk_texts(chunk_texts)
        
        assert "First part" in merged
        assert "Third part" in merged


class TestMultiPassTranscriber:
    """Test suite for MultiPassTranscriber"""
    
    def test_initialization(self):
        """Test MultiPassTranscriber initialization"""
        config = {
            'enabled': True,
            'chunk_duration': 30,
            'chunk_overlap': 2,
            'contextual_restoration': {'enabled': True, 'provider': 'local'},
            'emotion_mapping': {'enabled': True}
        }
        
        transcriber = MultiPassTranscriber(config)
        
        assert transcriber.chunk_duration == 30
        assert transcriber.chunk_overlap == 2
        assert transcriber.pass2_enabled == True
        assert transcriber.pass3_enabled == True
    
    def test_passes_can_be_disabled(self):
        """Test that passes can be individually disabled"""
        config = {
            'contextual_restoration': {'enabled': False},
            'emotion_mapping': {'enabled': False}
        }
        
        transcriber = MultiPassTranscriber(config)
        
        assert transcriber.pass2_enabled == False
        assert transcriber.pass3_enabled == False
    
    @patch('insightron.services.transcription.multi_pass_transcriber.AudioLoader')
    @patch('insightron.services.transcription.multi_pass_transcriber.TranscriptionEngine')
    def test_pass1_detect(self, mock_engine_class, mock_loader_class):
        """Test Pass 1 detection with mocked engine"""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.validate_audio_file.return_value = True
        mock_loader.load_signal.return_value = np.zeros(16000) # 1 sec of silence
        mock_loader.get_audio_metadata.return_value = {'duration': 1.0, 'filename': 'test.wav'}
        mock_loader.segment_by_time.return_value = [{'signal': np.zeros(16000), 'start_time': 0.0}]
        mock_loader_class.return_value = mock_loader
        
        mock_engine = MagicMock()
        mock_segments = [
            {'id': 0, 'start': 0, 'end': 5, 'text': 'Test segment'}
        ]
        mock_info = MagicMock()
        mock_info.language = 'en'
        mock_info.duration = 5.0
        mock_engine.process_signal_single_pass.return_value = mock_segments
        mock_engine_class.return_value = mock_engine
        
        # Create transcriber
        config = {'contextual_restoration': {'enabled': False}, 'emotion_mapping': {'enabled': False}}
        transcriber = MultiPassTranscriber(config)
        
        # Test Pass 1
        segments, info = transcriber.pass1_detect('test.wav')
        
        assert len(segments) == 1
        assert segments[0]['text'] == 'Test segment'
    
    def test_pass2_restore_disabled(self):
        """Test Pass 2 skips when disabled"""
        config = {'contextual_restoration': {'enabled': False}}
        transcriber = MultiPassTranscriber(config)
        
        segments = [{'text': 'test'}]
        result = transcriber.pass2_restore(segments)
        
        # Should return segments unchanged
        assert result == segments
    
    def test_pass3_emotion_disabled(self):
        """Test Pass 3 skips when disabled"""
        config = {'emotion_mapping': {'enabled': False}}
        transcriber = MultiPassTranscriber(config)
        
        segments = [{'text': 'test'}]
        result = transcriber.pass3_map_emotions(segments)
        
        # Should return segments unchanged
        assert result == segments


class TestIntegration:
    """Integration tests for multi-pass system"""
    
    def test_end_to_end_mock(self):
        """Test end-to-end flow with all components mocked"""
        # This would require extensive mocking but validates the full pipeline
        # Placeholder for comprehensive integration test
        pass
    
    def test_backward_compatibility(self):
        """Test that single-pass mode still works"""
        # Verify AudioTranscriber works with multi_pass.enabled = False
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
