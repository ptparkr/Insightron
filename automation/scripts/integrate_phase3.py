"""
Script to integrate Phase 3 features into gui.py
"""

# Read the original gui.py
with open('gui_backup.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find insertion points and make modifications
output = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # 1. Add import after settings_manager
    if 'from settings_manager import SettingsManager' in line:
        output.append(line)
        output.append('from realtime_transcriber import RealtimeTranscriber\n')
        i += 1
        continue
    
    # 2. Add state variables after self.transcriber = None
    if '        self.transcriber = None' in line and 'self.realtime_transcriber' not in lines[i+1]:
        output.append(line)
        output.append('        self.realtime_transcriber = None\n')
        output.append('        self.is_recording = False\n')
        i += 1
        continue
    
    # 3. Add Realtime tab
    if '        self.tab_batch = self.tab_view.add("Batch Mode")' in line:
        output.append(line)
        output.append('        self.tab_realtime = self.tab_view.add("Realtime")\n')
        i += 1
        continue
    
    # 4. Configure realtime tab color
    if '        self.tab_batch.configure(fg_color=self.COLORS' in line and i+1 < len(lines) and 'self.setup_single_file_tab' in lines[i+1]:
        output.append(line)
        output.append('        self.tab_realtime.configure(fg_color=self.COLORS[\'background\'])\n')
        output.append('        \n')
        i += 1
        continue
    
    # 5. Add setup_realtime_tab call
    if '        self.setup_batch_tab()' in line and i+1 < len(lines) and 'self.setup_settings_panel' in lines[i+1]:
        output.append(line)
        output.append('        self.setup_realtime_tab()\n')
        output.append('        \n')
        i += 1
        continue
    
    # 6. Add Phase 3 methods after setup_batch_tab
    if '        self.batch_transcribe_btn.pack(fill="x", padx=20, pady=(10, 20))' in line:
        output.append(line)
        # Check if next significant line is setup_settings_panel
        if i+1 < len(lines) and ('def setup_settings_panel' in lines[i+1] or (i+2 < len(lines) and 'def setup_settings_panel' in lines[i+2])):
            output.append('\n')
            output.append('    def setup_realtime_tab(self):\n')
            output.append('        """Realtime Transcription Tab"""\n')
            output.append('        rt_card = self.create_card(self.tab_realtime)\n')
            output.append('        rt_card.pack(fill="x", pady=20, padx=20)\n')
            output.append('        \n')
            output.append('        inner = ctk.CTkFrame(rt_card, fg_color="transparent")\n')
            output.append('        inner.pack(fill="x", padx=30, pady=30)\n')
            output.append('        \n')
            output.append('        icon = ctk.CTkLabel(inner, text="🎙️", font=(\'Segoe UI\', 48))\n')
            output.append('        icon.pack(pady=(0, 15))\n')
            output.append('        \n')
            output.append('        ctk.CTkLabel(\n')
            output.append('            inner, text="Select Microphone", font=(\'Segoe UI\', 14, \'bold\'),\n')
            output.append('            text_color=self.COLORS[\'text_secondary\']\n')
            output.append('        ).pack(pady=(0, 5))\n')
            output.append('        \n')
            output.append('        self.mic_var = ctk.StringVar(value="Loading...")\n')
            output.append('        self.mic_combo = ctk.CTkComboBox(\n')
            output.append('            inner, variable=self.mic_var, values=["Loading..."],\n')
            output.append('            font=(\'Segoe UI\', 14), width=300, height=40, corner_radius=8\n')
            output.append('        )\n')
            output.append('        self.mic_combo.pack(pady=(0, 20))\n')
            output.append('        \n')
            output.append('        ctk.CTkButton(\n')
            output.append('            inner, text="🔄 Refresh", command=self.refresh_microphones,\n')
            output.append('            width=80, height=24, font=(\'Segoe UI\', 11),\n')
            output.append('            fg_color="transparent", border_width=1,\n')
            output.append('            border_color=self.COLORS[\'border\']\n')
            output.append('        ).pack(pady=(0, 20))\n')
            output.append('        \n')
            output.append('        self.record_btn = ctk.CTkButton(\n')
            output.append('            self.tab_realtime, text="🔴 Start Recording",\n')
            output.append('            command=self.toggle_recording, font=(\'Segoe UI\', 18, \'bold\'),\n')
            output.append('            height=56, corner_radius=12, fg_color=self.COLORS[\'error\'],\n')
            output.append('            hover_color=\'#DC2626\'\n')
            output.append('        )\n')
            output.append('        self.record_btn.pack(fill="x", padx=20, pady=(10, 20))\n')
            output.append('        \n')
            output.append('        self.root.after(100, self.init_realtime)\n')
            output.append('\n')
            output.append('    def init_realtime(self):\n')
            output.append('        """Initialize realtime transcriber"""\n')
            output.append('        try:\n')
            output.append('            self.realtime_transcriber = RealtimeTranscriber()\n')
            output.append('            self.refresh_microphones()\n')
            output.append('        except Exception as e:\n')
            output.append('            logger.error(f"Failed to init realtime: {e}")\n')
            output.append('            self.mic_var.set("Error loading devices")\n')
            output.append('\n')
            output.append('    def refresh_microphones(self):\n')
            output.append('        """Refresh microphone list"""\n')
            output.append('        if not self.realtime_transcriber:\n')
            output.append('            return\n')
            output.append('        devices = self.realtime_transcriber.get_microphones()\n')
            output.append('        self.mic_devices = devices\n')
            output.append('        names = [d[\'name\'] for d in devices] or ["No microphones found"]\n')
            output.append('        self.mic_combo.configure(values=names)\n')
            output.append('        if names:\n')
            output.append('            self.mic_combo.set(names[0])\n')
            output.append('\n')
            output.append('    def toggle_recording(self):\n')
            output.append('        """Toggle recording"""\n')
            output.append('        if not self.is_recording:\n')
            output.append('            self.start_recording()\n')
            output.append('        else:\n')
            output.append('            self.stop_recording()\n')
            output.append('\n')
            output.append('    def start_recording(self):\n')
            output.append('        """Start recording"""\n')
            output.append('        try:\n')
            output.append('            name = self.mic_var.get()\n')
            output.append('            idx = -1\n')
            output.append('            for d in self.mic_devices:\n')
            output.append('                if d[\'name\'] == name:\n')
            output.append('                    idx = d[\'index\']\n')
            output.append('                    break\n')
            output.append('            \n')
            output.append('            self.is_recording = True\n')
            output.append('            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.COLORS[\'primary\'])\n')
            output.append('            self.tab_single.configure(state="disabled")\n')
            output.append('            self.tab_batch.configure(state="disabled")\n')
            output.append('            self.update_progress("🎙️ Listening...")\n')
            output.append('            self.update_results(f"--- Recording Started ({name}) ---")\n')
            output.append('            \n')
            output.append('            self.realtime_transcriber.model_size = self.model_var.get()\n')
            output.append('            lang = self.language_var.get().split(\' - \')[0]\n')
            output.append('            self.realtime_transcriber.language = lang\n')
            output.append('            self.realtime_transcriber.start_transcription(idx, self.on_realtime_text)\n')
            output.append('        except Exception as e:\n')
            output.append('            self.handle_error(e)\n')
            output.append('            self.stop_recording()\n')
            output.append('\n')
            output.append('    def stop_recording(self):\n')
            output.append('        """Stop recording"""\n')
            output.append('        self.is_recording = False\n')
            output.append('        self.record_btn.configure(text="🔴 Start Recording", fg_color=self.COLORS[\'error\'])\n')
            output.append('        if self.realtime_transcriber:\n')
            output.append('            self.realtime_transcriber.stop_transcription()\n')
            output.append('        self.update_progress("✅ Stopped")\n')
            output.append('        self.update_results("--- Recording Stopped ---")\n')
            output.append('        self.tab_single.configure(state="normal")\n')
            output.append('        self.tab_batch.configure(state="normal")\n')
            output.append('\n')
            output.append('    def on_realtime_text(self, text):\n')
            output.append('        """Callback for realtime text"""\n')
            output.append('        self.update_results(f"🗣️ {text}")\n')
        i += 1
        continue
    
    output.append(line)
    i += 1

# Write the modified gui.py
with open('gui.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print("Phase 3 integrated successfully!")
