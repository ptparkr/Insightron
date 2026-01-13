"""
File Selector component for Insightron GUI.

Provides file and folder selection functionality.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import List, Optional, Callable
from insightron.ui.themes.theme_manager import ThemeManager


class FileSelector:
    """
    File selection component.
    Provides UI for selecting single files or multiple files/folders.
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        mode: str = "single",  # "single", "multiple", or "folder"
        on_select: Optional[Callable] = None
    ):
        """
        Initialize file selector.
        
        Args:
            parent: Parent frame
            mode: Selection mode ("single", "multiple", or "folder")
            on_select: Callback when files are selected
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self.mode = mode
        self.on_select = on_select
        self.selected_files: List[str] = []
        self.file_path_var = tk.StringVar(value="No file selected" if mode == "single" else "No files selected")
        self._create_selector()
    
    def _create_selector(self):
        """Create the file selector UI."""
        # Card container
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=12,
            border_width=1,
            border_color=self.theme.border,
            fg_color=self.theme.surface,
        )
        self.card.pack(fill="x", pady=20, padx=20)
        
        # Inner container
        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=30)
        
        # Icon
        icon_text = "🎵" if self.mode == "single" else "📦" if self.mode == "multiple" else "📂"
        icon = ctk.CTkLabel(inner, text=icon_text, font=('Segoe UI', 48))
        icon.pack(pady=(0, 15))
        
        # File status
        file_label = ctk.CTkLabel(
            inner,
            textvariable=self.file_path_var,
            font=('Segoe UI', 15),
            text_color=self.theme.text_secondary
        )
        file_label.pack(pady=(0, 20))
        
        # Button(s)
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack()
        
        if self.mode == "single":
            self.browse_btn = ctk.CTkButton(
                btn_frame,
                text="📁 Choose Audio File",
                command=self._browse_single,
                font=('Segoe UI', 15, 'bold'),
                height=50,
                width=240,
                corner_radius=10,
                fg_color=self.theme.primary,
                hover_color=self.theme.primary_hover
            )
            self.browse_btn.pack()
        elif self.mode == "multiple":
            self.browse_files_btn = ctk.CTkButton(
                btn_frame,
                text="📄 Choose Files",
                command=self._browse_multiple,
                font=('Segoe UI', 14, 'bold'),
                height=48,
                width=180,
                corner_radius=10,
                fg_color=self.theme.primary,
                hover_color=self.theme.primary_hover
            )
            self.browse_files_btn.pack(side="left", padx=8)
            
            self.browse_folder_btn = ctk.CTkButton(
                btn_frame,
                text="📂 Choose Folder",
                command=self._browse_folder,
                font=('Segoe UI', 14, 'bold'),
                height=48,
                width=180,
                corner_radius=10,
                fg_color=self.theme.secondary,
                hover_color=self.theme.secondary_hover
            )
            self.browse_folder_btn.pack(side="left", padx=8)
        
        # Supported formats
        formats = ctk.CTkLabel(
            inner,
            text="MP3  •  WAV  •  M4A  •  FLAC  •  MP4  •  OGG  •  AAC",
            font=('Segoe UI', 12),
            text_color=self.theme.text_secondary
        )
        formats.pack(pady=(15, 0))
    
    def _browse_single(self):
        """Browse for single file."""
        filename = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.m4a *.flac *.mp4 *.ogg *.aac")]
        )
        if filename:
            self.selected_files = [filename]
            name = Path(filename).name
            if len(name) > 45:
                name = name[:42] + "..."
            self.file_path_var.set(f"✓ {name}")
            if self.on_select:
                self.on_select(self.selected_files)
    
    def _browse_multiple(self):
        """Browse for multiple files."""
        filenames = filedialog.askopenfilenames(
            filetypes=[("Audio", "*.mp3 *.wav *.m4a *.flac *.mp4 *.ogg *.aac")]
        )
        if filenames:
            self.selected_files = list(filenames)
            self.file_path_var.set(f"✓ {len(filenames)} files selected")
            if self.on_select:
                self.on_select(self.selected_files)
    
    def _browse_folder(self):
        """Browse for folder."""
        folder = filedialog.askdirectory()
        if folder:
            exts = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.ogg', '.aac'}
            files = [str(p) for p in Path(folder).glob('*') if p.suffix.lower() in exts]
            if files:
                self.selected_files = files
                self.file_path_var.set(f"✓ {len(files)} files from folder")
                if self.on_select:
                    self.on_select(self.selected_files)
    
    def get_selected_files(self) -> List[str]:
        """Get list of selected files."""
        return self.selected_files
    
    def clear_selection(self):
        """Clear file selection."""
        self.selected_files = []
        self.file_path_var.set("No file selected" if self.mode == "single" else "No files selected")
    
    def get_widget(self) -> ctk.CTkFrame:
        """Get the file selector widget."""
        return self.card
