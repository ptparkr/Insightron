"""
Text Formatter - Single-pass processing with pre-compiled regex

Features:
- O(n) single-pass processing
- Pre-compiled regex patterns
- Frozen dataclass views
- View-specific transition overrides
- Optional filler removal and error correction
"""

import re
import logging
from dataclasses import dataclass
from typing import FrozenSet, Literal, Dict, List, Any

logger = logging.getLogger(__name__)

# Pre-compiled patterns - compiled once at import
_PUNCTUATION_CLEAN = re.compile(r"\s+([,.!?;:])")
_PUNCTUATION_SPACE = re.compile(r"([,.!?;:])([a-zA-Z])")
_WHITESPACE = re.compile(r"\s+")
_EXCESSIVE_COMMA = re.compile(r",+")

LatexMode = Literal["off", "safe", "math"]


@dataclass(frozen=True)
class FormattingView:
    """Immutable formatting configuration."""

    structure: Literal["paragraphs", "bullets"]
    sentences_per_paragraph: int
    latex_mode: LatexMode
    remove_fillers: bool


# Pre-defined views - frozen
VIEWS: dict[str, FormattingView] = {
    "auto": FormattingView("paragraphs", 2, "safe", False),
    "paragraphs": FormattingView("paragraphs", 3, "safe", False),
    "minimal": FormattingView("paragraphs", 5, "safe", False),
    "bullets": FormattingView("bullets", 2, "safe", False),
    "thinking_session": FormattingView("paragraphs", 4, "safe", True),
    "meeting_notes": FormattingView("bullets", 2, "off", True),
    "study_notes": FormattingView("paragraphs", 3, "math", True),
}

# Base transition starters
_BASE_TRANSITIONS: FrozenSet[str] = frozenset(
    [
        "however",
        "furthermore",
        "moreover",
        "additionally",
        "in conclusion",
        "finally",
        "next",
        "then",
        "after that",
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
    ]
)

# View-specific transition overrides
_VIEW_OVERRIDES: Dict[str, Dict[str, List[str]]] = {
    "thinking_session": {"add": [], "remove": ["then", "after that"]},
    "meeting_notes": {
        "add": ["so the next thing", "action item", "we need to"],
        "remove": [],
    },
    "study_notes": {"add": [], "remove": []},
}

# LaTeX maps - use dict for proper escaping
SAFE_LATEX = {
    "alpha": r"$\alpha$",
    "beta": r"$\beta$",
    "gamma": r"$\gamma$",
    "delta": r"$\delta$",
    "sigma": r"$\sigma$",
    "theta": r"$\theta$",
    "lambda": r"$\lambda$",
    "omega": r"$\omega$",
    "plus or minus": r"$\pm$",
    "squared": r"$^2$",
    "cubed": r"$^3$",
    "greater than or equal to": r"$\ge$",
    "less than or equal to": r"$\le$",
}

MATH_LATEX = {"pi": r"$\pi$"}

# Strict fillers
STRICT_FILLERS: FrozenSet[str] = frozenset(["um", "uh", "er", "ah"])

# Common transcription error fixes
_COMMON_ERRORS = {
    "gonna": "going to",
    "wanna": "want to",
    "gotta": "got to",
}


