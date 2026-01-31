import pytest
import base64
from PIL import Image
import io

from app.models import stickerUtils


class TestQrCode:
    """Tests for qr_code function."""

    def test_returns_rgb_image(self):
        """Should return an RGB PIL Image."""
        result = stickerUtils.qr_code("test-data")
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_creates_valid_qr_image(self):
        """Should create a valid QR code image with non-zero size."""
        result = stickerUtils.qr_code("12345")
        width, height = result.size
        assert width > 0
        assert height > 0


class TestCreateBaseImage:
    """Tests for _create_base_image function."""

    def test_creates_white_image(self):
        """Should create a white RGB image."""
        result = stickerUtils._create_base_image()
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"
        # Check that it's white (sample center pixel)
        width, height = result.size
        pixel = result.getpixel((width // 2, height // 2))
        assert pixel == (255, 255, 255)

    def test_creates_correct_size(self):
        """Should create image with correct dimensions."""
        result = stickerUtils._create_base_image()
        assert result.size == stickerUtils.IMAGE_SIZE


class TestImageToBase64:
    """Tests for _image_to_base64 function."""

    def test_returns_base64_string(self):
        """Should return a valid base64 encoded string."""
        img = Image.new("RGB", (100, 100), color="white")
        result = stickerUtils._image_to_base64(img)
        assert isinstance(result, str)
        # Verify it's valid base64 by decoding
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_base64_can_be_converted_back_to_image(self):
        """Should produce base64 that can be decoded back to an image."""
        img = Image.new("RGB", (100, 100), color="red")
        result = stickerUtils._image_to_base64(img)

        # Decode and recreate image
        decoded = base64.b64decode(result)
        img_buffer = io.BytesIO(decoded)
        restored_img = Image.open(img_buffer)

        assert restored_img.size == (100, 100)
        assert restored_img.mode == "RGB"
