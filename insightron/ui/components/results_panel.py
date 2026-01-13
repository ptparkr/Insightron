"""
Results Panel component for Insightron GUI.

Displays transcription output log with timestamps.
PRIORITY COMPONENT: This panel should have maximum visibility
across all viewport sizes.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.ui.themes.design_tokens import SPACING, LayoutMode


class ResultsPanel:
    """
    Results/output log panel.
    Displays transcription results with timestamps.
    
    This is the priority component - it receives all available
    vertical space after other panels are laid out.
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        responsive_manager: Optional['ResponsiveManager'] = None
    ):
        """
        Initialize results panel.
        
        Args:
            parent: Parent frame
            responsive_manager: Optional ResponsiveManager for responsive behavior
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self.responsive = responsive_manager
        self._create_panel()
        
        # Subscribe to layout changes
        if self.responsive:
            self.responsive.subscribe(self._on_layout_change)
    
    def _on_layout_change(self, mode: LayoutMode) -> None:
        """Update typography based on layout mode."""
        try:
            header_font_size = ThemeManager.get_font_size('h2')
            caption_font_size = ThemeManager.get_font_size('caption')
            mono_size = ThemeManager.get_font_size('mono')
            
            self.title_label.configure(font=('Segoe UI', header_font_size, 'bold'))
            self.clear_btn.configure(font=('Segoe UI', caption_font_size, 'bold'))
            self.results_text.configure(font=('Consolas', mono_size))
        except Exception:
            pass  # Component may be destroyed

    
    def _create_panel(self):
        """Create the results panel UI."""
        # Card container - expands to fill available space
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=ThemeManager.get_radius('lg'),
            border_width=1,
            border_color=self.theme.border,
            fg_color=self.theme.surface,
        )
        self.card.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING.lg, pady=(SPACING.md, SPACING.sm))
        
        header_font_size = ThemeManager.get_font_size('h2')
        self.title_label = ctk.CTkLabel(
            header,
            text="📝 Output Log",
            font=('Segoe UI', header_font_size, 'bold'),
            text_color=self.theme.text_primary
        )
        self.title_label.pack(side="left")
        
        # Clear button
        btn_height = ThemeManager.get_button_height('sm')
        self.clear_btn = ctk.CTkButton(
            header,
            text="Clear",
            command=self.clear,
            font=('Segoe UI', ThemeManager.get_font_size('caption'), 'bold'),
            height=btn_height,
            corner_radius=ThemeManager.get_radius('sm'),
            fg_color="transparent",
            border_width=1,
            border_color=self.theme.border,
            text_color=self.theme.text_secondary,
            hover_color=self.theme.surface_light
        )
        self.clear_btn.pack(side="right")
        
        # Results text area - word wrap enabled for narrow viewports
        mono_size = ThemeManager.get_font_size('mono')
        self.results_text = ctk.CTkTextbox(
            self.card,
            font=('Consolas', mono_size),
            corner_radius=0,
            fg_color=self.theme.background,
            border_width=0,
            wrap="word"  # Enable word wrap for narrow viewports
        )
        self.results_text.pack(fill="both", expand=True, padx=SPACING.lg, pady=(0, SPACING.lg))
        self.results_text.configure(state="disabled")
    
    def append(self, message: str):
        """Append message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"
        
        self.results_text.configure(state="normal")
        self.results_text.insert("end", formatted_msg)
        self.results_text.see("end")
        self.results_text.configure(state="disabled")
    
    def clear(self):
        """Clear all results."""
        self.results_text.configure(state="normal")
        self.results_text.delete("0.0", "end")
        self.results_text.configure(state="disabled")
    
    def get_widget(self) -> ctk.CTkFrame:
        """Get the results panel widget."""
        return self.card