class TextFormatter:
    """
    Single-pass text formatter.
    O(n) where n = text length.
    """

    def __init__(self, view: str = "auto"):
        self._view = VIEWS.get(view, VIEWS["auto"])
        # Pre-compile view-specific transition pattern
        self._transition_pattern = self._build_transition_pattern()

    def _build_transition_pattern(self) -> re.Pattern:
        """Build transition detection pattern once."""
        starters = list(_BASE_TRANSITIONS)
        pattern = rf"^(?:{'|'.join(re.escape(s) for s in starters)})\b"
        return re.compile(pattern, re.IGNORECASE)

    def format(self, text: str) -> str:
        """Main entry point - O(n)."""
        if not text:
            return ""

        # Single-pass pipeline
        text = self._normalize(text)

        if self._view.remove_fillers:
            text = self._remove_fillers(text)

        if self._view.latex_mode != "off":
            text = self._apply_latex(text)

        # Structure
        if self._view.structure == "bullets":
            return self._to_bullets(text)
        return self._to_paragraphs(text)

    def format_segments(self, segments: list[dict]) -> str:
        """Format from segments - O(n)."""
        raw = " ".join(seg.get("text", "") for seg in segments).strip()
        return self.format(raw)

    def format_structure(self, segments: List[Dict[str, Any]], style: str = "auto") -> str:
        """Apply structural formatting to segments."""
        return self.format_segments(segments)

    def format_text(self, text: str, style: str = "auto") -> str:
        """Format raw text directly."""
        return self.format(text)

    def format_with_custom_structure(self, text: str, max_sentences_per_paragraph: int = 3) -> str:
        """Format text with custom paragraph limit."""
        original = self._view.sentences_per_paragraph
        self._view.sentences_per_paragraph = max_sentences_per_paragraph
        result = self.format(text)
        self._view.sentences_per_paragraph = original
        return result

    def format_as_bullets(self, text: str) -> str:
        """Format as bullets."""
        original = self._view.structure
        self._view.structure = "bullets"
        result = self.format(text)
        self._view.structure = original
        return result

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text).strip()
        text = self._fix_common_errors(text)
        text = self._remove_fillers(text)
        text = re.sub(r",+", ",", text)
        return text.strip()

    def _normalize(self, text: str) -> str:
        """Normalize whitespace and punctuation - O(n)."""
        # Capitalize first letter
        m = re.search(r"[A-Za-z]", text)
        if m:
            text = text[: m.start()] + text[m.start()].upper() + text[m.start() + 1 :]

        # Ensure trailing punctuation
        stripped = text.rstrip()
        if stripped and stripped[-1] not in ".!?":
            text = stripped + "."
        else:
            text = stripped

        # Clean punctuation spacing
        text = _PUNCTUATION_CLEAN.sub(r"\1", text)
        text = _PUNCTUATION_SPACE.sub(r"\1 \2", text)

        return text

    def _remove_fillers(self, text: str) -> str:
        """Remove fillers - O(n)."""
        words = text.split()
        cleaned = [w for w in words if w.strip(".,!?;:").lower() not in STRICT_FILLERS]
        return " ".join(cleaned)

    def _fix_common_errors(self, text: str) -> str:
        """Fix common transcription errors."""
        for k, v in _COMMON_ERRORS.items():
            text = re.sub(rf"\b{re.escape(k)}\b", v, text, flags=re.IGNORECASE)
        return text

    def _indicates_long_pause(self, text: str) -> bool:
        """Check if text indicates a pause/topic change."""
        if len(text.split()) <= 2:
            return False
        return bool(self._transition_pattern.match(text.strip()))

    def _apply_latex(self, text: str) -> str:
        """Apply LaTeX conversion - O(n)."""
        mapping = SAFE_LATEX.copy()
        if self._view.latex_mode == "math":
            mapping.update(MATH_LATEX)

        for term, latex in mapping.items():
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            # Use string replacement to avoid $ being interpreted as template
            text = pattern.sub(lambda m: latex, text)

        return text

    def _split_sentences(self, text: str) -> list[str]:
        """Split into sentences - O(n)."""
        # Avoid splitting after titles/initials
        pattern = r"(?<!\bMrs\.)(?<!\b(?:Mr|Ms|Dr)\.)(?<!\b[ap]\.m\.)(?<!\b[A-Z]\.)(?<=[.!?])\s+"
        parts = re.split(pattern, text)
        return [p for p in parts if p.strip()]

    def _to_paragraphs(self, text: str) -> str:
        """Convert to paragraphs - O(n)."""
        sentences = self._split_sentences(text)
        paragraphs = []
        current = []

        for sent in sentences:
            if not current:
                current.append(sent)
                continue

            # Check limit or transition
            if len(
                current
            ) >= self._view.sentences_per_paragraph or self._transition_pattern.match(
                sent.strip()
            ):
                paragraphs.append(" ".join(current))
                current = [sent]
            else:
                current.append(sent)

        if current:
            paragraphs.append(" ".join(current))

        return "\n\n".join(paragraphs)

    def _to_bullets(self, text: str) -> str:
        """Convert to bullets - O(n)."""
        sentences = self._split_sentences(text)
        bullets = []
        current = []

        for sent in sentences:
            if not current:
                current.append(sent)
            elif self._transition_pattern.match(sent.strip()):
                bullets.append(" ".join(current))
                current = [sent]
            else:
                current.append(sent)

        if current:
            bullets.append(" ".join(current))

        return "\n".join(f"* {b}" for b in bullets)


def get_formatter(view: str = "auto") -> TextFormatter:
    """Get formatter with specified view."""
    return TextFormatter(view)
