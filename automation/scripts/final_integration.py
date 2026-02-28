"""
FINAL integration script - adds Phase 3 + audio viz with correct setup call
"""

with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add realtime transcriber import
content = content.replace(
    'from settings_manager import SettingsManager',
    'from settings_manager import SettingsManager\nfrom realtime_transcriber import RealtimeTranscriber'
)

# 2. Add state variables
content = content.replace(
    '        self.transcriber = None',
    '        self.transcriber = None\n        self.realtime_transcriber = None\n        self.is_recording = False'
)

# 3. Add Realtime tab
content = content.replace(
    '        self.tab_batch = self.tab_view.add("Batch Mode")',
    '        self.tab_batch = self.tab_view.add("Batch Mode")\n        self.tab_realtime = self.tab_view.add("Realtime")'
)

# 4. Configure realtime tab color AND add setup call
content = content.replace(
    '''        # Configure tab colors
        self.tab_single.configure(fg_color=self.COLORS['background'])
        self.tab_batch.configure(fg_color=self.COLORS['background'])
        
        self.setup_single_file_tab()
        self.setup_batch_tab()''',
    '''        # Configure tab colors
        self.tab_single.configure(fg_color=self.COLORS['background'])
        self.tab_batch.configure(fg_color=self.COLORS['background'])
        self.tab_realtime.configure(fg_color=self.COLORS['background'])
        
        self.setup_single_file_tab()
        self.setup_batch_tab()
        self.setup_realtime_tab()'''
)

# 5. Add entire setup_realtime_tab method BEFORE setup_settings_panel
setup_realtime = '''
    def setup_realtime_tab(self):
        """Realtime Transcription Tab"""
        rt_card = self.create_card(self.tab_realtime)
        rt_card.pack(fill="x", pady=20, padx=20)
        
        inner = ctk.CTkFrame(rt_card, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=30)
        
        icon = ctk.CTkLabel(inner, text="🎙️", font=('Segoe UI', 48))
        icon.pack(pady=(0, 15))
        
        ctk.CTkLabel(
            inner, text="Select Microphone", font=('Segoe UI', 14, 'bold'),
            text_color=self.COLORS['text_secondary']
        ).pack(pady=(0, 5))
        
        self.mic_var = ctk.StringVar(value="Loading...")
        self.mic_combo = ctk.CTkComboBox(
            inner, variable=self.mic_var, values=["Loading..."],
            font=('Segoe UI', 14), width=300, height=40, corner_radius=8
        )
        self.mic_combo.pack(pady=(0, 20))
        
        ctk.CTkButton(
            inner, text="🔄 Refresh", command=self.refresh_microphones,
            width=80, height=24, font=('Segoe UI', 11),
            fg_color="transparent", border_width=1,
            border_color=self.COLORS['border']
        ).pack(pady=(0, 20))
        
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
        
        self.record_btn = ctk.CTkButton(
            self.tab_realtime, text="🔴 Start Recording",
            command=self.toggle_recording, font=('Segoe UI', 18, 'bold'),
            height=56, corner_radius=12, fg_color=self.COLORS['error'],
            hover_color='#DC2626'
        )
        self.record_btn.pack(fill="x", padx=20, pady=(10, 20))
        
        self.root.after(100, self.init_realtime)

    def init_realtime(self):
        """Initialize realtime transcriber"""
        try:
            self.realtime_transcriber = RealtimeTranscriber()
            self.refresh_microphones()
        except Exception as e:
            logger.error(f"Failed to init realtime: {e}")
            self.mic_var.set("Error loading devices")

    def refresh_microphones(self):
        """Refresh microphone list"""
        if not self.realtime_transcriber:
            return
        devices = self.realtime_transcriber.get_microphones()
        self.mic_devices = devices
        names = [d['name'] for d in devices] or ["No microphones found"]
        self.mic_combo.configure(values=names)
        if names:
            self.mic_combo.set(names[0])

    def toggle_recording(self):
        """Toggle recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording"""
        try:
            name = self.mic_var.get()
            idx = -1
            for d in self.mic_devices:
                if d['name'] == name:
                    idx = d['index']
                    break
            
            self.is_recording = True
            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.COLORS['primary'])
            self.tab_single.configure(state="disabled")
            self.tab_batch.configure(state="disabled")
            self.update_progress("🎙️ Listening...")
            self.update_results(f"--- Recording Started ({name}) ---")
            
            self.realtime_transcriber.model_size = self.model_var.get()
            lang = self.language_var.get().split(' - ')[0]
            self.realtime_transcriber.language = lang
            self.realtime_transcriber.start_transcription(idx, self.on_realtime_text, self.on_audio_level)
        except Exception as e:
            self.handle_error(e)
            self.stop_recording()

    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.record_btn.configure(text="🔴 Start Recording", fg_color=self.COLORS['error'])
        if self.realtime_transcriber:
            self.realtime_transcriber.stop_transcription()
        self.update_progress("✅ Stopped")
        self.update_results("---Recording Stopped ---")
        self.tab_single.configure(state="normal")
        self.tab_batch.configure(state="normal")
        # Reset audio level bar
        self.audio_level_bar.set(0)
        self.audio_level_bar.configure(progress_color=self.COLORS['success'])

    def on_realtime_text(self, text):
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

'''

content = content.replace(
    '    def setup_settings_panel(self):',
    setup_realtime + '    def setup_settings_panel(self):'
)

with open('gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Complete Phase 3 with audio viz integrated!")
