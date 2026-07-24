from typing import Tuple

class LineSplitter:
    """Intelligently splits long text into two 16-character lines for 1602A displays."""

    @staticmethod
    def split_text(text: str) -> Tuple[str, str]:
        text = text.strip()
        if len(text) <= 16:
            return text, ""

        # Find best space or punctuation near the midpoint (character 16)
        split_idx = text.rfind(" ", 0, 16)
        if split_idx == -1:
            split_idx = 16  # Force split if no space exists

        line1 = text[:split_idx].strip()
        line2 = text[split_idx:].strip()[:16]

        return line1, line2