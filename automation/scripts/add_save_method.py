"""Add save_recording method to realtime_transcriber.py"""

with open('realtime_transcriber.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the save_recording method at the end of the class
save_method = '''
    def save_recording(self, output_path: str):
        """Save the recorded audio to WAV file"""
        import wave
        
        if len(self.full_audio_buffer) == 0:
            logger.warning("No audio to save")
            return None
        
        try:
            # Convert float32 to 16-bit PCM
            audio_int16 = np.int16(self.full_audio_buffer * 32767)
            
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            logger.info(f"Audio saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return None
'''

# Append to end of file
content += save_method

with open('realtime_transcriber.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("save_recording method added!")
