"""
Replicate client for Google nano-banana using the official SDK.
Systematically tries different API schemas until one works.
"""
from __future__ import annotations

import time
import requests
from typing import List
import replicate

from src.retry import retry_http


class AIGenerationError(Exception):
    def __init__(self, message: str, prediction_id: str | None = None):
        super().__init__(message)
        self.prediction_id = prediction_id


def _head_ok(url: str) -> bool:
    """Check if URL is accessible with HEAD request."""
    try:
        r = requests.head(url, timeout=6)
        return 200 <= r.status_code < 300
    except Exception:
        return False


def run_nano_banana(*, prompt: str, image_urls: List[str], cfg) -> bytes:
    """
    Run nano-banana AI generation using Replicate SDK.
    Tries multiple API schemas until one succeeds.
    
    Args:
        prompt: The prompt (ignored, we use hardcoded prompt)
        image_urls: List containing [style_url, pfp_url] in that order
        cfg: Configuration object
    
    Returns:
        Generated image bytes
    """
    token = cfg.REPLICATE_API_TOKEN
    if not token:
        raise AIGenerationError("REPLICATE_API_TOKEN missing")
    
    # Set the Replicate API token for the SDK
    import os
    os.environ["REPLICATE_API_TOKEN"] = token

    # Validate input
    assert len(image_urls) == 2, f"Expected 2 URLs, got {len(image_urls)}"
    style_url, pfp_url = image_urls
    
    print(f"[AI] model=google/nano-banana style={style_url} pfp={pfp_url}")
    
    # Validate URLs
    if not _head_ok(style_url):
        raise ValueError(f"[AI] BAD_URL {style_url}")
    if not _head_ok(pfp_url):
        raise ValueError(f"[AI] BAD_URL {pfp_url}")
    
    # Hardcode the CryBB constants
    CRYBB_PROMPT = "change the clothes of the first character to the clothes of the character in the second image, if needed change his hair color, skin color, eyes color and tattoos in case they are different from the original image. keep the style consistent to the one in the first image.\nVERY IMPORTANT, always keep the tears\n"

    # Try different schemas in order
    schemas = [
        # Schema 1: image_urls array
        {
            "input": {
                "image_urls": [style_url, pfp_url],
                "prompt": CRYBB_PROMPT
            }
        },
        # Schema 2: images array  
        {
            "input": {
                "images": [style_url, pfp_url],
                "prompt": CRYBB_PROMPT
            }
        },
        # Schema 3: separate image_1, image_2
        {
            "input": {
                "image_1": style_url,
                "image_2": pfp_url,
                "prompt": CRYBB_PROMPT
            }
        },
        # Schema 4: image_input array (original)
        {
            "input": {
                "image_input": [style_url, pfp_url],
                "prompt": CRYBB_PROMPT,
                "aspect_ratio": "match_input_image",
                "output_format": "jpg"
            }
        }
    ]

    last_error = None
    
    for i, schema in enumerate(schemas, 1):
        try:
            print(f"[AI] attempt schema=S{i} payload=<redacted>")
            
            # Use Replicate SDK with current schema
            output = replicate.run("google/nano-banana", **schema)
            
            # Get the image bytes
            image_bytes = output.read()
            print(f"[AI] completed bytes={len(image_bytes)}")
            return image_bytes
            
        except Exception as e:
            error_msg = str(e)
            print(f"[AI] schema S{i} failed: {error_msg}")
            last_error = e
            
            # If it's E006 or 400, try next schema
            if "E006" in error_msg or "400" in error_msg:
                continue
            else:
                # Other errors, re-raise immediately
                raise AIGenerationError(f"Replicate SDK error: {e}")
    
    # All schemas failed
    raise RuntimeError(f"[AI] E006 after all schemas. Last error: {last_error}")


# Legacy function for backward compatibility
@retry_http
def _post_prediction(*, model: str, token: str, prompt: str, image_urls: List[str]) -> dict:
    """
    Legacy function - no longer used.
    Kept for backward compatibility.
    """
    raise NotImplementedError("Use run_nano_banana() with Replicate SDK instead")