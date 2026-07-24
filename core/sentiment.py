import re
from typing import Dict, Tuple

class SentimentScorer:
    """Lightweight rule-based sentiment engine for automatic mood assignments."""

    MOOD_PACKS = {
        "romantic": {
            "keywords": [r"\b(love|heart|kiss|hold|adore|forever|yours|baby|sweet|hug)\b"],
            "icon": "\x01", # Heart
        },
        "dark": {
            "keywords": [r"\b(pain|dark|shadow|bleed|die|ghost|grave|dead|fear|cold)\b"],
            "icon": "\x02", # Broken Heart
        },
        "hype": {
            "keywords": [r"\b(fire|burn|lit|wild|party|dance|loud|go|fast|night)\b"],
            "icon": "\x07", # Fire
        },
        "chill": {
            "keywords": [r"\b(star|sky|fly|dream|moon|river|wind|rain|slow|glow)\b"],
            "icon": "\x03", # Star
        },
    }

    @classmethod
    def analyze_text(cls, text: str) -> Tuple[str, float]:
        """Returns (suggested_mood, confidence_score)."""
        scores: Dict[str, int] = {mood: 0 for mood in cls.MOOD_PACKS}
        words = len(text.split())
        
        if words == 0:
            return "chill", 0.0

        for mood, data in cls.MOOD_PACKS.items():
            for pattern in data["keywords"]:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                scores[mood] += matches

        best_mood = max(scores, key=scores.get)
        highest_score = scores[best_mood]

        if highest_score == 0:
            return "chill", 0.20

        confidence = min(round(highest_score / (words * 0.08), 2), 0.99)
        return best_mood, max(confidence, 0.35)