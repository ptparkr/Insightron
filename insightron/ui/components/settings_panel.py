"""
Settings Panel component for Insightron GUI.

Provides configuration controls for model, language, and formatting.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.core.config import (
    WHISPER_MODEL,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    APP_VERSION
)


class SettingsPanel:
    """
    Settings configuration panel.
    Provides controls for model selection, language, and formatting.
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_change: Optional[Callable] = None
    ):
        """
        Initialize settings panel.
        
        Args:
            parent: Parent frame
            on_change: Callback function when settings change
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self.on_change = on_change
        
        # Variables
        self.model_var = tk.StringVar(value=WHISPER_MODEL)
        self.language_var = tk.StringVar(value=DEFAULT_LANGUAGE)
        self.formatting_var = tk.StringVar(value="auto")
        
        # Setup callbacks
        if self.on_change:
            self.model_var.trace_add("write", lambda *args: self.on_change())
            self.language_var.trace_add("write", lambda *args: self.on_change())
            self.formatting_var.trace_add("write", lambda *args: self.on_change())
        
        self._create_panel()
    
    def _create_panel(self):
        """Create the settings panel UI."""
        # Card container
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=12,
            border_width=1,
            border_color=self.theme.border,
            fg_color=self.theme.surface,
        )
        self.card.pack(fill="x", pady=(0, 15))
        
        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text="⚙️ Configuration",
            font=('Segoe UI', 18, 'bold'),
            text_color=self.theme.text_primary
        ).pack(side="left")
        
        # Settings Grid
        grid = ctk.CTkFrame(self.card, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=(0, 25))
        
        # Model Selection
        self._create_model_selector(grid)
        
        # Language Selection
        self._create_language_selector(grid)
        
        # Formatting Selection
        self._create_formatting_selector(grid)
    
    def _create_model_selector(self, parent: ctk.CTkFrame):
        """Create model selection dropdown."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        ctk.CTkLabel(
            frame,
            text="Whisper Model",
            font=('Segoe UI', 13, 'bold'),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(0, 8))
        
        ctk.CTkOptionMenu(
            frame,
            variable=self.model_var,
            values=["tiny", "base", "small", "medium", "large-v2", "distil-medium.en", "distil-large-v2"],
            font=('Segoe UI', 14, 'bold'),
            dropdown_font=('Segoe UI', 13),
            corner_radius=8,
            height=42,
            fg_color=self.theme.primary,
            button_color=self.theme.primary,
            button_hover_color=self.theme.primary_hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.primary
        ).pack(fill="x")
        
        ctk.CTkLabel(
            frame,
            text="Speed vs Accuracy",
            font=('Segoe UI', 11),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(6, 0))
    
    def _create_language_selector(self, parent: ctk.CTkFrame):
        """Create language selection dropdown."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        ctk.CTkLabel(
            frame,
            text="Language",
            font=('Segoe UI', 13, 'bold'),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(0, 8))
        
        lang_options = [f"{code} - {name}" for code, name in SUPPORTED_LANGUAGES.items()]
        
        ctk.CTkComboBox(
            frame,
            variable=self.language_var,
            values=lang_options,
            font=('Segoe UI', 14, 'bold'),
            dropdown_font=('Segoe UI', 13),
            corner_radius=8,
            height=42,
            fg_color=self.theme.secondary,
            border_color=self.theme.secondary,
            button_color=self.theme.secondary,
            button_hover_color=self.theme.secondary_hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.secondary
        ).pack(fill="x")
        
        ctk.CTkLabel(
            frame,
            text="Auto or Manual",
            font=('Segoe UI', 11),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(6, 0))
    
    def _create_formatting_selector(self, parent: ctk.CTkFrame):
        """Create formatting selection dropdown."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            frame,
            text="Text Formatting",
            font=('Segoe UI', 13, 'bold'),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(0, 8))
        
        ctk.CTkOptionMenu(
            frame,
            variable=self.formatting_var,
            values=["auto", "paragraphs", "minimal", "bullets"],
            font=('Segoe UI', 14, 'bold'),
            dropdown_font=('Segoe UI', 13),
            corner_radius=8,
            height=42,
            fg_color=self.theme.accent,
            button_color=self.theme.accent,
            button_hover_color=self.theme.accent_hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.accent
        ).pack(fill="x")
        
        ctk.CTkLabel(
            frame,
            text="Smart Detection",
            font=('Segoe UI', 11),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(6, 0))
    
    def get_model(self) -> str:
        """Get selected model."""
        return self.model_var.get()
    
    def get_language(self) -> str:
        """Get selected language code."""
        lang_str = self.language_var.get()
        return lang_str.split(' - ')[0] if ' - ' in lang_str else lang_str
    
    def get_formatting(self) -> str:
        """Get selected formatting style."""
        return self.formatting_var.get()
    
    def set_model(self, model: str):
        """Set model selection."""
        self.model_var.set(model)
    
    def set_language(self, language: str):
        """Set language selection."""
        self.language_var.set(language)
    
    def set_formatting(self, formatting: str):
        """Set formatting selection."""
        self.formatting_var.set(formatting)
    
    def get_widget(self) -> ctk.CTkFrame:
        """Get the settings panel widget."""
        return self.card
