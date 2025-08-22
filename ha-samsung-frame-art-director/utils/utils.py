from io import BytesIO
from typing import Optional, Tuple

from PIL import Image, ImageOps


class Utils:
    """Utility helpers for image processing and future TV interactions.

    The constructor accepts placeholders for compatibility with callers that may
    later pass TV IPs or state; these are unused for pure image utilities.
    """

    def __init__(self, tvips: Optional[str], uploaded_files: Optional[list]):
        self.tvips = tvips
        self.uploaded_files = uploaded_files

    def resize_and_crop_image(
        self,
        image_bytes: bytes,
        target_size: Tuple[int, int] = (3840, 2160),
        format_hint: Optional[str] = None,
    ) -> BytesIO:
        """Resize and center-crop an image to exactly target_size without distortion.

        - Preserves aspect ratio using ImageOps.fit (centered crop).
        - Applies EXIF orientation.
        - Returns a BytesIO containing the encoded image data.

        Args:
            image_bytes: Raw bytes of the source image.
            target_size: Desired (width, height) in pixels.
            format_hint: Optional file extension (e.g., "jpg", "png") to control output format.

        Returns:
            BytesIO containing the resized image data.
        """
        with Image.open(BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            fitted = ImageOps.fit(
                image,
                target_size,
                method=Image.LANCZOS,
                centering=(0.5, 0.5),
            )

            output = BytesIO()
            save_format = self._map_format(format_hint) or (image.format or "JPEG")
            params = {}
            if save_format.upper() in {"JPEG", "JPG"}:
                params["quality"] = 95
                params["optimize"] = True

            fitted.save(output, format=save_format, **params)
            output.seek(0)
            return output

    @staticmethod
    def _map_format(format_hint: Optional[str]) -> Optional[str]:
        if not format_hint:
            return None
        fmt = format_hint.strip().lower()
        if fmt in {"jpg", "jpeg"}:
            return "JPEG"
        if fmt == "png":
            return "PNG"
        if fmt == "webp":
            return "WEBP"
        return None


