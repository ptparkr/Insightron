"""
File Selector component for Insightron GUI.

Provides file and folder selection functionality with fluid button sizing.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import List, Optional, Callable
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.ui.themes.design_tokens import SPACING, LayoutMode


class FileSelector:
    """
    File selection component.
    Provides UI for selecting single files or multiple files/folders.
    Uses fluid layout with responsive sizing.
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        mode: str = "single",  # "single", "multiple", or "folder"
        on_select: Optional[Callable] = None,
        responsive_manager: Optional['ResponsiveManager'] = None
    ):
        """
        Initialize file selector.
        
        Args:
            parent: Parent frame
            mode: Selection mode ("single", "multiple", or "folder")
            on_select: Callback when files are selected
            responsive_manager: Optional ResponsiveManager for responsive behavior
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self.mode = mode
        self.on_select = on_select
        self.responsive = responsive_manager
        self.selected_files: List[str] = []
        self._is_compact: bool = False
        self.file_path_var = tk.StringVar(value="No file selected" if mode == "single" else "No files selected")
        self._create_selector()
        
        # Subscribe to layout changes
        if self.responsive:
            self.responsive.subscribe(self._on_layout_change)
    
    def _on_layout_change(self, mode: LayoutMode) -> None:
        """Update typography and layout based on mode."""
        try:
            icon_size = ThemeManager.get_font_size('hero')
            body_size = ThemeManager.get_font_size('body')
            caption_size = ThemeManager.get_font_size('caption')
            
            self.icon_label.configure(font=('Segoe UI', icon_size + 12))
            self.file_label.configure(font=('Segoe UI', body_size))
            self.formats_label.configure(font=('Segoe UI', caption_size))
            
            if hasattr(self, 'browse_btn'):
                self.browse_btn.configure(font=('Segoe UI', body_size, 'bold'))
            if hasattr(self, 'browse_files_btn'):
                self.browse_files_btn.configure(font=('Segoe UI', body_size, 'bold'))
            if hasattr(self, 'browse_folder_btn'):
                self.browse_folder_btn.configure(font=('Segoe UI', body_size, 'bold'))
        except Exception:
            pass  # Component may be destroyed

    
    def _create_selector(self):
        """Create the file selector UI."""
        # Card container - seamless look, height-aware
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=ThemeManager.get_radius('lg'),
            border_width=0,  # Seamless - no border gaps
            fg_color=self.theme.background,  # Match main background for seamless look
        )
        # Use responsive spacing when available so vertical padding
        # can shrink automatically on short viewports.
        pad_md = self.responsive.get_spacing('md') if self.responsive else SPACING.md
        pad_lg = self.responsive.get_spacing('lg') if self.responsive else SPACING.lg
        
        self.card.pack(fill="x", pady=pad_md, padx=pad_md)
        
        # Inner container
        self.inner = ctk.CTkFrame(self.card, fg_color="transparent")
        self.inner.pack(fill="x", padx=pad_lg, pady=pad_lg)
        
        # Icon
        icon_text = "🎵" if self.mode == "single" else "📦" if self.mode == "multiple" else "📂"
        icon_size = ThemeManager.get_font_size('hero')
        self.icon_label = ctk.CTkLabel(self.inner, text=icon_text, font=('Segoe UI', icon_size + 12))
        self.icon_label.pack(pady=(0, SPACING.md))
        
        # File status
        self.file_label = ctk.CTkLabel(
            self.inner,
            textvariable=self.file_path_var,
            font=('Segoe UI', ThemeManager.get_font_size('body')),
            text_color=self.theme.text_secondary
        )
        self.file_label.pack(pady=(0, SPACING.md))
        
        # Button(s) - using fill="x" for fluid widths
        btn_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        btn_height = ThemeManager.get_button_height('md')
        btn_font_size = ThemeManager.get_font_size('body')
        
        if self.mode == "single":
            self.browse_btn = ctk.CTkButton(
                btn_frame,
                text="📁 Choose Audio File",
                command=self._browse_single,
                font=('Segoe UI', btn_font_size, 'bold'),
                height=btn_height,
                corner_radius=ThemeManager.get_radius('md'),
                fg_color=self.theme.primary,
                hover_color=self.theme.primary_hover
            )
            self.browse_btn.pack(fill="x")  # Fluid width
        elif self.mode == "multiple":
            # Grid layout for two buttons
            btn_frame.columnconfigure(0, weight=1)
            btn_frame.columnconfigure(1, weight=1)
            
            self.browse_files_btn = ctk.CTkButton(
                btn_frame,
                text="📄 Choose Files",
                command=self._browse_multiple,
                font=('Segoe UI', btn_font_size, 'bold'),
                height=btn_height,
                corner_radius=ThemeManager.get_radius('md'),
                fg_color=self.theme.primary,
                hover_color=self.theme.primary_hover
            )
            self.browse_files_btn.grid(row=0, column=0, sticky="ew", padx=(0, SPACING.sm))
            
            self.browse_folder_btn = ctk.CTkButton(
                btn_frame,
                text="📂 Choose Folder",
                command=self._browse_folder,
                font=('Segoe UI', btn_font_size, 'bold'),
                height=btn_height,
                corner_radius=ThemeManager.get_radius('md'),
                fg_color=self.theme.secondary,
                hover_color=self.theme.secondary_hover
            )
            self.browse_folder_btn.grid(row=0, column=1, sticky="ew")
        
        # Supported formats
        self.formats_label = ctk.CTkLabel(
            self.inner,
            text="MP3  •  WAV  •  M4A  •  FLAC  •  MP4  •  OGG  •  AAC",
            font=('Segoe UI', ThemeManager.get_font_size('caption')),
            text_color=self.theme.text_secondary
        )
        self.formats_label.pack(pady=(SPACING.md, 0))
    
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
            # Enter compact mode once a file is selected to reduce
            # vertical footprint of the upload zone.
            self._apply_compact_mode()
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
            # Enter compact mode once files are selected to reduce
            # vertical footprint of the upload zone.
            self._apply_compact_mode()
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
                # Enter compact mode once files are selected to reduce
                # vertical footprint of the upload zone.
                self._apply_compact_mode()
                if self.on_select:
                    self.on_select(self.selected_files)
    
    def get_selected_files(self) -> List[str]:
        """Get list of selected files."""
        return self.selected_files
    
    def clear_selection(self):
        """Clear file selection."""
        self.selected_files = []
        self.file_path_var.set("No file selected" if self.mode == "single" else "No files selected")
        # Re-evaluate compact mode based on selection + viewport height
        self._apply_compact_mode()
    
    def get_widget(self) -> ctk.CTkFrame:
        """Get the file selector widget."""
        return self.card

    def _apply_compact_mode(self) -> None:
        """
        Apply or remove compact vertical layout.
        
        Compact mode is enabled when:
        - A file selection has been made, or
        - The viewport height is constrained (container-query style),
          as reported by the ResponsiveManager.
        """
        # Determine whether compact mode should be active.
        compact_due_to_height = bool(
            getattr(self.responsive, "is_short_height", False)
        )
        compact_due_to_selection = bool(self.selected_files)
        should_compact = compact_due_to_height or compact_due_to_selection
        
        if should_compact == self._is_compact:
            return  # No change
        
        self._is_compact = should_compact
        
        # Adjust vertical padding and secondary visuals in compact mode
        if self._is_compact:
            # Tighten inner padding - height-aware reduction
            compact_pad = (
                self.responsive.get_spacing('sm')
                if self.responsive
                else max(4, int(SPACING.lg * 0.5))
            )
            self.inner.pack_configure(pady=compact_pad)
            # De-emphasize decorative icon and formats on tight screens
            self.icon_label.pack_configure(pady=(0, SPACING.sm))
            self.formats_label.pack_configure(pady=(SPACING.sm, 0))
            
            # Reduce font sizes for height-aware compact mode
            if self.responsive and self.responsive.is_short_height:
                # Smaller icon when height is constrained
                icon_size = ThemeManager.get_font_size('hero')
                self.icon_label.configure(font=('Segoe UI', icon_size + 6))  # Reduced from +12
        else:
            # Restore default padding
            pad_lg = self.responsive.get_spacing('lg') if self.responsive else SPACING.lg
            self.inner.pack_configure(pady=pad_lg)
            self.icon_label.pack_configure(pady=(0, SPACING.md))
            self.formats_label.pack_configure(pady=(SPACING.md, 0))
            
            # Restore full icon size
            icon_size = ThemeManager.get_font_size('hero')
            self.icon_label.configure(font=('Segoe UI', icon_size + 12))
