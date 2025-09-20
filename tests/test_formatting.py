"""Tests for formatting utilities."""

from gangimg.utils.formatting import format_size
from gangimg.core.models import AnalysisResult, PartitionInfo, ImageType


class TestFormatting:
    """Test formatting utilities."""

    def test_format_size_bytes(self):
        """Test formatting bytes."""
        assert format_size(512) == "512B"
        assert format_size(1023) == "1023B"

    def test_format_size_kb(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == "1.0KB"
        assert format_size(2048) == "2.0KB"
        assert format_size(1536) == "1.5KB"

    def test_format_size_mb(self):
        """Test formatting megabytes."""
        assert format_size(1024 * 1024) == "1.0MB"
        assert format_size(1024 * 1024 * 2) == "2.0MB"
        assert format_size(1024 * 1024 + 512 * 1024) == "1.5MB"

    def test_format_size_gb(self):
        """Test formatting gigabytes."""
        assert format_size(1024 * 1024 * 1024) == "1.0GB"
        assert format_size(1024 * 1024 * 1024 * 2) == "2.0GB"

    def test_format_size_zero(self):
        """Test formatting zero size."""
        assert format_size(0) == "0B"