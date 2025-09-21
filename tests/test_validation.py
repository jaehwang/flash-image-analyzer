"""Tests for validation utilities."""

import os
import tempfile

from gangimg.utils.validation import validate_gang_image


class TestValidation:
    """Test validation utilities."""

    def test_validate_gang_image_valid_file(self) -> None:
        """Test validation with valid file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"A" * 2048)  # 2KB file
            tmp.flush()

            try:
                is_valid, errors = validate_gang_image(tmp.name)
                assert is_valid
                assert len(errors) == 0
            finally:
                os.unlink(tmp.name)

    def test_validate_gang_image_too_small(self) -> None:
        """Test validation with too small file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"A" * 512)  # 512 bytes (too small)
            tmp.flush()

            try:
                is_valid, errors = validate_gang_image(tmp.name)
                assert not is_valid
                assert "too small" in str(errors).lower()
            finally:
                os.unlink(tmp.name)

    def test_validate_gang_image_nonexistent(self) -> None:
        """Test validation with nonexistent file."""
        is_valid, errors = validate_gang_image("/nonexistent/file.bin")
        assert not is_valid
        assert len(errors) > 0
