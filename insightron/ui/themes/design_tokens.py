"""
Design Tokens for Insightron UI.

Centralized design system providing consistent spacing, typography,
and breakpoint definitions for a responsive layout paradigm.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple


class LayoutMode(Enum):
    """Layout modes for responsive design."""
    COMPACT = auto()    # Mobile/narrow (< 640px)
    STANDARD = auto()   # Tablet/medium (640-1024px)
    EXPANDED = auto()   # Desktop/wide (> 1024px)


@dataclass(frozen=True)
class SpacingScale:
    """
    Consistent spacing scale using multiples of 4px base unit.
    Use these instead of magic numbers for padding/margins.
    """
    xs: int = 4      # Micro spacing - tight elements
    sm: int = 8      # Compact - between related items
    md: int = 16     # Standard - section padding
    lg: int = 24     # Comfortable - card padding
    xl: int = 32     # Spacious - major sections
    xxl: int = 48    # Hero - large visual breaks
    
    def get(self, size: str) -> int:
        """Get spacing value by name."""
        return getattr(self, size, self.md)


@dataclass(frozen=True)
class TypographyScale:
    """
    Responsive typography scale.
    Each tuple contains (desktop, tablet, mobile) font sizes.
    """
    # Display/hero text
    hero: Tuple[int, int, int] = (36, 28, 24)
    
    # Headings
    h1: Tuple[int, int, int] = (24, 20, 18)
    h2: Tuple[int, int, int] = (18, 16, 15)
    h3: Tuple[int, int, int] = (15, 14, 13)
    
    # Body text
    body: Tuple[int, int, int] = (15, 14, 13)
    body_small: Tuple[int, int, int] = (13, 12, 12)
    
    # Captions and labels
    caption: Tuple[int, int, int] = (12, 11, 11)
    
    # Monospace (for logs)
    mono: Tuple[int, int, int] = (12, 11, 10)
    
    def get_size(self, style: str, mode: LayoutMode) -> int:
        """
        Get font size for a style at the given layout mode.
        
        Args:
            style: Typography style name (hero, h1, body, etc.)
            mode: Current layout mode
            
        Returns:
            Font size in pixels
        """
        sizes = getattr(self, style, self.body)
        mode_index = {
            LayoutMode.EXPANDED: 0,
            LayoutMode.STANDARD: 1,
            LayoutMode.COMPACT: 2
        }.get(mode, 1)
        return sizes[mode_index]


@dataclass(frozen=True)
class Breakpoints:
    """
    Viewport width breakpoints for responsive layout switches.
    Values in pixels.
    """
    mobile: int = 640       # Below this: COMPACT mode
    tablet: int = 1024      # 640-1024: STANDARD mode
    desktop: int = 1440     # 1024-1440: EXPANDED mode
    ultrawide: int = 2560   # Above 1440: EXPANDED with extra density
    
    def get_mode(self, width: int) -> LayoutMode:
        """
        Determine layout mode based on viewport width.
        
        Args:
            width: Current window width in pixels
            
        Returns:
            Appropriate LayoutMode for the width
        """
        if width < self.mobile:
            return LayoutMode.COMPACT
        elif width < self.tablet:
            return LayoutMode.STANDARD
        else:
            return LayoutMode.EXPANDED


@dataclass(frozen=True)  
class ComponentSizing:
    """
    Standard component sizing values.
    Provides consistent heights/widths across UI elements.
    """
    # Button heights (compact, standard, expanded)
    button_sm: Tuple[int, int, int] = (28, 32, 36)
    button_md: Tuple[int, int, int] = (36, 42, 48)
    button_lg: Tuple[int, int, int] = (44, 52, 56)
    
    # Input heights  
    input_height: Tuple[int, int, int] = (36, 40, 44)
    
    # Corner radii
    radius_sm: int = 6
    radius_md: int = 10
    radius_lg: int = 12
    
    # Minimum widths for interactive elements
    min_touch_target: int = 44  # Accessibility minimum
    
    def get_button_height(self, size: str, mode: LayoutMode) -> int:
        """Get button height for size and layout mode."""
        heights = getattr(self, f"button_{size}", self.button_md)
        mode_index = {
            LayoutMode.COMPACT: 0,
            LayoutMode.STANDARD: 1,
            LayoutMode.EXPANDED: 2
        }.get(mode, 1)
        return heights[mode_index]


# Global design token instances
SPACING = SpacingScale()
TYPOGRAPHY = TypographyScale()
BREAKPOINTS = Breakpoints()
SIZING = ComponentSizing()


def get_spacing(size: str = 'md') -> int:
    """Convenience function to get spacing value."""
    return SPACING.get(size)


def get_font_size(style: str, mode: LayoutMode = LayoutMode.STANDARD) -> int:
    """Convenience function to get font size."""
    return TYPOGRAPHY.get_size(style, mode)


def get_layout_mode(width: int) -> LayoutMode:
    """Convenience function to get layout mode from width."""
    return BREAKPOINTS.get_mode(width)
