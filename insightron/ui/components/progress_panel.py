"""
Progress Panel component for Insightron GUI.

Displays transcription progress and status with responsive spacing.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.ui.themes.design_tokens import SPACING, LayoutMode


class ProgressPanel:
    """
    Progress display panel.
    Shows current status and progress bar with design token spacing.
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        responsive_manager: Optional['ResponsiveManager'] = None
    ):
        """
        Initialize progress panel.
        
        Args:
            parent: Parent frame
            responsive_manager: Optional ResponsiveManager for responsive behavior
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self.responsive = responsive_manager
        self.progress_var = tk.StringVar(value="Ready to transcribe")
        self._create_panel()
        
        # Subscribe to layout changes
        if self.responsive:
            self.responsive.subscribe(self._on_layout_change)
    
    def _on_layout_change(self, mode: LayoutMode) -> None:
        """Update typography based on layout mode."""
        try:
            body_size = ThemeManager.get_font_size('body')
            self.status_label.configure(font=('Segoe UI', body_size))
        except Exception:
            pass  # Component may be destroyed

    
    def _create_panel(self):
        """Create the progress panel UI."""
        # Card container; geometry (pack/grid) is managed by parent
        # layout (e.g., main window grid), so we do not call pack/grid here.
        # Seamless look: border_width=0, match background color
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=ThemeManager.get_radius('lg'),
            border_width=0,  # Seamless - no border gaps
            fg_color=self.theme.background,  # Match main background for seamless look
        )
        
        # Inner container with responsive padding
        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING.lg, pady=SPACING.md)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            inner,
            textvariable=self.progress_var,
            font=('Segoe UI', ThemeManager.get_font_size('body')),
            text_color=self.theme.text_primary
        )
        self.status_label.pack(anchor="w", pady=(0, SPACING.sm))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            inner,
            height=8,
            corner_radius=4,
            progress_color=self.theme.primary
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
    
    def update_status(self, message: str):
        """Update status message."""
        self.progress_var.set(message)
    
    def set_progress(self, value: float):
        """Set progress bar value (0.0 to 1.0)."""
        self.progress_bar.set(value)
    
    def start_indeterminate(self):
        """Start indeterminate progress animation."""
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
    
    def stop_indeterminate(self):
        """Stop indeterminate progress and reset."""
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
    
    def get_widget(self) -> ctk.CTkFrame:
        """Get the progress panel widget."""
        return self.card
