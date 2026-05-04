"""
Header component for Insightron GUI.

Provides the application header with title and subtitle.
"""

import customtkinter as ctk
from typing import Optional
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.ui.themes.design_tokens import SPACING, LayoutMode


class Header:
    """
    Application header component.
    Displays title, subtitle, and branding with responsive typography.
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        responsive_manager: Optional['ResponsiveManager'] = None
    ):
        """
        Initialize header component.
        
        Args:
            parent: Parent frame to attach header to
            responsive_manager: Optional ResponsiveManager for responsive behavior
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self.responsive = responsive_manager
        self._create_header()
        
        # Subscribe to layout changes if responsive manager provided
        if self.responsive:
            self.responsive.subscribe(self._on_layout_change)
    
    def _create_header(self):
        """Create the header UI elements."""
        # Create card container; geometry (pack/grid) is managed
        # by the parent layout (e.g., main window grid), so we do
        # not call pack/grid on this card here.
        # Seamless look: border_width=0, match background color
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=ThemeManager.get_radius('lg'),
            border_width=0,  # Seamless - no border gaps
            fg_color=self.theme.background,  # Match main background for seamless look
        )
        
        # Inner container with responsive padding
        pad = SPACING.lg
        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="x", padx=pad, pady=SPACING.md)
        
        # Title with responsive font size
        title_size = ThemeManager.get_font_size('hero')
        self.title_label = ctk.CTkLabel(
            inner,
            text="✨ Insightron",
            font=('Segoe UI', title_size, 'bold'),
            text_color=self.theme.primary
        )
        self.title_label.pack(anchor="w")
        
        # Subtitle with responsive font size
        subtitle_size = ThemeManager.get_font_size('body')
        self.subtitle_label = ctk.CTkLabel(
            inner,
            text="AI-Powered Transcription  •  Lightning Fast  •  100% Private",
            font=('Segoe UI', subtitle_size),
            text_color=self.theme.text_secondary
        )
        self.subtitle_label.pack(anchor="w", pady=(SPACING.xs, 0))
    
    def _on_layout_change(self, mode: LayoutMode) -> None:
        """Update header typography based on layout mode."""
        try:
            title_size = ThemeManager.get_font_size('hero')
            subtitle_size = ThemeManager.get_font_size('body')
            
            self.title_label.configure(font=('Segoe UI', title_size, 'bold'))
            self.subtitle_label.configure(font=('Segoe UI', subtitle_size))
        except Exception:
            pass  # Component may be destroyed
    
    def get_widget(self) -> ctk.CTkFrame:
        """Get the header widget."""
        return self.card
