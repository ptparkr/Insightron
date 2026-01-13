#!/usr/bin/env python3
"""
Performance Benchmark Suite for Insightron
Measures performance metrics and provides optimization recommendations.
"""

import time
import psutil
import sys
import os
from pathlib import Path
import tempfile
import logging
from typing import Dict, List, Tuple, Any
import json
import shutil
import numpy as np
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.transcription.text_formatter import TextFormatter, format_transcript
from insightron.core.utils import create_markdown
from insightron.core.model_manager import ModelManager
from insightron.services.batch.batch_processor import BatchTranscriber
from insightron.services.realtime.realtime_transcriber import RealtimeTranscriber

# Configure logging
logging.basicConfig(level=logging.WARNING)

class PerformanceBenchmark:
    """Comprehensive performance benchmarking for Insightron components."""
    
    def __init__(self, baseline_file: str = None):
        self.results = {}
        self.system_info = self._get_system_info()
        self.baseline = self._load_baseline(baseline_file) if baseline_file else None
        self.test_audio_path = Path("benchmark_test.wav")
        
        # Ensure test audio exists
        if not self.test_audio_path.exists():
            print("⚠️ Test audio not found. Generating...")
            import generate_test_audio
            generate_test_audio.generate_sine_wave(str(self.test_audio_path))
    
    def _get_system_info(self) -> Dict:
        """Get system information for context."""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'python_version': sys.version,
            'platform': sys.platform
        }

    def _load_baseline(self, filename: str) -> Dict:
        """Load baseline results for comparison."""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load baseline file {filename}: {e}")
            return None
    
    def benchmark_text_formatter(self) -> Dict:
        """Benchmark text formatter performance."""
        print("🧪 Benchmarking Text Formatter...")
        
        formatter = TextFormatter()
        
        # Test data of varying sizes
        test_cases = [
            ("Small text", "Hello world this is a test sentence."),
            ("Medium text", "Hello world this is a test sentence. " * 50),
            ("Large text", "Hello world this is a test sentence. " * 500),
            ("Very large text", "Hello world this is a test sentence. " * 2000)
        ]
        
        results = {}
        
        for name, text in test_cases:
            print(f"  Testing {name} ({len(text)} chars)...")
            
            # Test clean_text
            start_time = time.time()
            cleaned = formatter.clean_text(text)
            clean_time = time.time() - start_time
            
            # Test format_text
            start_time = time.time()
            formatted = formatter.format_text(text)
            format_time = time.time() - start_time
            
            # Test custom structure
            start_time = time.time()
            custom = formatter.format_with_custom_structure(text, 3)
            custom_time = time.time() - start_time
            
            results[name] = {
                'text_length': len(text),
                'clean_time': clean_time,
                'format_time': format_time,
                'custom_time': custom_time,
                'total_time': clean_time + format_time + custom_time,
                'chars_per_second': len(text) / (clean_time + format_time + custom_time) if (clean_time + format_time + custom_time) > 0 else 0
            }
        
        return results
    
    def benchmark_markdown_creation(self) -> Dict:
        """Benchmark markdown creation performance."""
        print("🧪 Benchmarking Markdown Creation...")
        
        test_cases = [
            ("Small transcript", "This is a short transcript."),
            ("Medium transcript", "This is a medium length transcript. " * 100),
            ("Large transcript", "This is a large transcript with many sentences. " * 1000),
            ("Very large transcript", "This is a very large transcript with many sentences. " * 5000)
        ]
        
        results = {}
        
        for name, text in test_cases:
            print(f"  Testing {name} ({len(text)} chars)...")
            
            start_time = time.time()
            markdown = create_markdown(
                filename="benchmark_test",
                text=text,
                date="2024-01-01 12:00:00",
                duration="10:00",
                model="medium",
                duration_seconds=600.0,
                file_size_mb=5.0,
                language="en",
                segments=[{'start': 0, 'end': 600, 'text': text}]
            )
            end_time = time.time()
            
            results[name] = {
                'text_length': len(text),
                'markdown_length': len(markdown),
                'creation_time': end_time - start_time,
                'chars_per_second': len(text) / (end_time - start_time) if (end_time - start_time) > 0 else 0
            }
        
        return results
    
    def benchmark_memory_usage(self) -> Dict:
        """Benchmark memory usage patterns."""
        print("🧪 Benchmarking Memory Usage...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024**2)  # MB
        
        # Test text formatter memory usage
        formatter = TextFormatter()
        large_text = "This is a test sentence. " * 10000
        
        memory_before = process.memory_info().rss / (1024**2)
        formatted_text = formatter.format_text(large_text)
        memory_after = process.memory_info().rss / (1024**2)
        
        formatter_memory = memory_after - memory_before
        
        # Test markdown creation memory usage
        memory_before = process.memory_info().rss / (1024**2)
        markdown = create_markdown(
            filename="memory_test",
            text=large_text,
            date="2024-01-01 12:00:00",
            duration="10:00",
            model="medium",
            duration_seconds=600.0,
            file_size_mb=5.0,
            language="en"
        )
        memory_after = process.memory_info().rss / (1024**2)
        
        markdown_memory = memory_after - memory_before
        
        return {
            'initial_memory_mb': initial_memory,
            'formatter_memory_mb': formatter_memory,
            'markdown_memory_mb': markdown_memory,
            'total_memory_mb': memory_after - initial_memory
        }

    def benchmark_single_file_transcription(self) -> Dict:
        """Benchmark single-file transcription performance."""
        print("🧪 Benchmarking Single-File Transcription...")
        
        if not self.test_audio_path.exists():
            print("  Skipping: Test audio not found")
            return {}

        # Measure model load time
        model_manager = ModelManager()
        model_name = model_manager.model_size
        print(f"  Loading model '{model_name}'...")
        
        start_time = time.time()
        # Ensure reload for benchmark
        model_manager._model = None 
        model = model_manager.load_model()
        load_time = time.time() - start_time
        
        # Measure transcription time
        print(f"  Transcribing {self.test_audio_path}...")
        start_time = time.time()
        # transcribe uses load_model internally, so it will use the one we just loaded
        result = model_manager.transcribe(str(self.test_audio_path))
        transcribe_time = time.time() - start_time
        
        # Measure cached load time (should be instant)
        print("  Testing cached model access...")
        start_time = time.time()
        _ = model_manager.load_model()
        cached_load_time = time.time() - start_time
        
        return {
            'model': model_name,
            'load_time_seconds': load_time,
            'cached_load_time_seconds': cached_load_time,
            'transcription_time_seconds': transcribe_time,
            'audio_duration_seconds': 10.0, # Known from generation
            'real_time_factor': transcribe_time / 10.0
        }

    def benchmark_batch_processing(self) -> Dict:
        """Benchmark batch processing performance."""
        print("🧪 Benchmarking Batch Processing...")
        
        if not self.test_audio_path.exists():
            print("  Skipping: Test audio not found")
            return {}
            
        # Create temporary directory with multiple copies of test audio
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            num_files = 4
            files = []
            
            print(f"  Preparing {num_files} test files...")
            for i in range(num_files):
                dest = temp_path / f"test_{i}.wav"
                shutil.copy(self.test_audio_path, dest)
                files.append(str(dest))
            
            # Benchmark sequential (simulated by 1 worker)
            # Note: BatchProcessor defaults to cpu_count, we'll assume it uses multiprocessing
            
            print(f"  Running batch processing on {num_files} files...")
            processor = BatchTranscriber()
            
            start_time = time.time()
            results = processor.transcribe_batch(files, formatting_style="auto")
            total_time = time.time() - start_time
            
            successful = len(results['successful'])
            failed = len(results['failed'])
            
            return {
                'file_count': num_files,
                'total_time_seconds': total_time,
                'avg_time_per_file': total_time / num_files,
                'successful': successful,
                'failed': failed,
                'throughput_files_per_min': (num_files / total_time) * 60
            }

    def benchmark_realtime_simulation(self) -> Dict:
        """Benchmark real-time transcription components."""
        print("🧪 Benchmarking Real-Time Components...")
        
        # Test buffer performance
        from collections import deque
        import numpy as np
        
        buffer_size = 16000 * 30 # 30 seconds
        audio_buffer = deque(maxlen=buffer_size)
        chunk_size = 16000 # 1 second
        
        print("  Testing buffer write performance...")
        start_time = time.time()
        # Simulate writing 60 seconds of audio
        for _ in range(60):
            chunk = np.random.rand(chunk_size).astype(np.float32)
            audio_buffer.extend(chunk)
        write_time = time.time() - start_time
        
        print("  Testing buffer read performance...")
        start_time = time.time()
        # Read snapshot
        _ = np.array(audio_buffer)
        read_time = time.time() - start_time
        
        return {
            'buffer_write_60s_time': write_time,
            'buffer_read_snapshot_time': read_time,
            'latency_overhead_ms': (write_time / 60 + read_time) * 1000
        }
    
    def run_all_benchmarks(self) -> Dict:
        """Run all benchmarks and return comprehensive results."""
        print("🚀 Starting Insightron Performance Benchmarks")
        print("=" * 60)
        
        all_results = {
            'system_info': self.system_info,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'text_formatter': self.benchmark_text_formatter(),
            'markdown_creation': self.benchmark_markdown_creation(),
            'memory_usage': self.benchmark_memory_usage(),
            'single_file': self.benchmark_single_file_transcription(),
            'batch_processing': self.benchmark_batch_processing(),
            'realtime_simulation': self.benchmark_realtime_simulation()
        }
        
        self.results = all_results
        return all_results
    
    def print_summary(self):
        """Print a summary of benchmark results."""
        if not self.results:
            print("No benchmark results available. Run benchmarks first.")
            return
        
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        
        # System info
        print(f"🖥️  System: {self.system_info['cpu_count']} cores, {self.system_info['memory_gb']}GB RAM")
        
        # Single File
        if 'single_file' in self.results and self.results['single_file']:
            sf = self.results['single_file']
            print(f"\n🎧 Single File Transcription ({sf.get('model', 'unknown')}):")
            print(f"  Load Time: {sf['load_time_seconds']:.2f}s")
            print(f"  Cached Load: {sf['cached_load_time_seconds']:.4f}s")
            print(f"  RTF (Real Time Factor): {sf['real_time_factor']:.2f}x")
            
            if self.baseline and 'single_file' in self.baseline:
                base_rtf = self.baseline['single_file'].get('real_time_factor')
                if base_rtf:
                    imp = (base_rtf - sf['real_time_factor']) / base_rtf * 100
                    print(f"  Improvement vs Baseline: {imp:+.1f}%")

        # Batch Processing
        if 'batch_processing' in self.results and self.results['batch_processing']:
            bp = self.results['batch_processing']
            print(f"\n📦 Batch Processing:")
            print(f"  Throughput: {bp['throughput_files_per_min']:.1f} files/min")
            print(f"  Avg Time/File: {bp['avg_time_per_file']:.2f}s")

        # Realtime
        if 'realtime_simulation' in self.results:
            rt = self.results['realtime_simulation']
            print(f"\n🔴 Real-time Latency Overhead:")
            print(f"  Buffer Overhead: {rt['latency_overhead_ms']:.3f}ms")

        # Memory usage
        print(f"\n💾 Memory Usage:")
        print(f"  Total Overhead: {self.results['memory_usage']['total_memory_mb']:.1f} MB")
        
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to JSON file."""
        if not self.results:
            print("No benchmark results to save.")
            return
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📁 Results saved to: {filename}")

def main():
    """Main benchmark execution function."""
    parser = argparse.ArgumentParser(description="Insightron Benchmark Suite")
    parser.add_argument("--baseline", help="Path to baseline results JSON for comparison")
    args = parser.parse_args()

    print("🎤 Insightron Performance Benchmark Suite")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark(baseline_file=args.baseline)
    
    try:
        # Run all benchmarks
        results = benchmark.run_all_benchmarks()
        
        # Print summary
        benchmark.print_summary()
        
        # Save results
        benchmark.save_results()
        
        print(f"\n✅ Benchmark completed successfully!")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
