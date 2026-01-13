"""
Remove unsupported 'state' parameter from tab configuration
"""

with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove tab state configuration lines from start_recording
content = content.replace(
    '''            self.is_recording = True
            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.COLORS['primary'])
            self.tab_single.configure(state="disabled")
            self.tab_batch.configure(state="disabled")
            self.update_progress("🎙️ Listening...")''',
    '''            self.is_recording = True
            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.COLORS['primary'])
            self.update_progress("🎙️ Listening...")'''
)

# Remove tab state configuration lines from stop_recording  
content = content.replace(
    '''        self.update_progress("✅ Stopped")
        self.tab_single.configure(state="normal")
        self.tab_batch.configure(state="normal")
        # Reset audio level bar''',
    '''        self.update_progress("✅ Stopped")
        # Reset audio level bar'''
)

with open('gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Tab state configuration lines removed!")
