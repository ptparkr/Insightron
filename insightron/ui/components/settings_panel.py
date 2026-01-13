"""
Settings Panel component for Insightron GUI.

Provides configuration controls for model, language, and formatting
with adaptive responsive grid layout.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.ui.themes.design_tokens import SPACING, LayoutMode
from insightron.core.config import (
    WHISPER_MODEL,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    APP_VERSION
)


class SettingsPanel:
    """
    Settings configuration panel with responsive grid layout.
    
    Adapts to viewport size:
    - Expanded (desktop): 3 columns side-by-side
    - Standard (tablet): 2 columns + 1 below
    - Compact (mobile): Single column stack
    """
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_change: Optional[Callable] = None,
        responsive_manager: Optional['ResponsiveManager'] = None
    ):
        """
        Initialize settings panel.
        
        Args:
            parent: Parent frame
            on_change: Callback function when settings change
            responsive_manager: Optional ResponsiveManager for responsive behavior
        """
        self.parent = parent
        self.theme = ThemeManager.get_theme()
        self.on_change = on_change
        self.responsive = responsive_manager
        self._current_mode = LayoutMode.STANDARD
        
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
        
        # Subscribe to layout changes
        if self.responsive:
            self.responsive.subscribe(self._on_layout_change)
    
    def _create_panel(self):
        """Create the settings panel UI."""
        # Card container; geometry (pack/grid) is managed by parent
        # layout (e.g., main window grid), so we do not call pack/grid here.
        # Seamless look: border_width=0, match parent gray container
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=0,  # No corner radius - parent container has rounded corners
            border_width=0,  # Seamless - no border gaps
            fg_color="transparent",  # Transparent to show parent gray container
        )
        
        # Header - minimal gap between header and settings
        header = ctk.CTkFrame(self.card, fg_color="transparent", border_width=0)
        header.pack(fill="x", padx=SPACING.lg, pady=(SPACING.md, 0))  # No bottom padding
        
        header_font_size = ThemeManager.get_font_size('h2')
        ctk.CTkLabel(
            header,
            text="⚙️ Configuration",
            font=('Segoe UI', header_font_size, 'bold'),
            text_color=self.theme.text_primary
        ).pack(side="left")
        
        # Settings Container - will be reorganized on layout change
        # Minimal gap from header - start immediately after Configuration text
        pad_y = SPACING.md if self.responsive and self.responsive.is_short_height else SPACING.lg
        self.settings_container = ctk.CTkFrame(self.card, fg_color="transparent", border_width=0)
        self.settings_container.pack(fill="x", padx=SPACING.lg, pady=(SPACING.sm, pad_y))  # Small top padding
        
        # Create selector frames (these will be reorganized in _update_grid_layout)
        self.model_frame = self._create_model_selector()
        self.language_frame = self._create_language_selector()
        self.formatting_frame = self._create_formatting_selector()
        
        # Initial layout
        self._update_grid_layout(self._current_mode)
    
    def _create_model_selector(self) -> ctk.CTkFrame:
        """Create model selection dropdown."""
        frame = ctk.CTkFrame(self.settings_container, fg_color="transparent", border_width=0)
        
        label_size = ThemeManager.get_font_size('h3')
        caption_size = ThemeManager.get_font_size('caption')
        
        # Label directly above dropdown - minimal gap
        model_label = ctk.CTkLabel(
            frame,
            text="Whisper Model",
            font=('Segoe UI', label_size, 'bold'),
            text_color=self.theme.text_primary  # Use primary text color for better visibility
        )
        model_label.pack(anchor="w", pady=(0, SPACING.xs))  # Minimal gap between label and dropdown
        
        btn_height = ThemeManager.get_button_height('md')
        ctk.CTkOptionMenu(
            frame,
            variable=self.model_var,
            values=["tiny", "base", "small", "medium", "large-v2", "distil-medium.en", "distil-large-v2"],
            font=('Segoe UI', label_size, 'bold'),
            dropdown_font=('Segoe UI', label_size),
            corner_radius=ThemeManager.get_radius('sm'),
            height=btn_height,
            fg_color=self.theme.primary,
            button_color=self.theme.primary,
            button_hover_color=self.theme.primary_hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.primary
        ).pack(fill="x", pady=(0, 0))  # No gap after dropdown
        
        # Caption text - small gap after dropdown
        ctk.CTkLabel(
            frame,
            text="Speed vs Accuracy",
            font=('Segoe UI', caption_size),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(SPACING.sm, 0))  # Small gap after dropdown
        
        return frame
    
    def _create_language_selector(self) -> ctk.CTkFrame:
        """Create language selection dropdown."""
        frame = ctk.CTkFrame(self.settings_container, fg_color="transparent", border_width=0)
        
        label_size = ThemeManager.get_font_size('h3')
        caption_size = ThemeManager.get_font_size('caption')
        
        # Label directly above dropdown - minimal gap
        ctk.CTkLabel(
            frame,
            text="Language",
            font=('Segoe UI', label_size, 'bold'),
            text_color=self.theme.text_primary  # Use primary text color for better visibility
        ).pack(anchor="w", pady=(0, SPACING.xs))  # Minimal gap between label and dropdown
        
        lang_options = [f"{code} - {name}" for code, name in SUPPORTED_LANGUAGES.items()]
        
        btn_height = ThemeManager.get_button_height('md')
        ctk.CTkComboBox(
            frame,
            variable=self.language_var,
            values=lang_options,
            font=('Segoe UI', label_size, 'bold'),
            dropdown_font=('Segoe UI', label_size),
            corner_radius=ThemeManager.get_radius('sm'),
            height=btn_height,
            fg_color=self.theme.secondary,
            border_color=self.theme.secondary,
            button_color=self.theme.secondary,
            button_hover_color=self.theme.secondary_hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.secondary
        ).pack(fill="x", pady=(0, 0))  # No gap after dropdown
        
        # Caption text - small gap after dropdown
        ctk.CTkLabel(
            frame,
            text="Auto or Manual",
            font=('Segoe UI', caption_size),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(SPACING.sm, 0))  # Small gap after dropdown
        
        return frame
    
    def _create_formatting_selector(self) -> ctk.CTkFrame:
        """Create formatting selection dropdown."""
        frame = ctk.CTkFrame(self.settings_container, fg_color="transparent", border_width=0)
        
        label_size = ThemeManager.get_font_size('h3')
        caption_size = ThemeManager.get_font_size('caption')
        
        # Label directly above dropdown - minimal gap
        ctk.CTkLabel(
            frame,
            text="Text Formatting",
            font=('Segoe UI', label_size, 'bold'),
            text_color=self.theme.text_primary  # Use primary text color for better visibility
        ).pack(anchor="w", pady=(0, SPACING.xs))  # Minimal gap between label and dropdown
        
        btn_height = ThemeManager.get_button_height('md')
        ctk.CTkOptionMenu(
            frame,
            variable=self.formatting_var,
            values=["auto", "paragraphs", "minimal", "bullets"],
            font=('Segoe UI', label_size, 'bold'),
            dropdown_font=('Segoe UI', label_size),
            corner_radius=ThemeManager.get_radius('sm'),
            height=btn_height,
            fg_color=self.theme.accent,
            button_color=self.theme.accent,
            button_hover_color=self.theme.accent_hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.accent
        ).pack(fill="x", pady=(0, 0))  # No gap after dropdown
        
        # Caption text - small gap after dropdown
        ctk.CTkLabel(
            frame,
            text="Smart Detection",
            font=('Segoe UI', caption_size),
            text_color=self.theme.text_secondary
        ).pack(anchor="w", pady=(SPACING.sm, 0))  # Small gap after dropdown
        
        return frame
    
    def _update_grid_layout(self, mode: LayoutMode):
        """Reorganize selector frames based on layout mode."""
        # Remove all frames from grid
        for frame in [self.model_frame, self.language_frame, self.formatting_frame]:
            frame.pack_forget()
        
        gap = SPACING.sm
        
        if mode == LayoutMode.COMPACT:
            # Single column - stack vertically
            self.model_frame.pack(fill="x", pady=(0, gap))
            self.language_frame.pack(fill="x", pady=(0, gap))
            self.formatting_frame.pack(fill="x")
        elif mode == LayoutMode.STANDARD:
            # 2 columns + 1 below
            row1 = ctk.CTkFrame(self.settings_container, fg_color="transparent")
            row1.pack(fill="x", pady=(0, gap))
            self.model_frame.pack(in_=row1, side="left", fill="both", expand=True, padx=(0, gap))
            self.language_frame.pack(in_=row1, side="left", fill="both", expand=True)
            self.formatting_frame.pack(fill="x")
        else:  # EXPANDED
            # 3 columns side-by-side
            self.model_frame.pack(side="left", fill="both", expand=True, padx=(0, gap))
            self.language_frame.pack(side="left", fill="both", expand=True, padx=(0, gap))
            self.formatting_frame.pack(side="left", fill="both", expand=True)
    
    def _on_layout_change(self, mode: LayoutMode) -> None:
        """Handle layout mode changes."""
        if mode == self._current_mode:
            return
        self._current_mode = mode
        try:
            self._update_grid_layout(mode)
        except Exception:
            pass  # Component may be destroyed
    
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
