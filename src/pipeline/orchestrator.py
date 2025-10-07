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
        mode = (self.cfg.IMAGE_PIPELINE or "ai").lower()
        if mode == "placeholder":
            return render_placeholder_bytes(pfp_url, self.cfg)
        try:
            # Direct AI generation without separate AIGenerator class
            if not self.cfg.CRYBB_STYLE_URL:
                raise ValueError("CRYBB_STYLE_URL is required for AI pipeline")
            prompt = build_prompt()
            image_urls = [self.cfg.CRYBB_STYLE_URL, pfp_url]
            return run_nano_banana(prompt=prompt, image_urls=image_urls, cfg=self.cfg)
        except Exception:
            return render_placeholder_bytes(pfp_url, self.cfg)


