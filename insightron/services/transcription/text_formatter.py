#!/usr/bin/env python3
"""
Enhanced Text Formatter for Insightron
Intelligently formats transcribed text with proper structure, punctuation, and paragraph breaks.
Optimized for performance and accuracy with improved error handling.
"""

import re
import logging
import hashlib
from typing import List, Tuple, Dict, Set, Optional, Any
from functools import lru_cache
from insightron.core.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextFormatter:
    """
    Human Readability Engine for Insightron.
    Mental model: typesetter, not author.
    
    Responsibilities:
    - Apply punctuation
    - Structure into paragraphs/lists
    - Format inline LaTeX for scientific/math terms
    
    Never:
    - Change meaning
    - Add words
    """
    
    def __init__(self):
        # Technical/Mathematical terms for LaTeX conversion (only if unambiguous)
        self.latex_map = {
            "alpha": r"$\alpha$",
            "beta": r"$\beta$",
            "gamma": r"$\gamma$",
            "delta": r"$\delta$",
            "pi": r"$\pi$",
            "sigma": r"$\sigma$",
            "theta": r"$\theta$",
            "lambda": r"$\lambda$",
            "omega": r"$\omega$",
            "plus or minus": r"$\pm$",
            "squared": r"$^2$",
            "cubed": r"$^3$",
            "greater than or equal to": r"$\ge$",
            "less than or equal to": r"$\le$"
        }

    def format_structure(self, segments: List[Dict[str, Any]], style: str = "auto") -> str:
        """
        Apply structural formatting to the transcription segments.
        Guarantees meaning preservation.
        """
        # 1. Join raw text
        raw_text = " ".join([seg["text"] for seg in segments])
        
        # 2. Apply Punctuation (Typesetting)
        # We use a simple rule-based approach to ensure we don't add semantic weight
        formatted_text = self._apply_punctuation(raw_text)
        
        # 3. Apply LaTeX (Technical formatting)
        formatted_text = self._apply_latex(formatted_text)
        
        # 4. Apply Structural Layout (Paragraphs/Lists)
        if style == "bullets":
            return self._to_bullets(formatted_text)
        
        return self._to_paragraphs(formatted_text)

    def _apply_punctuation(self, text: str) -> str:
        """Standardize punctuation and capitalization."""
        if not text:
            return ""
            
        # Ensure capitalization of the first word
        text = text[0].upper() + text[1:] if len(text) > 0 else text
        
        # Ensure it ends with a period if missing
        if not text.rstrip()[-1] in ".!?":
            text = text.rstrip() + "."
            
        # Basic cleanup of spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])([a-zA-Z])', r'\1 \2', text)
        
        return text

    def _apply_latex(self, text: str) -> str:
        """Convert unambiguous terms to LaTeX."""
        # Simple word-for-word mapping to avoid meaning shift
        for term, latex in self.latex_map.items():
            pattern = re.compile(rf'\b{term}\b', re.IGNORECASE)
            text = pattern.sub(latex, text)
        return text

    def _to_paragraphs(self, text: str) -> str:
        """Break text into readable paragraphs based on length and pauses."""
        # Typesetter rule: avoid "walls of text"
        sentences = re.split(r'(?<=[.!?])\s+', text)
        paragraphs = []
        current_p = []
        
        for i, sent in enumerate(sentences):
            current_p.append(sent)
            # Break every 3-5 sentences for readability
            if len(current_p) >= 4:
                paragraphs.append(" ".join(current_p))
                current_p = []
                
        if current_p:
            paragraphs.append(" ".join(current_p))
            
        return "\n\n".join(paragraphs)

    def _to_bullets(self, text: str) -> str:
        """Convert text into a bulleted list."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return "\n".join([f"* {s}" for s in sentences if s.strip()])
