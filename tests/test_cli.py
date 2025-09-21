"""Tests for CLI module."""

from unittest.mock import patch

import pytest

from gangimg.cli import create_parser, select_analyzer


class TestCLI:
    """Test CLI functionality."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser.prog == "gangimg"
        assert parser.description == "Analyze embedded system gang images"

    def test_parser_help(self):
        """Test parser help doesn't crash."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_parser_version(self):
        """Test version argument."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_select_analyzer_qualcomm(self):
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
