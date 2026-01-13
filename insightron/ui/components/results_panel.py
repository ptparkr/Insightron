"""
Results Panel component for Insightron GUI.

Displays transcription output log with timestamps.
"""

import customtkinter as ctk
from datetime import datetime
from insightron.ui.themes.theme_manager import ThemeManager


class ResultsPanel:
    """
    Results/output log panel.
    Displays transcription results with timestamps.
    """
    
    def __init__(self, parent: ctk.CTkFrame):
        """
        Initialize results panel.
        
        Args:
            parent: Parent frame
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self._create_panel()
    
    def _create_panel(self):
        """Create the results panel UI."""
        # Card container
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=12,
            border_width=1,
            border_color=self.theme.border,
            fg_color=self.theme.surface,
        )
        self.card.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text="📝 Output Log",
            font=('Segoe UI', 18, 'bold'),
            text_color=self.theme.text_primary
        ).pack(side="left")
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            header,
            text="Clear",
            command=self.clear,
            font=('Segoe UI', 12, 'bold'),
            height=28,
            width=80,
            corner_radius=6,
            fg_color="transparent",
            border_width=1,
            border_color=self.theme.border,
            text_color=self.theme.text_secondary,
            hover_color=self.theme.surface_light
        )
        self.clear_btn.pack(side="right")
        
        # Results text area
        self.results_text = ctk.CTkTextbox(
            self.card,
            font=('Consolas', 11),
            corner_radius=0,
            fg_color=self.theme.background,
            border_width=0
        )
        self.results_text.pack(fill="both", expand=True, padx=25, pady=(0, 25))
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
