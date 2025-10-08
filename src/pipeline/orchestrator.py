from typing import List
from src.image_processor import ImageProcessor
from src.ai.nano_banana_client import run_nano_banana


def render_placeholder_bytes(pfp_url: str, cfg) -> bytes:
    import requests
    r = requests.get(pfp_url, timeout=cfg.HTTP_TIMEOUT_SECS)
    r.raise_for_status()
    img_bytes = r.content
    return ImageProcessor().render(img_bytes)


class Orchestrator:
    def __init__(self, cfg):
        self.cfg = cfg

    def render(self, *, pfp_url: str, mention_text: str) -> bytes:
        """Legacy method for backward compatibility."""
        mode = (self.cfg.IMAGE_PIPELINE or "ai").lower()
        if mode == "placeholder":
            return render_placeholder_bytes(pfp_url, self.cfg)
        try:
            # Direct AI generation with hardcoded constants
            print(f"Starting AI generation for PFP: {pfp_url}")
            return run_nano_banana(prompt="", image_urls=[pfp_url], cfg=self.cfg)
        except Exception as e:
            print(f"AI generation failed: {e}")
            return render_placeholder_bytes(pfp_url, self.cfg)

    def render_with_urls(self, image_urls: List[str], mention_text: str = "") -> bytes:
        """New method that accepts image URLs list directly."""
        mode = (self.cfg.IMAGE_PIPELINE or "ai").lower()
        if mode == "placeholder":
            # Use second URL for placeholder (target pfp)
            return render_placeholder_bytes(image_urls[1] if len(image_urls) > 1 else image_urls[0], self.cfg)
        try:
            # Direct AI generation with hardcoded constants
            user_pfp = image_urls[1] if len(image_urls) > 1 else image_urls[0]
            print(f"Starting AI generation for PFP: {user_pfp}")
            return run_nano_banana(prompt="", image_urls=[user_pfp], cfg=self.cfg)
        except Exception as e:
            print(f"AI generation failed: {e}")
            # Fallback to placeholder with second URL (target pfp)
            return render_placeholder_bytes(image_urls[1] if len(image_urls) > 1 else image_urls[0], self.cfg)
