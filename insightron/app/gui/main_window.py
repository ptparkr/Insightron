"""
Main GUI Window for Insightron.

Modern, modular GUI application using component-based architecture.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from insightron.ui.components import Header, SettingsPanel, ProgressPanel, ResultsPanel, FileSelector
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.ui.themes.design_tokens import LayoutMode, SPACING
from insightron.ui.responsive import ResponsiveManager
from insightron.core.config import (
    APP_VERSION,
    TRANSCRIPTION_FOLDER,
    RECORDINGS_FOLDER,
    WHISPER_MODEL,
    DEFAULT_LANGUAGE
)
from insightron.core.settings_manager import SettingsManager
from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.batch.batch_processor import batch_transcribe_files
from insightron.services.realtime.realtime_transcriber import RealtimeTranscriber
from insightron.core.utils import create_realtime_note

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightronGUI:
    """
    Modern GUI application for Insightron.
    
    Features:
    - Component-based architecture
    - Modular UI components
    - Clean separation of concerns
    - Professional appearance
    """
    
    def __init__(self, root: ctk.CTk):
        """
        Initialize the Insightron GUI application.
        
        Args:
            root: CustomTkinter root window
        """
        self.root = root
        self.root.title(f"Insightron v{APP_VERSION}")
        
        # Responsive window sizing
        self.root.minsize(520, 600)  # Minimum usable size
        self.root.geometry("1100x900")  # Default size
        
        # CRITICAL: Configure root window for expansion chain
        # This ensures the root can expand and fill the screen
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Initialize managers
        self.settings_manager = SettingsManager()
        self.theme = ThemeManager.get_theme()
        
        # Application state
        self.selected_file: Optional[str] = None
        self.selected_batch_files: list = []
        self.is_transcribing = False
        self.is_recording = False
        self.realtime_transcriber: Optional[RealtimeTranscriber] = None
        
        # Initialize Status Bar early so it's available for _setup_ui
        self.status_bar = ctk.CTkLabel(
            self.root,
            text="Initializing GUI...",
            fg_color=self.theme.background,
            text_color=self.theme.text_secondary,
            height=25,
            font=('Segoe UI', 10)
        )
        self.status_bar.grid(row=1, column=0, sticky="ew")
        self.root.grid_rowconfigure(1, weight=0)
        
        # Setup UI
        self._setup_responsive()
        self._setup_ui()
        self._center_window()
        self._load_settings()
        
        # Start asynchronous service initialization
        self.root.after(100, self._init_services_async)
        
        logger.info("Insightron GUI initialized")
    
    def _init_services_async(self):
        """Initialize heavy services in a background thread."""
        def run_init():
            try:
                # Thread-safe UI updates using root.after
                self.root.after(0, lambda: self.results_panel.append("🚀 Initializing AI engines..."))
                self.root.after(0, lambda: self.progress_panel.update_status("🔄 Loading Model Manager..."))
                
                # Pre-load ModelManager (this can be slow)
                from insightron.core.model_manager import ModelManager
                model_manager = ModelManager()
                
                self.root.after(0, lambda: self.progress_panel.update_status("🔄 Initializing Realtime Engine..."))
                # Re-run refresh mics and init internal state
                self.root.after(0, self._init_realtime)
                
                self.root.after(0, lambda: self.progress_panel.update_status("✅ Systems Ready"))
                self.root.after(0, lambda: self.results_panel.append("✅ All AI systems loaded and ready."))
                self.root.after(0, lambda: self.status_bar.configure(text="Systems Ready"))
                logger.info("Async service initialization complete")
            except Exception as e:
                logger.error(f"Async init failed: {e}")
                self.root.after(0, lambda: self.results_panel.append(f"❌ Failed to initialize some services: {e}"))
                self.root.after(0, lambda: self.progress_panel.update_status("⚠️ System Warning"))

        thread = threading.Thread(target=run_init, daemon=True)
        thread.start()
        logger.info("Async init thread started")
    
    def _setup_responsive(self):
        """Initialize responsive layout management."""
        self.responsive = ResponsiveManager(self.root)
        self.responsive.subscribe(self._on_layout_change)
        self._current_layout_mode = LayoutMode.STANDARD
        
        # Bind resize handler for dynamic padding updates
        self.root.bind("<Configure>", self._on_window_resize)
    
    def _on_window_resize(self, event=None):
        """Handle window resize events to dynamically update grid padding and max-width centering."""
        # Only process root window resize events
        if event and event.widget != self.root:
            return
        
        if hasattr(self, 'content'):
            try:
                pad_md = self.responsive.get_spacing('md')
                pad_sm = self.responsive.get_spacing('sm')
                max_content_width = 1200
                
                current_width = self.root.winfo_width()
                
                # Apply max-width centering
                if current_width > max_content_width + (pad_md * 2):
                    side_pad = (current_width - max_content_width) // 2
                    self.content.grid_configure(padx=side_pad, pady=pad_md)
                    self.content.configure(width=max_content_width)
                else:
                    self.content.grid_configure(padx=pad_md, pady=pad_md)
                    self.content.configure(width=0)
                
                # Update padding for all grid children
                if hasattr(self, 'header_component'):
                    self.header_component.get_widget().grid_configure(pady=(0, pad_md))
                if hasattr(self, 'tab_view'):
                    self.tab_view.grid_configure(pady=(0, pad_md))
                if hasattr(self, 'config_container'):
                    self.config_container.grid_configure(pady=(0, pad_md))
                if hasattr(self, 'output_container'):
                    self.output_container.grid_configure(pady=(0, pad_sm))
            except Exception as e:
                logger.debug(f"Resize handler error (safe during init): {e}")
    
    def _on_layout_change(self, mode: LayoutMode):
        """Handle layout mode changes from ResponsiveManager."""
        if mode == self._current_layout_mode:
            return
        
        self._current_layout_mode = mode
        ThemeManager.set_layout_mode(mode)
        
        # Trigger resize handler to update spacing and max-width
        self._on_window_resize()
        logger.debug(f"Layout mode changed to: {mode.name}")
    
    def _setup_ui(self):
        """Setup the main UI components with responsive spacing."""
        # Get spacing from responsive manager so padding can adapt
        # to both width and height (container-query style).
        pad_lg = self.responsive.get_spacing('lg')
        pad_md = self.responsive.get_spacing('md')
        pad_sm = self.responsive.get_spacing('sm')
        
        # MASTER SCROLLABLE CONTAINER: Wrap entire app in scrollable frame
        # This ensures if content is too tall, user can scroll to see Output Log
        self.scrollable_container = ctk.CTkScrollableFrame(
            self.root,
            fg_color=self.theme.background,
            border_width=0,  # Seamless look - no border
        )
        # CRITICAL: Configure scrollable container to expand fully
        self.scrollable_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.scrollable_container.grid_columnconfigure(0, weight=1)
        # For a scrollable frame, we don't usually want to weight the inner row
        # unless we want the content to be forced to fill the canvas.
        # We'll leave it at weight 0 to allow natural height expansion.
        
        # INNER CONTENT WRAPPER: Centers content with max-width constraint
        self.content_wrapper = ctk.CTkFrame(
            self.scrollable_container,
            fg_color=self.theme.background,
            border_width=0,
        )
        self.content_wrapper.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.content_wrapper.grid_columnconfigure(0, weight=1)
        logger.info("Content wrapper initialized")

        # Content container
        self.content = ctk.CTkFrame(
            self.content_wrapper,
            fg_color=self.theme.background,
            border_width=0,
        )
        # CRITICAL: Use nsew to allow content to fill wrapper correctly
        self.content.grid(row=0, column=0, sticky="nsew", padx=pad_md, pady=pad_md)
        
        # Configure CSS-grid-like macro layout within content container:
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=0)
        self.content.grid_rowconfigure(1, weight=0)
        self.content.grid_rowconfigure(2, weight=0)
        self.content.grid_rowconfigure(3, weight=1, minsize=400) 
        
        # 1. Output Log Panel Container (Initialize early for error logging)
        self.output_container = ctk.CTkFrame(
            self.content, 
            fg_color=self.theme.surface,
            corner_radius=ThemeManager.get_radius('lg')
        )
        self.output_container.grid(
            row=3, column=0, sticky="nsew", 
            pady=(0, 0), padx=pad_lg
        )
        self.output_container.grid_columnconfigure(0, weight=1)
        self.output_container.grid_rowconfigure(0, weight=1)
        
        self.results_panel = ResultsPanel(
            self.output_container,
            responsive_manager=self.responsive
        )
        self.results_panel.get_widget().grid(row=0, column=0, sticky="nsew", padx=pad_md, pady=pad_md)
        
        self.progress_panel = ProgressPanel(
            self.results_panel.progress_container,
            responsive_manager=self.responsive
        )
        self.progress_panel.get_widget().grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        logger.info("Output and Progress panels initialized")
        
        # 2. Header
        self.header_component = Header(self.content, responsive_manager=self.responsive)
        self.header_component.get_widget().grid(
            row=0, column=0, sticky="ew", pady=(0, pad_md)
        )
        logger.info("Header gridded")
        
        # 3. Tab View (Row 1)
        self.tab_view = ctk.CTkTabview(
            self.content,
            corner_radius=ThemeManager.get_radius('lg'),
            fg_color=self.theme.background,
            segmented_button_fg_color=self.theme.surface_light,
            segmented_button_selected_color=self.theme.primary,
            segmented_button_selected_hover_color=self.theme.primary_hover,
            text_color=self.theme.text_secondary,
            segmented_button_unselected_hover_color=self.theme.border,
            border_width=0,
        )
        self.tab_view.grid(row=1, column=0, sticky="ew", pady=(0, pad_md), padx=0)
        
        try:
            self.tab_single = self.tab_view.add("Single File")
            self.tab_batch = self.tab_view.add("Batch Mode")
            self.tab_realtime = self.tab_view.add("Realtime")
            
            self._setup_single_file_tab()
            self._setup_batch_tab()
            self._setup_realtime_tab()
            logger.info("Tabs initialized")
        except Exception as e:
            logger.error(f"Tab init failed: {e}")
            self.results_panel.append(f"❌ UI Error: {e}")

        for tab in [self.tab_single, self.tab_batch, self.tab_realtime]:
            tab.configure(fg_color=self.theme.background)
            tab.grid_columnconfigure(0, weight=1)
        
        # 4. Settings Panel (Row 2)
        self.config_container = ctk.CTkFrame(
            self.content,
            corner_radius=ThemeManager.get_radius('lg'),
            fg_color=self.theme.surface,
            border_width=0
        )
        self.config_container.grid(row=2, column=0, sticky="ew", pady=(0, pad_md), padx=pad_lg)
        self.config_container.grid_columnconfigure(0, weight=1)
        
        self.settings_panel = SettingsPanel(
            self.config_container,
            on_change=self._save_settings, # Fix: Save settings on change
            responsive_manager=self.responsive
        )
        self.settings_panel.get_widget().grid(row=0, column=0, sticky="ew", padx=pad_md, pady=pad_md)
        
        logger.info("Main UI setup completed")
        self.status_bar.configure(text="UI Ready - Initializing Engines...")
    
    def _setup_single_file_tab(self):
        """Setup single file transcription tab."""
        # Configure tab grid for horizontal expansion
        self.tab_single.grid_columnconfigure(0, weight=1)
        
        # File selector
        self.single_file_selector = FileSelector(
            self.tab_single,
            mode="single",
            on_select=lambda files: setattr(self, 'selected_file', files[0] if files else None),
            responsive_manager=self.responsive
        )
        # CRITICAL: Use grid with sticky="ew" to force horizontal expansion
        self.single_file_selector.get_widget().grid(row=0, column=0, sticky="ew", pady=20, padx=20)
        
        # Transcribe button
        body_size = ThemeManager.get_font_size('body')
        btn_height = ThemeManager.get_button_height('lg')
        self.transcribe_btn = ctk.CTkButton(
            self.tab_single,
            text="⚡ Start Transcription",
            command=self._start_transcription,
            font=('Segoe UI', body_size + 3, 'bold'),
            height=btn_height,
            corner_radius=ThemeManager.get_radius('lg'),
            fg_color=self.theme.primary,
            hover_color=self.theme.primary_hover
        )
        # CRITICAL: Use grid with sticky="ew" to force horizontal expansion
        self.transcribe_btn.grid(row=1, column=0, sticky="ew", padx=SPACING.lg, pady=(SPACING.sm, SPACING.lg))
    
    def _setup_batch_tab(self):
        """Setup batch processing tab."""
        # Configure tab grid for horizontal expansion
        self.tab_batch.grid_columnconfigure(0, weight=1)
        
        # File selector
        self.batch_file_selector = FileSelector(
            self.tab_batch,
            mode="multiple",
            on_select=lambda files: setattr(self, 'selected_batch_files', files),
            responsive_manager=self.responsive
        )
        # CRITICAL: Use grid with sticky="ew" to force horizontal expansion
        self.batch_file_selector.get_widget().grid(row=0, column=0, sticky="ew", pady=20, padx=20)
        
        # Batch transcribe button
        body_size = ThemeManager.get_font_size('body')
        btn_height = ThemeManager.get_button_height('lg')
        self.batch_transcribe_btn = ctk.CTkButton(
            self.tab_batch,
            text="⚡ Process All Files",
            command=self._start_batch_transcription,
            font=('Segoe UI', body_size + 3, 'bold'),
            height=btn_height,
            corner_radius=ThemeManager.get_radius('lg'),
            fg_color=self.theme.accent,
            hover_color=self.theme.accent_hover
        )
        # CRITICAL: Use grid with sticky="ew" to force horizontal expansion
        self.batch_transcribe_btn.grid(row=1, column=0, sticky="ew", padx=SPACING.lg, pady=(SPACING.sm, SPACING.lg))
    
    def _setup_realtime_tab(self):
        """Setup realtime transcription tab with design tokens."""
        # Configure tab grid for horizontal expansion
        self.tab_realtime.grid_columnconfigure(0, weight=1)
        
        rt_card = ctk.CTkFrame(
            self.tab_realtime,
            corner_radius=ThemeManager.get_radius('lg'),
            border_width=0,  # Seamless - no border
            fg_color=self.theme.background,  # Match background for seamless look
        )
        # CRITICAL: Use grid with sticky="ew" to force horizontal expansion
        rt_card.grid(row=0, column=0, sticky="ew", pady=SPACING.lg, padx=SPACING.lg)
        rt_card.grid_columnconfigure(0, weight=1)
        
        inner = ctk.CTkFrame(rt_card, fg_color="transparent", border_width=0)
        inner.grid(row=0, column=0, sticky="ew", padx=SPACING.lg, pady=SPACING.lg)
        inner.grid_columnconfigure(0, weight=1)
        
        # Microphone selection
        body_size = ThemeManager.get_font_size('body')
        mic_label = ctk.CTkLabel(
            inner,
            text="Select Microphone",
            font=('Segoe UI', body_size, 'bold'),
            text_color=self.theme.text_secondary
        )
        mic_label.grid(row=0, column=0, sticky="w", pady=(0, SPACING.xs))
        
        self.mic_var = ctk.StringVar(value="Loading...")
        btn_height = ThemeManager.get_button_height('md')
        self.mic_combo = ctk.CTkComboBox(
            inner,
            variable=self.mic_var,
            values=["Loading..."],
            font=('Segoe UI', body_size),
            height=btn_height,
            corner_radius=ThemeManager.get_radius('sm'),
            fg_color=self.theme.surface_light,
            border_color=self.theme.border,
            button_color=self.theme.primary,
            button_hover_color=self.theme.primary_hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.primary
        )
        self.mic_combo.grid(row=1, column=0, sticky="ew", pady=(0, SPACING.lg))
        
        # Refresh button
        btn_height_sm = ThemeManager.get_button_height('sm')
        caption_size = ThemeManager.get_font_size('caption')
        refresh_btn = ctk.CTkButton(
            inner,
            text="🔄 Refresh",
            command=self._refresh_microphones,
            height=btn_height_sm,
            font=('Segoe UI', caption_size),
            fg_color="transparent",
            border_width=1,
            border_color=self.theme.border,
            corner_radius=ThemeManager.get_radius('sm')
        )
        refresh_btn.grid(row=2, column=0, sticky="ew", pady=(0, SPACING.md))
        
        # Audio level indicator
        audio_label = ctk.CTkLabel(
            inner,
            text="Audio Level",
            font=('Segoe UI', body_size, 'bold'),
            text_color=self.theme.text_secondary
        )
        audio_label.grid(row=3, column=0, sticky="w", pady=(SPACING.md, SPACING.xs))
        
        self.audio_level_bar = ctk.CTkProgressBar(
            inner,
            height=20,
            progress_color=self.theme.success,
            corner_radius=ThemeManager.get_radius('sm')
        )
        self.audio_level_bar.grid(row=4, column=0, sticky="ew", pady=(0, SPACING.lg))
        self.audio_level_bar.set(0)
        
        # Record button
        btn_height_lg = ThemeManager.get_button_height('lg')
        self.record_btn = ctk.CTkButton(
            self.tab_realtime,
            text="🔴 Start Recording",
            command=self._toggle_recording,
            font=('Segoe UI', body_size + 3, 'bold'),
            height=btn_height_lg,
            corner_radius=ThemeManager.get_radius('lg'),
            fg_color=self.theme.error,
            hover_color='#DC2626'
        )
        # CRITICAL: Use grid with sticky="ew" to force horizontal expansion
        self.record_btn.grid(row=1, column=0, sticky="ew", padx=SPACING.lg, pady=(SPACING.sm, SPACING.lg))
        
        # Realtime init is now part of _init_services_async
    
    def _init_realtime(self):
        """Initialize realtime transcriber."""
        try:
            self.realtime_transcriber = RealtimeTranscriber()
            self._refresh_microphones()
        except Exception as e:
            logger.error(f"Failed to init realtime: {e}")
            self.mic_var.set("Error loading devices")
    
    def _refresh_microphones(self):
        """Refresh microphone list."""
        if not self.realtime_transcriber:
            return
        devices = self.realtime_transcriber.get_microphones()
        self.mic_devices = devices
        names = [d['name'] for d in devices] or ["No microphones found"]
        self.mic_combo.configure(values=names)
        if names:
            self.mic_combo.set(names[0])
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start realtime recording."""
        try:
            name = self.mic_var.get()
            idx = -1
            for d in self.mic_devices:
                if d['name'] == name:
                    idx = d['index']
                    break
            
            self.is_recording = True
            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.theme.primary)
            self.progress_panel.update_status("🎙️ Listening...")
            self.results_panel.append(f"--- Recording Started ({name}) ---")
            
            self.realtime_transcriber.model_size = self.settings_panel.get_model()
            lang = self.settings_panel.get_language()
            self.realtime_transcriber.language = lang
            self.realtime_transcriber.start_transcription(
                idx,
                self._on_realtime_text,
                self._on_audio_level
            )
        except Exception as e:
            self._handle_error(e)
            self._stop_recording()
    
    def _stop_recording(self):
        """Stop realtime recording."""
        self.is_recording = False
        self.record_btn.configure(text="🔴 Start Recording", fg_color=self.theme.error)
        if self.realtime_transcriber:
            self.realtime_transcriber.stop_transcription()
        
        # Save recording
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            save_path = RECORDINGS_FOLDER / filename
            
            saved_file = self.realtime_transcriber.save_recording(str(save_path))
            if saved_file:
                self.results_panel.append(f"⏹ Stopped recording - Saved to {filename}")
                
                # Save transcription note
                try:
                    data = self.realtime_transcriber.get_transcription_data()
                    text_content = data['text'] or "(No speech detected or transcription failed)"
                    note_filename = f"recording_{timestamp}"
                    
                    duration_seconds = 0
                    if self.realtime_transcriber.full_audio_buffer:
                        total_samples = sum(len(chunk) for chunk in self.realtime_transcriber.full_audio_buffer)
                        duration_seconds = total_samples / self.realtime_transcriber.sample_rate
                    
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    duration_str = f"{minutes}:{seconds:02d}"
                    
                    note_content = create_realtime_note(
                        filename=note_filename,
                        text=text_content,
                        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        duration=duration_str,
                        file_size_mb=save_path.stat().st_size / (1024 * 1024) if save_path.exists() else 0,
                        model=self.realtime_transcriber.model_size,
                        language=data['language'],
                        formatting_style=self.settings_panel.get_formatting(),
                        duration_seconds=duration_seconds,
                        segments=data['segments'],
                        folder_path=str(TRANSCRIPTION_FOLDER)
                    )
                    
                    note_path = TRANSCRIPTION_FOLDER / f"{note_filename}.md"
                    note_path.write_text(note_content, encoding='utf-8')
                    self.results_panel.append(f"📝 Saved note to Notes: {note_filename}.md")
                except Exception as e:
                    logger.error(f"Failed to save note: {e}")
                    self.results_panel.append(f"❌ Failed to save note: {e}")
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")
            self.results_panel.append(f"⏹ Stopped recording - Save failed: {e}")
        
        self.progress_panel.update_status("✅ Stopped")
        self.audio_level_bar.set(0)
    
    def _on_realtime_text(self, text: str):
        """Callback for realtime text."""
        self.results_panel.append(f"🗣️ {text}")
    
    def _on_audio_level(self, level: float):
        """Update audio level indicator."""
        self.root.after(0, lambda: self._update_audio_level(level))
    
    def _update_audio_level(self, level: float):
        """Update progress bar with color coding."""
        self.audio_level_bar.set(level)
        
        if level < 0.5:
            color = self.theme.success
        elif level < 0.8:
            color = '#F59E0B'
        else:
            color = self.theme.error
        
        self.audio_level_bar.configure(progress_color=color)
    
    def _start_transcription(self):
        """Start single file transcription."""
        if not self.selected_file:
            messagebox.showerror("No File", "Please select an audio file.")
            return
        
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        self._disable_controls()
        self.progress_panel.start_indeterminate()
        
        threading.Thread(target=self._transcribe_audio, daemon=True).start()
    
    def _start_batch_transcription(self):
        """Start batch transcription."""
        if not self.selected_batch_files:
            messagebox.showerror("No Files", "Please select files or folder.")
            return
        
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        self._disable_controls()
        self.progress_panel.start_indeterminate()
        
        threading.Thread(target=self._transcribe_batch, daemon=True).start()
    
    def _transcribe_audio(self):
        """Single file transcription worker."""
        try:
            self.progress_panel.update_status("🔄 Loading model...")
            model_size = self.settings_panel.get_model()
            lang = self.settings_panel.get_language()
            
            transcriber = AudioTranscriber(model_size, lang)
            
            def callback(msg):
                self.progress_panel.update_status(f"🎙️ {msg}")
            
            output, data = transcriber.transcribe_file(
                self.selected_file,
                progress_callback=callback,
                formatting_style=self.settings_panel.get_formatting(),
                language=lang
            )
            
            self.progress_panel.update_status("✅ Transcription Complete!")
            self.results_panel.append(f"Completed: {output.name} ({data.get('duration', '?')})")
            self.root.after(0, lambda: self._show_success_dialog(output))
        except Exception as e:
            self._handle_error(e)
        finally:
            self.root.after(0, self._reset_ui)
    
    def _transcribe_batch(self):
        """Batch transcription worker."""
        try:
            from insightron.services.batch.batch_processor import batch_transcribe_files
            
            self.progress_panel.update_status("🔄 Starting batch...")
            model_size = self.settings_panel.get_model()
            lang = self.settings_panel.get_language()
            
            transcriber = AudioTranscriber(model_size, lang)
            
            def callback(completed, total, filename):
                self.progress_panel.update_status(f"📦 [{completed}/{total}] {filename}")
                self.results_panel.append(f"Processed: {filename}")
            
            results = batch_transcribe_files(
                self.selected_batch_files,
                model_size=model_size,
                language=lang,
                progress_callback=callback,
                transcriber=transcriber
            )
            
            self.progress_panel.update_status("✅ Batch Complete!")
            summary = f"Batch Results: {results['completed']} OK, {results['failed_count']} Failed"
            self.results_panel.append(summary)
        except Exception as e:
            self._handle_error(e)
        finally:
            self.root.after(0, self._reset_ui)
    
    def _handle_error(self, e: Exception):
        """Handle errors."""
        logger.error(f"Error: {e}")
        self.progress_panel.update_status("❌ Error")
        self.results_panel.append(f"ERROR: {str(e)}")
        messagebox.showerror("Error", str(e))
    
    def _reset_ui(self):
        """Reset UI after transcription."""
        self.progress_panel.stop_indeterminate()
        self._enable_controls()
        self.is_transcribing = False
    
    def _disable_controls(self):
        """Disable UI controls during transcription."""
        for btn in [self.transcribe_btn, self.batch_transcribe_btn]:
            btn.configure(state="disabled")
    
    def _enable_controls(self):
        """Enable UI controls."""
        for btn in [self.transcribe_btn, self.batch_transcribe_btn]:
            btn.configure(state="normal")
    
    def _show_success_dialog(self, output_path: Path):
        """Show success dialog."""
        if messagebox.askyesno("Success!", "Open output folder?"):
            try:
                os.startfile(str(output_path.parent))
            except:
                pass
    
    def _center_window(self):
        """Center window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
    
    def _load_settings(self):
        """Load saved settings."""
        try:
            # Set updating flag to prevent redundant save calls during initial load
            self.settings_panel._updating = True
            self.settings_panel.set_model(self.settings_manager.get("model", WHISPER_MODEL))
            self.settings_panel.set_language(self.settings_manager.get("language", DEFAULT_LANGUAGE))
            self.settings_panel.set_formatting(self.settings_manager.get("formatting", "auto"))
            self.settings_panel._updating = False
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            if hasattr(self, 'settings_panel'):
                self.settings_panel._updating = False
    
    def _save_settings(self):
        """Save current settings."""
        self.settings_manager.set("model", self.settings_panel.get_model())
        self.settings_manager.set("language", self.settings_panel.get_language())
        self.settings_manager.set("formatting", self.settings_panel.get_formatting())
