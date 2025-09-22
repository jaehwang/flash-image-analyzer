"""Tests for CLI module."""


import pytest

from flash_img.cli import create_parser, select_analyzer


class TestCLI:
    """Test CLI functionality."""

    def test_create_parser(self) -> None:
        """Test parser creation."""
        parser = create_parser()
        assert parser.prog == "flash_img"
        assert parser.description == "Analyze embedded system flash images"

    def test_parser_help(self) -> None:
        """Test parser help doesn't crash."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_parser_version(self) -> None:
        """Test version argument."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_select_analyzer_qualcomm(self) -> None:
        """Test selecting Qualcomm analyzer."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp.flush()

            try:
                analyzer = select_analyzer(tmp.name, "qualcomm", False)
                assert analyzer is not None
            finally:
                os.unlink(tmp.name)

    def test_select_analyzer_nvidia(self) -> None:
        """Test selecting NVIDIA analyzer."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp.flush()

            try:
                analyzer = select_analyzer(tmp.name, "nvidia", False)
                assert analyzer is not None
            finally:
                os.unlink(tmp.name)

    def test_select_analyzer_auto_detect(self) -> None:
        """Test auto-detection of analyzer."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp.flush()

            try:
                analyzer = select_analyzer(tmp.name, "auto", False)
                assert analyzer is not None  # Should fall back to Qualcomm
            finally:
                os.unlink(tmp.name)
