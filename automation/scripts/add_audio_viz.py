"""
Script to add audio level visualization to gui.py
"""

# Read the current gui.py (which has Phase 3 features)
with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add audio level bar widget after the refresh button
old_refresh = '''        ).pack(pady=(0, 20))
        
        self.record_btn = ctk.CTkButton('''

new_refresh = '''        ).pack(pady=(0, 20))
        
        # Audio Level Indicator
        ctk.CTkLabel(
            inner, text="Audio Level", font=('Segoe UI', 12, 'bold'),
            text_color=self.COLORS['text_secondary']
        ).pack(pady=(10, 5))
        
        self.audio_level_bar = ctk.CTkProgressBar(
            inner, width=300, height=20,
            progress_color=self.COLORS['success']
        )
        self.audio_level_bar.pack(pady=(0, 20))
        self.audio_level_bar.set(0)
        
        self.record_btn = ctk.CTkButton('''

content = content.replace(old_refresh, new_refresh)

# Update start_transcription call to include audio level callback
old_start = '''            self.realtime_transcriber.start_transcription(idx, self.on_realtime_text)'''
new_start = '''            self.realtime_transcriber.start_transcription(idx, self.on_realtime_text, self.on_audio_level)'''

content = content.replace(old_start, new_start)

# Add audio level reset in stop_recording
old_stop = '''        self.tab_single.configure(state="normal")
        self.tab_batch.configure(state="normal")

    def on_realtime_text(self, text):'''

new_stop = '''        self.tab_single.configure(state="normal")
        self.tab_batch.configure(state="normal")
        # Reset audio level bar
        self.audio_level_bar.set(0)
        self.audio_level_bar.configure(progress_color=self.COLORS['success'])

    def on_realtime_text(self, text):'''

content = content.replace(old_stop, new_stop)

# Add audio level callback methods after on_realtime_text
old_text_callback = '''    def on_realtime_text(self, text):
        """Callback for realtime text"""
        self.update_results(f"🗣️ {text}")

    def setup_settings_panel(self):'''

new_text_callback = '''    def on_realtime_text(self, text):
        """Callback for realtime text"""
        self.update_results(f"🗣️ {text}")

    def on_audio_level(self, level):
        """Update audio level indicator"""
        self.root.after(0, lambda: self._update_audio_level(level))

    def _update_audio_level(self, level):
        """Update progress bar with color coding"""
        self.audio_level_bar.set(level)
        
        # Color coding: green (0-0.5), yellow (0.5-0.8), red (0.8-1.0)
        if level < 0.5:
            color = self.COLORS['success']  # Green
        elif level < 0.8:
            color = '#F59E0B'  # Yellow/Orange
        else:
            color = self.COLORS['error']  # Red
        
        self.audio_level_bar.configure(progress_color=color)

    def setup_settings_panel(self):'''

content = content.replace(old_text_callback, new_text_callback)

# Write the updated gui.py
with open('gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Audio visualization added successfully!")
