"""
Image processing module for CryBB Maker Bot.
Now placeholder-only: overlay and facial landmark logic removed.
"""
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
from .config import Config


class ImageProcessor:
    """Image processing utilities (placeholder-only)."""

    def apply_placeholder(self, pfp_bytes: bytes, watermark: Optional[str] = None) -> bytes:
        """Apply placeholder transformation with light enhancements and optional watermark."""
        try:
            image = Image.open(io.BytesIO(pfp_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Enhance contrast slightly
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)

            # Enhance saturation slightly
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)

            if watermark:
                image = self._add_watermark(image, watermark)

            output = io.BytesIO()
            image.save(output, format='JPEG', quality=Config.JPEG_QUALITY, optimize=True)
            return output.getvalue()
        except Exception as e:
            print(f"Error applying placeholder transformation: {e}")
            raise

    def render(self, pfp_bytes: bytes, watermark: Optional[str] = None) -> bytes:
        """Main render function: returns placeholder image bytes."""
        return self.apply_placeholder(pfp_bytes, watermark)

    def _add_watermark(self, image: Image.Image, watermark_text: str) -> Image.Image:
        """Add watermark text to bottom-right of the image."""
        try:
            draw = ImageDraw.Draw(image)
            try:
                font_size = max(12, image.width // 30)
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = image.width - text_width - 10
            y = image.height - text_height - 10

            draw.text((x + 1, y + 1), watermark_text, font=font, fill=(0, 0, 0))
            draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255))
            return image
        except Exception as e:
            print(f"Error adding watermark: {e}")
            return image
