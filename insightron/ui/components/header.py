"""
Header component for Insightron GUI.

Provides the application header with title and subtitle.
"""

import customtkinter as ctk
from insightron.ui.themes.theme_manager import ThemeManager


class Header:
    """
    Application header component.
    Displays title, subtitle, and branding.
    """
    
    def __init__(self, parent: ctk.CTkFrame):
        """
        Initialize header component.
        
        Args:
            parent: Parent frame to attach header to
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self._create_header()
    
    def _create_header(self):
        """Create the header UI elements."""
        # Create card container
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=12,
            border_width=1,
            border_color=self.theme.border,
            fg_color=self.theme.surface,
        )
        self.card.pack(fill="x", pady=(0, 20))
        
        # Inner container
        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            inner,
            text="✨ Insightron",
            font=('Segoe UI', 36, 'bold'),
            text_color=self.theme.primary
        )
        self.title_label.pack(anchor="w")
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            inner,
            text="AI-Powered Transcription  •  Lightning Fast  •  100% Private",
            font=('Segoe UI', 14),
            text_color=self.theme.text_secondary
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))
    
    def get_widget(self) -> ctk.CTkFrame:
        """Get the header widget."""
        return self.card
