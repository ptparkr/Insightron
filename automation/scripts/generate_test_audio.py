import wave
import math
import struct
import os

def generate_sine_wave(filename, duration=10, frequency=440, sample_rate=16000):
    """Generate a sine wave audio file."""
    print(f"Generating {duration}s audio file: {filename}")
    
    n_frames = int(duration * sample_rate)
    
    try:
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            for i in range(n_frames):
                value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
                data = struct.pack('<h', value)
                wav_file.writeframesraw(data)
        
        print(f"Successfully created {filename}")
        return True
    except Exception as e:
        print(f"Error creating audio file: {e}")
        return False

if __name__ == "__main__":
    generate_sine_wave("benchmark_test.wav")
