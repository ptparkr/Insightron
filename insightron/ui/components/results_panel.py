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
        # Card container - expands to fill available space.
        # Geometry (pack/grid) is managed by parent layout
        # (e.g., main window grid), so we do not call pack/grid here.
        # The parent grid with sticky="nsew" and weight=1 ensures this expands.
        # Seamless look: border_width=0, match parent gray container
        self.card = ctk.CTkFrame(
            self.parent,
            corner_radius=0,  # No corner radius - parent container has rounded corners
            border_width=0,  # Seamless - no border gaps
            fg_color="transparent",  # Transparent to show parent gray container
        )
        # Configure card to expand and fill available space
        # The card itself will be managed by parent grid, but we ensure
        # internal layout expands properly
        self.card.grid_propagate(True)  # Allow natural expansion
        # Set a reasonable minimum height via minsize (handled by parent grid)
        # The actual expansion is controlled by parent grid row weight=1
        
        # Header - use grid for consistency
        header = ctk.CTkFrame(self.card, fg_color="transparent", border_width=0)
        header.grid(row=0, column=0, sticky="ew", padx=SPACING.lg, pady=(SPACING.md, SPACING.sm))
        header.grid_columnconfigure(0, weight=1)
        
        header_font_size = ThemeManager.get_font_size('h2')
        self.title_label = ctk.CTkLabel(
            header,
            text="📝 Output Log",
            font=('Segoe UI', header_font_size, 'bold'),
            text_color=self.theme.text_primary
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
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
        self.clear_btn.grid(row=0, column=1, sticky="e")
        
        # Results text area - RESTORED
        # This area displays the transcription output log.
        mono_size = ThemeManager.get_font_size('mono')
        self.results_text = ctk.CTkTextbox(
            self.card,
            font=('Consolas', mono_size),
            corner_radius=ThemeManager.get_radius('md'),
            fg_color=self.theme.background,
            border_width=1,
            border_color=self.theme.border,
            wrap="word",
        )
        self.results_text.grid(row=1, column=0, sticky="nsew", padx=SPACING.lg, pady=(SPACING.sm, SPACING.sm))
        self.results_text.configure(state="disabled")
        
        # Configure card grid 
        self.card.grid_rowconfigure(0, weight=0)  # Header: auto
        self.card.grid_rowconfigure(1, weight=1)  # Results text area: expands
        self.card.grid_rowconfigure(2, weight=0)  # Progress panel: auto
        self.card.grid_columnconfigure(0, weight=1)
        
        # Progress panel container - will be populated by main_window
        self.progress_container = ctk.CTkFrame(self.card, fg_color="transparent", border_width=0)
        self.progress_container.grid(row=2, column=0, sticky="ew", padx=SPACING.lg, pady=(SPACING.sm, SPACING.lg))
        self.progress_container.grid_columnconfigure(0, weight=1)
    
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
