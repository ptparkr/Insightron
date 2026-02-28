"""
Responsive utilities for Insightron UI.

Provides viewport-aware layout management and responsive callbacks.
"""

import customtkinter as ctk
from typing import Callable, List, Optional
from insightron.ui.themes.design_tokens import (
    LayoutMode,
    BREAKPOINTS,
    SPACING,
    TYPOGRAPHY,
    SIZING,
    get_layout_mode
)


class ResponsiveManager:
    """
    Manages viewport-aware layout decisions.
    
    Monitors window resize events and notifies subscribers when
    the layout mode changes (compact/standard/expanded).
    
    Usage:
        responsive = ResponsiveManager(root)
        responsive.subscribe(lambda mode: update_layout(mode))
    """
    
    def __init__(self, root: ctk.CTk):
        """
        Initialize ResponsiveManager.
        
        Args:
            root: The root CTk window to monitor
        """
        self.root = root
        self._current_mode: LayoutMode = LayoutMode.STANDARD
        self._is_short_height: bool = False  # True when viewport height is limited
        self._observers: List[Callable[[LayoutMode], None]] = []
        self._debounce_id: Optional[str] = None
        self._debounce_delay: int = 100  # ms
        
        # Bind to configure events
        root.bind("<Configure>", self._on_configure)
        
        # Initialize mode based on current size
        root.after(50, self._update_mode)
    
    @property
    def mode(self) -> LayoutMode:
        """Get current layout mode."""
        return self._current_mode
    
    @property
    def is_compact(self) -> bool:
        """Check if in compact (mobile) mode."""
        return self._current_mode == LayoutMode.COMPACT
    
    @property
    def is_expanded(self) -> bool:
        """Check if in expanded (desktop) mode."""
        return self._current_mode == LayoutMode.EXPANDED
    
    @property
    def is_short_height(self) -> bool:
        """
        Check if the viewport height is constrained.
        
        This acts like a container query for vertical height.
        When True (e.g. height < 800px), components should
        switch to more compact vertical layouts.
        """
        return self._is_short_height
    
    def subscribe(self, callback: Callable[[LayoutMode], None]) -> None:
        """
        Subscribe to layout mode changes.
        
        Args:
            callback: Function to call when mode changes, receives new LayoutMode
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unsubscribe(self, callback: Callable[[LayoutMode], None]) -> None:
        """
        Unsubscribe from layout mode changes.
        
        Args:
            callback: Previously registered callback to remove
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def get_spacing(self, size: str = 'md') -> int:
        """
        Get spacing value adjusted for current layout mode.
        
        Args:
            size: Spacing size name (xs, sm, md, lg, xl, xxl)
            
        Returns:
            Spacing value in pixels
        """
        base = SPACING.get(size)
        
        # Start with base spacing and scale based on layout conditions.
        scale = 1.0
        
        # Slightly reduce spacing in compact (narrow width) mode.
        if self._current_mode == LayoutMode.COMPACT:
            scale *= 0.75
        
        # If vertical height is constrained, aggressively reduce vertical
        # padding by 50% to keep priority content (Output Log) visible.
        if self._is_short_height:
            scale *= 0.5
        
        return max(2, int(base * scale))
    
    def get_font_size(self, style: str) -> int:
        """
        Get font size for current layout mode.
        
        Args:
            style: Typography style (hero, h1, h2, body, caption, etc.)
            
        Returns:
            Font size in pixels
        """
        return TYPOGRAPHY.get_size(style, self._current_mode)
    
    def get_button_height(self, size: str = 'md') -> int:
        """
        Get button height for current layout mode.
        
        Args:
            size: Button size (sm, md, lg)
            
        Returns:
            Height in pixels
        """
        return SIZING.get_button_height(size, self._current_mode)
    
    def get_scaled_value(self, base: int, factor: float = 1.0) -> int:
        """
        Scale a value based on current layout mode.
        
        Args:
            base: Base value in pixels
            factor: Additional scaling factor
            
        Returns:
            Scaled value
        """
        mode_scale = {
            LayoutMode.COMPACT: 0.85,
            LayoutMode.STANDARD: 1.0,
            LayoutMode.EXPANDED: 1.1
        }.get(self._current_mode, 1.0)
        return int(base * mode_scale * factor)
    
    def _on_configure(self, event) -> None:
        """Handle window configure events with debouncing."""
        # Only respond to root window changes
        if event.widget != self.root:
            return
        
        # Cancel pending update
        if self._debounce_id:
            self.root.after_cancel(self._debounce_id)
        
        # Schedule debounced update
        self._debounce_id = self.root.after(
            self._debounce_delay,
            self._update_mode
        )
    
    def _update_mode(self) -> None:
        """Update layout mode and height flags based on current window size."""
        try:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            new_mode = get_layout_mode(width)
            new_short_height = height < 800  # Container-query style breakpoint
            
            changed = False
            if new_mode != self._current_mode:
                self._current_mode = new_mode
                changed = True
            
            if new_short_height != self._is_short_height:
                self._is_short_height = new_short_height
                changed = True
            
            # Only notify observers if something actually changed
            if changed:
                self._notify_observers()
        except Exception:
            # Window might not be fully initialized
            pass
    
    def _notify_observers(self) -> None:
        """Notify all subscribers of mode change."""
        for callback in self._observers:
            try:
                callback(self._current_mode)
            except Exception:
                # Don't let one callback break others
                pass


class ResponsiveFrame(ctk.CTkFrame):
    """
    A CTkFrame that automatically responds to layout mode changes.
    
    Subclass this to create components that adapt their layout
    based on viewport size.
    """
    
    def __init__(
        self,
        master,
        responsive_manager: Optional[ResponsiveManager] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self._responsive = responsive_manager
        
        if responsive_manager:
            responsive_manager.subscribe(self._on_mode_change)
    
    def _on_mode_change(self, mode: LayoutMode) -> None:
        """
        Called when layout mode changes.
        Override in subclasses to implement responsive behavior.
        
        Args:
            mode: New layout mode
        """
        pass
    
    def destroy(self) -> None:
        """Clean up subscriptions on destroy."""
        if self._responsive:
            self._responsive.unsubscribe(self._on_mode_change)
        super().destroy()


def create_responsive_grid(
    parent: ctk.CTkFrame,
    mode: LayoutMode,
    columns_config: dict
) -> None:
    """
    Configure a grid layout that adapts to the layout mode.
    
    Args:
        parent: Parent frame to configure
        mode: Current layout mode
        columns_config: Dict mapping mode to column count
            Example: {LayoutMode.COMPACT: 1, LayoutMode.STANDARD: 2, LayoutMode.EXPANDED: 3}
    """
    num_cols = columns_config.get(mode, 1)
    
    # Reset column weights
    for i in range(10):  # Reset up to 10 columns
        parent.columnconfigure(i, weight=0)
    
    # Set weights for active columns
    for i in range(num_cols):
        parent.columnconfigure(i, weight=1, uniform="responsive_col")
