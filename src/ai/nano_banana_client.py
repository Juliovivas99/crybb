"""
Replicate client for Google nano-banana using the official SDK.
Based on developer's working example.
"""
from __future__ import annotations

import time
from typing import List
import replicate

from src.retry import retry_http


class AIGenerationError(Exception):
    def __init__(self, message: str, prediction_id: str | None = None):
        super().__init__(message)
        self.prediction_id = prediction_id


def run_nano_banana(*, prompt: str, image_urls: List[str], cfg) -> bytes:
    """
    Run nano-banana AI generation using Replicate SDK.
    
    Args:
        prompt: The prompt (ignored, we use hardcoded prompt)
        image_urls: List containing only the user's profile picture URL
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

    # Hardcode the CryBB constants directly in the API call
    CRYBB_STYLE_URL = "https://crybb-assets-p55s0u52l-juliovivas99s-projects.vercel.app/crybb.jpeg"
    CRYBB_PROMPT = "change the clothes of the first character to the clothes of the character in the second image, if needed change his hair color, skin color, eyes color and tattoos in case they are different from the original image. keep the style consistent to the one in the first image.\nVERY IMPORTANT, always keep the tears\n"

    # Ensure correct image order: [CryBB brand image, user profile picture]
    if len(image_urls) >= 1:
        user_pfp_url = image_urls[0]
        final_image_urls = [CRYBB_STYLE_URL, user_pfp_url]
    else:
        raise ValueError("User profile picture URL is missing for AI generation.")

    print(f"CryBB API call: prompt='{CRYBB_PROMPT[:50]}...', images=[0]={CRYBB_STYLE_URL}, [1]={user_pfp_url}")

    try:
        # Use Replicate SDK exactly as developer example
        output = replicate.run(
            "google/nano-banana",
            input={
                "prompt": CRYBB_PROMPT,
                "image_input": final_image_urls,
                "aspect_ratio": "match_input_image",
                "output_format": "jpg"
            }
        )
        
        # Get the image bytes
        image_bytes = output.read()
        print(f"AI generation successful, got {len(image_bytes)} bytes")
        return image_bytes
        
    except Exception as e:
        print(f"Replicate SDK error: {e}")
        raise AIGenerationError(f"Replicate SDK error: {e}")


# Legacy function for backward compatibility
@retry_http
def _post_prediction(*, model: str, token: str, prompt: str, image_urls: List[str]) -> dict:
    """
    Legacy function - no longer used.
    Kept for backward compatibility.
    """
    raise NotImplementedError("Use run_nano_banana() with Replicate SDK instead")