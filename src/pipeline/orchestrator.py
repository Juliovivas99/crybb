from typing import List
from src.image_processor import ImageProcessor
from src.ai.nano_banana_client import run_nano_banana
from src.ai.prompt_crybb import build_prompt


def render_placeholder_bytes(pfp_url: str, cfg) -> bytes:
    import requests
    r = requests.get(pfp_url, timeout=cfg.HTTP_TIMEOUT_SECS)
    r.raise_for_status()
    img_bytes = r.content
    return ImageProcessor().render(img_bytes, watermark=cfg.WATERMARK_TEXT)


class Orchestrator:
    def __init__(self, cfg):
        self.cfg = cfg

    def render(self, *, pfp_url: str, mention_text: str) -> bytes:
        """Legacy method for backward compatibility."""
        mode = (self.cfg.IMAGE_PIPELINE or "ai").lower()
        if mode == "placeholder":
            return render_placeholder_bytes(pfp_url, self.cfg)
        try:
            # Direct AI generation without separate AIGenerator class
            if not self.cfg.CRYBB_STYLE_URL:
                raise ValueError("CRYBB_STYLE_URL is required for AI pipeline")
            prompt = build_prompt()
            # Fixed: enforce [style, pfp] order
            image_urls = [self.cfg.CRYBB_STYLE_URL, pfp_url]
            print(f"Nano-banana image order: [0]={self.cfg.CRYBB_STYLE_URL}, [1]={pfp_url}")
            return run_nano_banana(prompt=prompt, image_urls=image_urls, cfg=self.cfg)
        except Exception:
            return render_placeholder_bytes(pfp_url, self.cfg)

    def render_with_urls(self, image_urls: List[str], mention_text: str = "") -> bytes:
        """New method that accepts image URLs list directly."""
        mode = (self.cfg.IMAGE_PIPELINE or "ai").lower()
        if mode == "placeholder":
            # Use second URL for placeholder (target pfp)
            return render_placeholder_bytes(image_urls[1] if len(image_urls) > 1 else image_urls[0], self.cfg)
        try:
            if not self.cfg.CRYBB_STYLE_URL:
                raise ValueError("CRYBB_STYLE_URL is required for AI pipeline")
            prompt = build_prompt()
            # Use provided image_urls directly
            print(f"Nano-banana image order: [0]={image_urls[0] if len(image_urls) > 0 else 'N/A'}, [1]={image_urls[1] if len(image_urls) > 1 else 'N/A'}")
            return run_nano_banana(prompt=prompt, image_urls=image_urls, cfg=self.cfg)
        except Exception as e:
            print(f"AI generation failed: {e}")
            # Fallback to placeholder with second URL (target pfp)
            return render_placeholder_bytes(image_urls[1] if len(image_urls) > 1 else image_urls[0], self.cfg)
