"""
Script to fix tab errors and add audio save feature
"""

with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove tab state changes in start_recording
content = content.replace(
    '''            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.COLORS['primary'])
            self.tab_single.configure(state="disabled")
            self.tab_batch.configure(state="disabled")
            self.update_progress("🎙️ Listening...")
            self.update_results(f"--- Recording Started ({name}) ---")''',
    '''            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.COLORS['primary'])
            self.update_progress("🎙️ Listening...")
            self.update_results(f"--- Recording Started ({name}) ---")
            self.realtime_transcript = []  # Reset transcript tracking'''
)

# 2. Replace entire stop_recording method with audio save
old_stop = '''    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.record_btn.configure(text="🔴 Start Recording", fg_color=self.COLORS['error'])
        if self.realtime_transcriber:
           self.realtime_transcriber.stop_transcription()
        self.update_progress("✅ Stopped")
        self.update_results("--- Recording Stopped ---")
        self.tab_single.configure(state="normal")
        self.tab_batch.configure(state="normal")
        # Reset audio level bar
        self.audio_level_bar.set(0)
        self.audio_level_bar.configure(progress_color=self.COLORS['success'])'''

new_stop = '''    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.record_btn.configure(text="🔴 Start Recording", fg_color=self.COLORS['error'])
        
        if self.realtime_transcriber:
            # Save audio and create note
            from datetime import datetime
            timestamp = datetime.now().strftime("%H-%M_%d-%m-%y")
            
            # Create recordings folder
            recordings_dir = TRANSCRIPTION_FOLDER / "Recordings"
            recordings_dir.mkdir(exist_ok=True)
            
            # Save WAV file
            audio_file = recordings_dir / f"{timestamp}.wav"
            saved_path = self.realtime_transcriber.save_recording(str(audio_file))
            
            if saved_path:
                self.update_results(f"💾 Audio saved: {audio_file.name}")
                
                # Create Obsidian note with transcription
                if hasattr(self, 'realtime_transcript') and self.realtime_transcript:
                    note_path = TRANSCRIPTION_FOLDER / f"{timestamp}.md"
                    transcript = "\\n\\n".join(self.realtime_transcript)
                    
                    with open(note_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Realtime Transcription\\n\\n")
                        f.write(f"**Date**: {timestamp.replace('_', ' ').replace('-', ':')}\\n\\n")
                        f.write(f"**Audio**: [[Recordings/{audio_file.name}]]\\n\\n")
                        f.write(f"## Transcription\\n\\n{transcript}\\n")
                    
                    self.update_results(f"📝 Note created: {note_path.name}")
            
            self.realtime_transcriber.stop_transcription()
        
        self.update_progress("✅ Stopped")
        self.update_results("--- Recording Stopped ---")
        # Reset audio level bar
        self.audio_level_bar.set(0)
        self.audio_level_bar.configure(progress_color=self.COLORS['success'])'''

content = content.replace(old_stop, new_stop)

# 3. Update on_realtime_text to track transcriptions
content = content.replace(
    '''    def on_realtime_text(self, text):
        """Callback for realtime text"""
        self.update_results(f"🗣️ {text}")''',
    '''    def on_realtime_text(self, text):
        """Callback for realtime text"""
        if not hasattr(self, 'realtime_transcript'):
            self.realtime_transcript = []
        self.realtime_transcript.append(text)
        self.update_results(f"🗣️ {text}")'''
)

with open('gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Tab fixes and audio save feature added!")
