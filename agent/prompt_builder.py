"""
Builds optimized prompts from reference analysis results.
"""


class PromptBuilder:
    def build_from_analysis(self, analysis: dict, user_description: str = None) -> str:
        if not analysis:
            return user_description or ""

        chars = analysis.get("characteristics", {})
        palette = analysis.get("palette", [])
        parts = []

        if user_description:
            parts.append(user_description)

        if chars.get("style"):
            parts.append(f"Estilo: {chars['style']}.")
        if chars.get("typography"):
            parts.append(f"Tipografia: {chars['typography']}.")
        if chars.get("rhythm"):
            parts.append(f"Ritmo: {chars['rhythm']}.")
        if chars.get("transitions"):
            parts.append(f"Transições: {chars['transitions']}.")
        if chars.get("background"):
            parts.append(f"Fundo: {chars['background']}.")
        if chars.get("mood"):
            parts.append(f"Atmosfera: {chars['mood']}.")
        if palette:
            parts.append(f"Paleta: {', '.join(palette[:4])}.")

        return " ".join(parts)

    def build_scene_context(self, global_prompt: str, scene_desc: str,
                            scene_num: int, total_scenes: int,
                            style: dict = None) -> str:
        ctx = f"[Cena {scene_num}/{total_scenes}] {scene_desc}"
        if global_prompt:
            ctx = f"{global_prompt}\n\n{ctx}"
        return ctx
