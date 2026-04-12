"""
Theme Manager for Insightron GUI.

Provides centralized theme management with modern dark theme support.
"""

from typing import Dict, Any
from dataclasses import dataclass

# Import design tokens for integration
from insightron.ui.themes.design_tokens import (
    LayoutMode,
    SPACING,
    TYPOGRAPHY,
    SIZING,
    BREAKPOINTS,
    get_layout_mode
)


@dataclass
class Theme:
    """Theme configuration dataclass."""
    # Primary colors
    primary: str
    primary_hover: str
    
    # Secondary colors
    secondary: str
    secondary_hover: str
    
    # Accent colors
    accent: str
    accent_hover: str
    
    # Surface colors
    surface: str
    surface_light: str
    
    # Background
    background: str
    
    # Text colors
    text_primary: str
    text_secondary: str
    
    # Border
    border: str
    
    # Status colors
    success: str
    error: str
    warning: str


class ThemeManager:
    """
    Manages application themes.
    Provides access to color schemes, styling, and design tokens.
    """
    
    # Modern Dark - Black Theme (Default)
    DARK_THEME = Theme(
        primary='#6366F1',           # Vibrant Indigo
        primary_hover='#4F46E5',
        secondary='#EC4899',         # Vibrant Pink
        secondary_hover='#DB2777',
        accent='#0EA5E9',             # Bright Sky Blue
        accent_hover='#0284C7',
        surface='#18181B',            # Zinc 900 (Sleek dark)
        surface_light='#27272A',     # Zinc 800 (Elevated elements)
        background='#09090B',          # Zinc 950 (Deep background)
        text_primary='#FAFAFA',        # Zinc 50 (Very crisp text)
        text_secondary='#A1A1AA',   # Zinc 400 (Subtle text)
        border='#3F3F46',            # Zinc 700 (Clean divider)
        success='#10B981',
        error='#F43F5E',             # Rose 500
        warning='#F59E0B',
    )
    
    _current_theme: Theme = DARK_THEME
    _current_mode: LayoutMode = LayoutMode.STANDARD
    
    @classmethod
    def get_theme(cls) -> Theme:
        """Get the current theme."""
        return cls._current_theme
    
    @classmethod
    def set_theme(cls, theme: Theme):
        """Set the current theme."""
        cls._current_theme = theme
    
    @classmethod
    def set_layout_mode(cls, mode: LayoutMode):
        """Set the current layout mode for responsive sizing."""
        cls._current_mode = mode
    
    @classmethod
    def get_layout_mode(cls) -> LayoutMode:
        """Get the current layout mode."""
        return cls._current_mode
    
    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        """Get colors as a dictionary for compatibility."""
        theme = cls.get_theme()
        return {
            'primary': theme.primary,
            'primary_hover': theme.primary_hover,
            'secondary': theme.secondary,
            'secondary_hover': theme.secondary_hover,
            'accent': theme.accent,
            'accent_hover': theme.accent_hover,
            'surface': theme.surface,
            'surface_light': theme.surface_light,
            'background': theme.background,
            'text_primary': theme.text_primary,
            'text_secondary': theme.text_secondary,
            'border': theme.border,
            'success': theme.success,
            'error': theme.error,
            'warning': theme.warning,
        }
    
    @classmethod
    def get_spacing(cls, size: str = 'md') -> int:
        """
        Get spacing value from design tokens.
        
        Args:
            size: Spacing size (xs, sm, md, lg, xl, xxl)
            
        Returns:
            Spacing value in pixels
        """
        return SPACING.get(size)
    
    @classmethod
    def get_font_size(cls, style: str) -> int:
        """
        Get font size for the current layout mode.
        
        Args:
            style: Typography style (hero, h1, h2, body, caption, etc.)
            
        Returns:
            Font size in pixels
        """
        return TYPOGRAPHY.get_size(style, cls._current_mode)
    
    @classmethod
    def get_button_height(cls, size: str = 'md') -> int:
        """
        Get button height for the current layout mode.
        
        Args:
            size: Button size (sm, md, lg)
            
        Returns:
            Height in pixels
        """
        return SIZING.get_button_height(size, cls._current_mode)
    
    @classmethod
    def get_radius(cls, size: str = 'md') -> int:
        """
        Get corner radius value.
        
        Args:
            size: Radius size (sm, md, lg)
            
        Returns:
            Radius value in pixels
        """
        return getattr(SIZING, f'radius_{size}', SIZING.radius_md)


def get_theme() -> Dict[str, str]:
    """Get current theme colors as dictionary (convenience function)."""
    return ThemeManager.get_colors()

