"""
Audio Visualizer Component for Insightron.

A sleek, responsive audio visualizer canvas using CustomTkinter's canvas wrapper.
Draws dynamic bars or waveforms based on audio level input with a modern look.
"""

import customtkinter as ctk
import math
from typing import Tuple, List

from insightron.ui.themes.theme_manager import ThemeManager

class AudioVisualizer(ctk.CTkFrame):
    """
    Audio visualizer utilizing a canvas for smooth, reactive rendering.
    Supports a sleek EQ bar or wave representation.
    """
    
    def __init__(self, master, num_bars: int = 40, update_speed_ms: int = 50, **kwargs):
        """
        Initialize the Audio Visualizer.
        
        Args:
            master: Parent widget
            num_bars: Number of distinct frequency/amplitude bars to show
            update_speed_ms: Refresh rate for decay animation
        """
        # Set transparent fallback color to rely on theme background
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = "transparent"
            
        super().__init__(master, **kwargs)
        
        self.theme = ThemeManager.get_theme()
        
        # Options
        self.num_bars = num_bars
        self.update_speed_ms = update_speed_ms
        self.current_level = 0.0
        
        # Smoothing buffers for each bar to create variations
        # target values
        self.target_heights = [0.0] * num_bars
        # actual displayed values
        self.current_heights = [0.0] * num_bars
        
        # Configure grid expansion
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # CTkCanvas (accessing standard tk.Canvas underneath for drawing)
        # Using a fixed minimal height, it will expand based on master layout
        self.canvas = ctk.CTkCanvas(
            self,
            bg=self._hex_to_rgb_tk(self.theme.surface_light),
            highlightthickness=0,
            bd=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Bind resize to redraw
        self.canvas.bind("<Configure>", self._on_resize)
        
        # Start decay animation loop
        self._animate()

    def _hex_to_rgb_tk(self, hex_color: str) -> str:
        """Helper to ensure valid Tk color format if using hex."""
        if not hex_color.startswith('#'):
            return '#1A1A1A' # Fallback
        return hex_color

    def set_level(self, level: float):
        """
        Set the raw audio level (0.0 to 1.0)
        """
        self.current_level = max(0.0, min(1.0, level))
        self._generate_target_heights()

    def _generate_target_heights(self):
        """
        Creates stylized targets based on the current level.
        Simulates an EQ curve where the center reacts more intensely.
        """
        center = self.num_bars / 2
        
        for i in range(self.num_bars):
            # Calculate distance from center (normalized -1 to 1)
            dist_normalized = abs(i - center) / center
            
            # Bell curve shaped weighting so center bars are taller
            weight = math.exp(-2.0 * dist_normalized**2)
            
            # Create some pseudo-randomness based on position to make it look active
            noise = (math.sin(i * 13.37 + self.current_level * 100) + 1) * 0.15 + 0.85
            
            # The target height is heavily weighted by the raw level
            target = self.current_level * weight * noise
            
            self.target_heights[i] = min(1.0, max(0.05, target)) # minimum 5% height

    def _animate(self):
        """Periodic loop to smoothly move current_heights toward target_heights."""
        decay_factor = 0.15 # Higher = snaps to target, Lower = smoother but lags
        rise_factor = 0.3   # Fast attack
        
        # Update current heights
        for i in range(self.num_bars):
            diff = self.target_heights[i] - self.current_heights[i]
            if diff > 0:
                self.current_heights[i] += diff * rise_factor
            else:
                self.current_heights[i] += diff * decay_factor
                
            # Idle gentle wave if raw level is basically zero
            if self.current_level < 0.01:
               idle_wave = (math.sin(i * 0.3 + self.winfo_id() / 100.0) + 1.0) * 0.02 + 0.01
               self.current_heights[i] = max(self.current_heights[i], idle_wave)
                
        self._draw_bars()
        
        # Schedule next tick
        self.after(self.update_speed_ms, self._animate)

    def _draw_bars(self):
        """Renders the bars on the canvas."""
        self.canvas.delete("all")
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return # Canvas not yet mapped
            
        bar_gap = 2
        total_gaps = (self.num_bars - 1) * bar_gap
        bar_width = max((canvas_width - total_gaps) / self.num_bars, 1.0)
        
        # Colors based on general level mapping to theme colors
        if self.current_level < 0.5:
            bar_color = self.theme.primary
        elif self.current_level < 0.8:
            bar_color = self.theme.warning
        else:
            bar_color = self.theme.error
            
        x_offset = 0
        for i in range(self.num_bars):
            normalized_h = self.current_heights[i]
            # Height in pixels
            h = normalized_h * (canvas_height * 0.9)  # Max 90% of canvas
            
            # Center the bars vertically (waveform style)
            y0 = (canvas_height / 2) - (h / 2)
            y1 = (canvas_height / 2) + (h / 2)
            
            x0 = x_offset
            x1 = x_offset + bar_width
            
            # Draw rounded caps if possible, tk rect is simple so we use polygons/ovals for caps if desired,
            # but for a simple clean look, straight rects are fine. We will use simple rects for speed.
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill=bar_color, outline="", width=0
            )
            
            x_offset += bar_width + bar_gap

    def _on_resize(self, event):
        """Force a redraw when resized."""
        self._draw_bars()

    def reset(self):
        """Reset the visualizer to zero immediately."""
        self.current_level = 0.0
        self.target_heights = [0.0] * self.num_bars
        # Let the animation decay handle bringing current heights to 0 smoothly
