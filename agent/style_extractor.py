"""
Extracts style information (palette, typography, timing) from reference media.
"""
from utils.image_utils import extract_dominant_colors


class StyleExtractor:
    def extract_from_analysis(self, analysis: dict) -> dict:
        """Convert raw analysis dict into structured style config."""
        if not analysis:
            return self._defaults()

        chars = analysis.get("characteristics", {})
        return {
            "palette":     analysis.get("palette", self._defaults()["palette"]),
            "style":       chars.get("style", "Modern"),
            "typography":  chars.get("typography", "Sans-serif bold"),
            "rhythm":      chars.get("rhythm", "Medium"),
            "transitions": chars.get("transitions", "Fade"),
            "background":  chars.get("background", "Solid dark"),
            "mood":        chars.get("mood", "Professional"),
            "prompt":      analysis.get("prompt", ""),
        }

    def _defaults(self) -> dict:
        return {
            "palette":     ["#6c63ff", "#00d4aa", "#1a1a1e", "#f0f0f2"],
            "style":       "Modern",
            "typography":  "Sans-serif bold",
            "rhythm":      "Medium",
            "transitions": "Fade",
            "background":  "Solid dark",
            "mood":        "Professional",
            "prompt":      "",
        }
