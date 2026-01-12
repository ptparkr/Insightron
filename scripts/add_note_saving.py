"""
Add note-saving functionality to gui.py
"""

with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports to include RECORDINGS_FOLDER and create_realtime_note
content = content.replace(
    'from config import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, TRANSCRIPTION_FOLDER',
    'from config import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, TRANSCRIPTION_FOLDER, RECORDINGS_FOLDER'
)

content = content.replace(
    'from realtime_transcriber import RealtimeTranscriber',
    'from realtime_transcriber import RealtimeTranscriber\nfrom utils import create_realtime_note'
)

# 2. Replace the stop_recording method
old_stop_recording = '''    def stop_recording(self):
        \"\"\"Stop recording\"\"\"
        self.is_recording = False
        self.record_btn.configure(text=\"🔴 Start Recording\", fg_color=self.COLORS['error'])
        if self.realtime_transcriber:
            self.realtime_transcriber.stop_transcription()
        self.update_progress(\"✅ Stopped\")
        self.update_results(\"---Recording Stopped ---\")
        self.tab_single.configure(state=\"normal\")
        self.tab_batch.configure(state=\"normal\")
        # Reset audio level bar
        self.audio_level_bar.set(0)
        self.audio_level_bar.configure(progress_color=self.COLORS['success'])'''

new_stop_recording = '''    def stop_recording(self):
        \"\"\"Stop recording\"\"\"
        self.is_recording = False
        self.record_btn.configure(text=\"🔴 Start Recording\", fg_color=self.COLORS['error'])
        if self.realtime_transcriber:
            self.realtime_transcriber.stop_transcription()
        
        # Save recording to Recordings folder
        try:
            timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")
            filename = f\"recording_{timestamp}.wav\"
            save_path = RECORDINGS_FOLDER / filename
            
            saved_file = self.realtime_transcriber.save_recording(str(save_path))
            if saved_file:
                self.update_results(f\"⏹ Stopped recording - Saved to {filename}\")
                
                # Save transcription note
                try:
                    data = self.realtime_transcriber.get_transcription_data()
                    if data['text']:
                        note_filename = f\"recording_{timestamp}\"
                        
                        # Calculate duration
                        duration_seconds = 0
                        if self.realtime_transcriber.full_audio_buffer.size > 0:
                            duration_seconds = len(self.realtime_transcriber.full_audio_buffer) / self.realtime_transcriber.sample_rate
                        
                        minutes = int(duration_seconds // 60)
                        seconds = int(duration_seconds % 60)
                        duration_str = f\"{minutes}:{seconds:02d}\"
                        
                        note_content = create_realtime_note(
                            filename=note_filename,
                            text=data['text'],
                            date=datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\"),
                            duration=duration_str,
                            file_size_mb=save_path.stat().st_size / (1024 * 1024) if save_path.exists() else 0,
                            model=self.realtime_transcriber.model_size,
                            language=data['language'],
                            formatting_style=self.formatting_var.get(),
                            duration_seconds=duration_seconds,
                            segments=data['segments'],
                        )
                        
                        note_path = TRANSCRIPTION_FOLDER / f\"{note_filename}.md\"
                        note_path.write_text(note_content, encoding='utf-8')
                        self.update_results(f\"📝 Saved note to Notes: {note_filename}.md\")
                        
                except Exception as e:
                    logger.error(f\"Failed to save note: {e}\")
                    self.update_results(f\"❌ Failed to save note: {e}\")
                    
            else:
                self.update_results(\"⏹ Stopped recording - No audio to save\")
        except Exception as e:
            logger.error(f\"Failed to save recording: {e}\")
            self.update_results(f\"⏹ Stopped recording - Save failed: {e}\")
        
        self.update_progress(\"✅ Stopped\")
        self.tab_single.configure(state=\"normal\")
        self.tab_batch.configure(state=\"normal\")
        # Reset audio level bar
        self.audio_level_bar.set(0)
        self.audio_level_bar.configure(progress_color=self.COLORS['success'])'''

content = content.replace(old_stop_recording, new_stop_recording)

with open('gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Note-saving functionality added!")
