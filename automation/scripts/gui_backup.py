import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
import os
import logging
from typing import Optional, List
from datetime import datetime
from config import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, TRANSCRIPTION_FOLDER
from settings_manager import SettingsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsightronGUI:
    """
    Premium GUI for Insightron with Modern Aesthetics
    """
    
    # Modern Dark - Black Theme
    COLORS = {
        'primary': '#3B82F6',        # Bright Blue
        'primary_hover': '#2563EB',
        'secondary': '#8B5CF6',      # Purple
        'secondary_hover': '#7C3AED',
        'accent': '#10B981',         # Emerald
        'accent_hover': '#059669',
        'surface': '#121212',        # Material Dark (Almost Black)
        'surface_light': '#1E1E1E',  # Slightly lighter for inputs/hovers
        'background': '#000000',     # Pure Black
        'text_primary': '#FFFFFF',   # Pure White
        'text_secondary': '#A1A1AA', # Light Gray
        'border': '#27272A',         # Subtle Dark Border
        'success': '#10B981',
        'error': '#EF4444',
        'warning': '#F59E0B',
    }
    
    def __init__(self, root: ctk.CTk):
        """Initialize the Premium Insightron GUI"""
        self.root = root
        self.root.title("Insightron")
        self.root.geometry("1000x850")
        
        # Initialize Settings Manager
        self.settings = SettingsManager()
        
        # State
        self.selected_file = None
        self.selected_batch_files = []
        self.is_transcribing = False
        self.transcriber = None
        
        # Setup UI
        self.setup_ui()
        self.center_window()
        self.load_settings()
        
        logger.info("Premium GUI initialized")
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
    
    def load_settings(self):
        """Load saved settings"""
        try:
            self.model_var.set(self.settings.get("model", "medium"))
            self.language_var.set(self.settings.get("language", DEFAULT_LANGUAGE))
            self.formatting_var.set(self.settings.get("formatting", "auto"))
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def save_current_settings(self, *args):
        """Save current settings"""
        self.settings.set("model", self.model_var.get())
        self.settings.set("language", self.language_var.get())
        self.settings.set("formatting", self.formatting_var.get())

    def create_card(self, parent, **kwargs):
        """Create a premium card with subtle border"""
        return ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=1,
            border_color=self.COLORS['border'],
            fg_color=self.COLORS['surface'],
            **kwargs
        )

    def setup_ui(self):
        """Setup Premium UI"""
        # Main container with gradient-like background
        self.content = ctk.CTkFrame(self.root, fg_color=self.COLORS['background'])
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== PREMIUM HEADER =====
        header = self.create_card(self.content)
        header.pack(fill="x", pady=(0, 20))
        
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=30, pady=20)
        
        # Title with gradient-like effect using larger font
        title = ctk.CTkLabel(
            header_inner, 
            text="✨ Insightron", 
            font=('Segoe UI', 36, 'bold'),
            text_color=self.COLORS['primary']
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header_inner, 
            text="AI-Powered Transcription  •  Lightning Fast  •  100% Private",
            font=('Segoe UI', 14),
            text_color=self.COLORS['text_secondary']
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # ===== PREMIUM TABS =====
        self.tab_view = ctk.CTkTabview(
            self.content,
            corner_radius=12,
            fg_color=self.COLORS['surface'],
            segmented_button_fg_color=self.COLORS['surface_light'],
            segmented_button_selected_color=self.COLORS['primary'],
            segmented_button_selected_hover_color=self.COLORS['primary_hover'],
            text_color=self.COLORS['text_secondary'],
            segmented_button_unselected_hover_color=self.COLORS['border']
        )
        self.tab_view.pack(fill="both", expand=True, pady=(0, 15))
        
        self.tab_single = self.tab_view.add("Single File")
        self.tab_batch = self.tab_view.add("Batch Mode")
        
        # Configure tab colors
        self.tab_single.configure(fg_color=self.COLORS['background'])
        self.tab_batch.configure(fg_color=self.COLORS['background'])
        
        self.setup_single_file_tab()
        self.setup_batch_tab()
        
        # ===== SHARED COMPONENTS =====
        self.setup_settings_panel()
        self.setup_progress_panel()
        self.setup_results_panel()

    def setup_single_file_tab(self):
        """Single File Tab with Premium Design"""
        # Upload Card
        upload_card = self.create_card(self.tab_single)
        upload_card.pack(fill="x", pady=20, padx=20)
        
        inner = ctk.CTkFrame(upload_card, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=30)
        
        # Large Icon
        icon = ctk.CTkLabel(
            inner, 
            text="🎵", 
            font=('Segoe UI', 48)
        )
        icon.pack(pady=(0, 15))
        
        # File Status
        self.file_path_var = tk.StringVar(value="No audio file selected")
        file_label = ctk.CTkLabel(
            inner, 
            textvariable=self.file_path_var,
            font=('Segoe UI', 15),
            text_color=self.COLORS['text_secondary']
        )
        file_label.pack(pady=(0, 20))
        
        # Premium Browse Button
        self.browse_btn = ctk.CTkButton(
            inner, 
            text="📁 Choose Audio File",
            command=self.browse_file,
            font=('Segoe UI', 15, 'bold'),
            height=50,
            width=240,
            corner_radius=10,
            fg_color=self.COLORS['primary'],
            hover_color=self.COLORS['primary_hover']
        )
        self.browse_btn.pack()
        
        # Supported formats with icons
        formats = ctk.CTkLabel(
            inner, 
            text="MP3  •  WAV  •  M4A  •  FLAC  •  MP4  •  OGG  •  AAC",
            font=('Segoe UI', 12),
            text_color=self.COLORS['text_secondary']
        )
        formats.pack(pady=(15, 0))
        
        # Action Button
        self.transcribe_btn = ctk.CTkButton(
            self.tab_single, 
            text="⚡ Start Transcription",
            command=self.start_transcription,
            font=('Segoe UI', 18, 'bold'),
            height=56,
            corner_radius=12,
            fg_color=self.COLORS['accent'],
            hover_color=self.COLORS['accent_hover']
        )
        self.transcribe_btn.pack(fill="x", padx=20, pady=(10, 20))

    def setup_batch_tab(self):
        """Batch Mode Tab with Premium Design"""
        # Batch Card
        batch_card = self.create_card(self.tab_batch)
        batch_card.pack(fill="x", pady=20, padx=20)
        
        inner = ctk.CTkFrame(batch_card, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=30)
        
        # Icon
        icon = ctk.CTkLabel(inner, text="📦", font=('Segoe UI', 48))
        icon.pack(pady=(0, 15))
        
        # Status
        self.batch_path_var = tk.StringVar(value="No files selected")
        batch_label = ctk.CTkLabel(
            inner, 
            textvariable=self.batch_path_var,
            font=('Segoe UI', 15),
            text_color=self.COLORS['text_secondary']
        )
        batch_label.pack(pady=(0, 20))
        
        # Button Row
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack()
        
        self.browse_batch_btn = ctk.CTkButton(
            btn_frame, 
            text="📄 Choose Files",
            command=self.browse_batch_files,
            font=('Segoe UI', 14, 'bold'),
            height=48,
            width=180,
            corner_radius=10,
            fg_color=self.COLORS['primary'],
            hover_color=self.COLORS['primary_hover']
        )
        self.browse_batch_btn.pack(side="left", padx=8)
        
        self.browse_folder_btn = ctk.CTkButton(
            btn_frame, 
            text="📂 Choose Folder",
            command=self.browse_folder,
            font=('Segoe UI', 14, 'bold'),
            height=48,
            width=180,
            corner_radius=10,
            fg_color=self.COLORS['secondary'],
            hover_color=self.COLORS['secondary_hover']
        )
        self.browse_folder_btn.pack(side="left", padx=8)
        
        # Batch Action Button
        self.batch_transcribe_btn = ctk.CTkButton(
            self.tab_batch, 
            text="⚡ Process All Files",
            command=self.start_batch_transcription,
            font=('Segoe UI', 18, 'bold'),
            height=56,
            corner_radius=12,
            fg_color=self.COLORS['accent'],
            hover_color=self.COLORS['accent_hover']
        )
        self.batch_transcribe_btn.pack(fill="x", padx=20, pady=(10, 20))

    def setup_settings_panel(self):
        """Premium Settings Panel"""
        settings_card = self.create_card(self.content)
        settings_card.pack(fill="x", pady=(0, 15))
        
        # Header
        header = ctk.CTkFrame(settings_card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(
            header, 
            text="⚙️ Configuration",
            font=('Segoe UI', 18, 'bold'),
            text_color=self.COLORS['text_primary']
        ).pack(side="left")
        
        # Settings Grid
        grid = ctk.CTkFrame(settings_card, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=(0, 25))
        
        # Model
        model_frame = ctk.CTkFrame(grid, fg_color="transparent")
        model_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        ctk.CTkLabel(
            model_frame, 
            text="Whisper Model",
            font=('Segoe UI', 13, 'bold'),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w", pady=(0, 8))
        
        self.model_var = ctk.StringVar(value="medium")
        self.model_var.trace_add("write", self.save_current_settings)
        
        ctk.CTkOptionMenu(
            model_frame, 
            variable=self.model_var,
            values=["tiny", "base", "small", "medium", "large-v2"],
            font=('Segoe UI', 14, 'bold'),
            dropdown_font=('Segoe UI', 13),
            corner_radius=8,
            height=42,
            fg_color=self.COLORS['primary'],
            button_color=self.COLORS['primary'],
            button_hover_color=self.COLORS['primary_hover'],
            dropdown_fg_color=self.COLORS['surface_light'],
            dropdown_hover_color=self.COLORS['primary']
        ).pack(fill="x")
        
        ctk.CTkLabel(
            model_frame,
            text="Speed vs Accuracy",
            font=('Segoe UI', 11),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w", pady=(6, 0))
        
        # Language
        lang_frame = ctk.CTkFrame(grid, fg_color="transparent")
        lang_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        ctk.CTkLabel(
            lang_frame,
            text="Language",
            font=('Segoe UI', 13, 'bold'),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w", pady=(0, 8))
        
        self.language_var = ctk.StringVar(value=DEFAULT_LANGUAGE)
        self.language_var.trace_add("write", self.save_current_settings)
        
        lang_options = [f"{code} - {name}" for code, name in SUPPORTED_LANGUAGES.items()]
        
        ctk.CTkComboBox(
            lang_frame,
            variable=self.language_var,
            values=lang_options,
            font=('Segoe UI', 14, 'bold'),
            dropdown_font=('Segoe UI', 13),
            corner_radius=8,
            height=42,
            fg_color=self.COLORS['secondary'],
            border_color=self.COLORS['secondary'],
            button_color=self.COLORS['secondary'],
            button_hover_color=self.COLORS['secondary_hover'],
            dropdown_fg_color=self.COLORS['surface_light'],
            dropdown_hover_color=self.COLORS['secondary']
        ).pack(fill="x")
        
        ctk.CTkLabel(
            lang_frame,
            text="Auto or Manual",
            font=('Segoe UI', 11),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w", pady=(6, 0))
        
        # Formatting
        fmt_frame = ctk.CTkFrame(grid, fg_color="transparent")
        fmt_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            fmt_frame,
            text="Text Formatting",
            font=('Segoe UI', 13, 'bold'),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w", pady=(0, 8))
        
        self.formatting_var = ctk.StringVar(value="auto")
        self.formatting_var.trace_add("write", self.save_current_settings)
        
        ctk.CTkOptionMenu(
            fmt_frame,
            variable=self.formatting_var,
            values=["auto", "paragraphs", "minimal"],
            font=('Segoe UI', 14, 'bold'),
            dropdown_font=('Segoe UI', 13),
            corner_radius=8,
            height=42,
            fg_color=self.COLORS['accent'],
            button_color=self.COLORS['accent'],
            button_hover_color=self.COLORS['accent_hover'],
            dropdown_fg_color=self.COLORS['surface_light'],
            dropdown_hover_color=self.COLORS['accent']
        ).pack(fill="x")
        
        ctk.CTkLabel(
            fmt_frame,
            text="Smart Detection",
            font=('Segoe UI', 11),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w", pady=(6, 0))

    def setup_progress_panel(self):
        """Premium Progress Panel"""
        progress_card = self.create_card(self.content)
        progress_card.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        inner.pack(fill="x", padx=25, pady=20)
        
        # Status
        self.progress_var = tk.StringVar(value="Ready to transcribe")
        ctk.CTkLabel(
            inner,
            textvariable=self.progress_var,
            font=('Segoe UI', 15),
            text_color=self.COLORS['text_primary']
        ).pack(anchor="w", pady=(0, 12))
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            inner,
            height=8,
            corner_radius=4,
            progress_color=self.COLORS['primary']
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

    def setup_results_panel(self):
        """Premium Results Panel"""
        results_card = self.create_card(self.content)
        results_card.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(results_card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text="📝 Output Log",
            font=('Segoe UI', 18, 'bold'),
            text_color=self.COLORS['text_primary']
        ).pack(side="left")
        
        ctk.CTkButton(
            header,
            text="Clear",
            command=self.clear_all,
            font=('Segoe UI', 12, 'bold'),
            height=28,
            width=80,
            corner_radius=6,
            fg_color="transparent",
            border_width=1,
            border_color=self.COLORS['border'],
            text_color=self.COLORS['text_secondary'],
            hover_color=self.COLORS['surface_light']
        ).pack(side="right")
        
        # Results Text
        self.results_text = ctk.CTkTextbox(
            results_card,
            font=('Consolas', 11),
            corner_radius=0,
            fg_color=self.COLORS['background'],
            border_width=0
        )
        self.results_text.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        self.results_text.configure(state="disabled")

    # ===== EVENT HANDLERS =====
    
    def browse_file(self):
        """Browse single file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.m4a *.flac *.mp4 *.ogg *.aac")]
        )
        if filename:
            self.selected_file = filename
            name = Path(filename).name
            if len(name) > 45:
                name = name[:42] + "..."
            self.file_path_var.set(f"✓ {name}")
            self.update_results(f"Selected: {Path(filename).name}")

    def browse_batch_files(self):
        """Browse multiple files"""
        filenames = filedialog.askopenfilenames(
            filetypes=[("Audio", "*.mp3 *.wav *.m4a *.flac *.mp4 *.ogg *.aac")]
        )
        if filenames:
            self.selected_batch_files = list(filenames)
            self.batch_path_var.set(f"✓ {len(filenames)} files selected")
            self.update_results(f"Batch: Selected {len(filenames)} files")

    def browse_folder(self):
        """Browse folder"""
        folder = filedialog.askdirectory()
        if folder:
            exts = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.ogg', '.aac'}
            files = [str(p) for p in Path(folder).glob('*') if p.suffix.lower() in exts]
            if files:
                self.selected_batch_files = files
                self.batch_path_var.set(f"✓ {len(files)} files from folder")
                self.update_results(f"Batch: Found {len(files)} audio files")
            else:
                messagebox.showinfo("No Files", "No audio files found in folder.")

    def start_transcription(self):
        """Start single transcription"""
        if not self.selected_file:
            messagebox.showerror("No File", "Please select an audio file.")
            return
        self._start_processing(self.transcribe_audio)

    def start_batch_transcription(self):
        """Start batch"""
        if not self.selected_batch_files:
            messagebox.showerror("No Files", "Please select files or folder.")
            return
        self._start_processing(self.transcribe_batch)

    def _start_processing(self, target):
        """Start processing"""
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        for btn in [self.transcribe_btn, self.batch_transcribe_btn, 
                    self.browse_btn, self.browse_batch_btn, self.browse_folder_btn]:
            btn.configure(state="disabled")
        
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        threading.Thread(target=target, daemon=True).start()

    def transcribe_audio(self):
        """Single file worker"""
        try:
            from transcribe import AudioTranscriber
            self.update_progress("🔄 Loading model...")
            
            transcriber = AudioTranscriber(self.model_var.get())
            lang = self.language_var.get().split(' - ')[0]
            
            def callback(msg):
                self.update_progress(f"🎙️ {msg}")
            
            output, data = transcriber.transcribe_file(
                self.selected_file,
                progress_callback=callback,
                formatting_style=self.formatting_var.get(),
                language=lang
            )
            
            self.update_progress("✅ Transcription Complete!")
            self.update_results(f"Completed: {output.name} ({data.get('duration', '?')})")
            self.root.after(0, lambda: self.show_success_dialog(output))
            
        except Exception as e:
            self.handle_error(e)
        finally:
            self.root.after(0, self.reset_ui)

    def transcribe_batch(self):
        """Batch worker"""
        try:
            from batch_processor import batch_transcribe_files
            
            self.update_progress("🔄 Starting batch...")
            lang = self.language_var.get().split(' - ')[0]
            
            def callback(completed, total, filename):
                self.update_progress(f"📦 [{completed}/{total}] {filename}")
                self.update_results(f"Processed: {filename}")
            
            results = batch_transcribe_files(
                self.selected_batch_files,
                model_size=self.model_var.get(),
                language=lang,
                progress_callback=callback
            )
            
            self.update_progress("✅ Batch Complete!")
            summary = f"Batch Results: {results['completed']} OK, {results['failed_count']} Failed"
            self.update_results(summary)
            
        except Exception as e:
            self.handle_error(e)
        finally:
            self.root.after(0, self.reset_ui)

    def handle_error(self, e):
        logger.error(f"Error: {e}")
        self.update_progress("❌ Error")
        self.update_results(f"ERROR: {str(e)}")
        messagebox.showerror("Error", str(e))

    def reset_ui(self):
        """Reset UI"""
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        for btn in [self.transcribe_btn, self.batch_transcribe_btn,
                    self.browse_btn, self.browse_batch_btn, self.browse_folder_btn]:
            btn.configure(state="normal")
        self.is_transcribing = False

    def update_progress(self, msg):
        self.root.after(0, lambda: self.progress_var.set(msg))

    def update_results(self, msg):
        """Append message with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {msg}\n"
        
        def append():
            self.results_text.configure(state="normal")
            self.results_text.insert("end", formatted_msg)
            self.results_text.see("end")
            self.results_text.configure(state="disabled")
        self.root.after(0, append)

    def clear_all(self):
        self.results_text.configure(state="normal")
        self.results_text.delete("0.0", "end")
        self.results_text.configure(state="disabled")
        self.progress_var.set("Ready")
        self.progress_bar.set(0)

    def show_success_dialog(self, output_path):
        if messagebox.askyesno("Success!", "Open output folder?"):
            try:
                os.startfile(str(output_path.parent))
            except:
                pass
