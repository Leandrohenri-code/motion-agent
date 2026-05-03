import base64
import os
from pathlib import Path


def image_to_base64(path: str) -> str:
    """Convert an image file to a base64 data URL."""
    ext = Path(path).suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}
    mime = mime_map.get(ext, "jpeg")
    with open(path, "rb") as f:
        data = f.read()
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"


def base64_to_bytes(data_url: str) -> bytes:
    """Strip the data URL prefix and decode base64."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    return base64.b64decode(data_url)


def resize_image(path: str, max_size: int = 1024) -> str:
    """Resize an image to max_size on its longest side. Returns new path."""
    try:
        from PIL import Image
        img = Image.open(path)
        w, h = img.size
        if max(w, h) <= max_size:
            return path
        scale = max_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        out = path.replace(".", "_resized.", 1)
        img.save(out)
        return out
    except Exception:
        return path


def extract_dominant_colors(path: str, n: int = 6) -> list:
    """Extract n dominant hex colors from an image using k-means."""
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(path).convert("RGB").resize((150, 150))
        arr = np.array(img).reshape(-1, 3).astype(float)
        # Simple k-means via PIL quantize
        palette_img = img.quantize(colors=n)
        palette = palette_img.getpalette()[:n * 3]
        colors = []
        for i in range(0, len(palette), 3):
            r, g, b = palette[i], palette[i + 1], palette[i + 2]
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        return colors
    except Exception:
        return ["#6c63ff", "#00d4aa", "#1a1a1e", "#f0f0f2", "#ff4d6d", "#ffb340"]
