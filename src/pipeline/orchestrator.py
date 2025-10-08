from typing import List
from src.image_processor import ImageProcessor
from src.ai.nano_banana_client import run_nano_banana


def normalize_pfp_url(pfp_url: str) -> str:
    """Normalize profile picture URL to ensure it's accessible."""
    # Remove any size parameters and ensure we get a good quality image
    if "_400x400" in pfp_url:
        return pfp_url.replace("_400x400", "_400x400")
    return pfp_url


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
        
        # Prepare inputs with proper order
        style = self.cfg.CRYBB_STYLE_URL
        assert style, "CRYBB_STYLE_URL must be set"
        
        pfp = normalize_pfp_url(pfp_url)
        assert pfp, "Profile picture URL must be provided"
        
        image_urls = [style, pfp]  # style FIRST
        print(f"[AI] order-ok style_first")
        
        # No fallback - let exceptions bubble up
        print(f"Starting AI generation for PFP: {pfp}")
        return run_nano_banana(prompt="", image_urls=image_urls, cfg=self.cfg)

    def render_with_urls(self, image_urls: List[str], mention_text: str = "") -> bytes:
        """New method that accepts image URLs list directly."""
        mode = (self.cfg.IMAGE_PIPELINE or "ai").lower()
        if mode == "placeholder":
            # Use second URL for placeholder (target pfp)
            return render_placeholder_bytes(image_urls[1] if len(image_urls) > 1 else image_urls[0], self.cfg)
        
        # Prepare inputs with proper order
        style = self.cfg.CRYBB_STYLE_URL
        assert style, "CRYBB_STYLE_URL must be set"
        
        user_pfp = image_urls[1] if len(image_urls) > 1 else image_urls[0]
        pfp = normalize_pfp_url(user_pfp)
        assert pfp, "Profile picture URL must be provided"
        
        image_urls_ordered = [style, pfp]  # style FIRST
        print(f"[AI] order-ok style_first")
        
        # No fallback - let exceptions bubble up
        print(f"Starting AI generation for PFP: {pfp}")
        return run_nano_banana(prompt="", image_urls=image_urls_ordered, cfg=self.cfg)