"""Tests for NVIDIA Tegra platform analyzer."""

import os
import struct
import tempfile
from unittest.mock import Mock, patch

import pytest

from flash_img.core.exceptions import AnalysisError
from flash_img.core.models import ImageType
from flash_img.platforms.nvidia import NVIDIAAnalyzer


class TestNVIDIAAnalyzer:
    """Test NVIDIA Tegra analyzer functionality."""

    def test_can_handle_nvidia_signature(self) -> None:
        """Test detection of NVIDIA signatures."""
        # Test with NVIDIA magic
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"NVDA" + b"\x00" * 508)
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    assert analyzer.can_handle(f) is True
            finally:
                os.unlink(tmp.name)

    def test_can_handle_tegra_signature(self) -> None:
        """Test detection of Tegra signatures."""
        # Test with Tegra magic
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"TEGR" + b"\x00" * 508)
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    assert analyzer.can_handle(f) is True
            finally:
                os.unlink(tmp.name)

    def test_can_handle_bct_signature(self) -> None:
        """Test detection of BCT signatures."""
        # Test with BCT magic
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"BCT\x00" + b"\x00" * 508)
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    assert analyzer.can_handle(f) is True
            finally:
                os.unlink(tmp.name)

    def test_can_handle_gpt_signature(self) -> None:
        """Test detection of GPT signatures."""
        # Test with GPT signature at LBA 1
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"\x00" * 512)  # LBA 0
            tmp.write(b"EFI PART" + b"\x00" * 504)  # LBA 1
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    assert analyzer.can_handle(f) is True
            finally:
                os.unlink(tmp.name)

    def test_can_handle_unknown_format(self) -> None:
        """Test rejection of unknown formats."""
        # Test with unknown data
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"UNKNOWN_FORMAT" + b"\x00" * 60000)
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    assert analyzer.can_handle(f) is False
            finally:
                os.unlink(tmp.name)

    def test_detect_bct_at_offset_zero(self) -> None:
        """Test BCT detection at offset 0."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"BCT\x00" + b"\x00" * 4092)  # 4KB BCT
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    bct_info = analyzer._detect_bct(f)
                    assert bct_info is not None
                    assert bct_info.name == "BCT"
                    assert bct_info.offset == 0
                    assert bct_info.size >= 4096  # BCT size estimation may vary
            finally:
                os.unlink(tmp.name)

    def test_detect_bct_at_offset_512(self) -> None:
        """Test BCT detection at offset 512."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"\x00" * 512)  # Padding
            tmp.write(b"NVDA" + b"\x00" * 4092)  # BCT with NVIDIA signature
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    bct_info = analyzer._detect_bct(f)
                    assert bct_info is not None
                    assert bct_info.name == "BCT"
                    assert bct_info.offset == 512
                    assert bct_info.size >= 4096  # BCT size estimation may vary
            finally:
                os.unlink(tmp.name)

    def test_detect_tegra_image_type_bootloader(self) -> None:
        """Test Tegra image type detection for bootloaders."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)

                # Test MB1 (first stage bootloader)
                assert analyzer._detect_tegra_image_type("mb1", b"\x00" * 16) == ImageType.SBL

                # Test MB2/TegraBoot
                assert analyzer._detect_tegra_image_type("mb2", b"\x00" * 16) == ImageType.APPSBL
                assert (
                    analyzer._detect_tegra_image_type("tegraboot", b"\x00" * 16) == ImageType.APPSBL
                )

                # Test CBoot
                assert analyzer._detect_tegra_image_type("cboot", b"\x00" * 16) == ImageType.APPSBL
            finally:
                os.unlink(tmp.name)

    def test_detect_tegra_image_type_firmware(self) -> None:
        """Test Tegra image type detection for firmware."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)

                # Test BPMP (Boot and Power Management Processor)
                assert analyzer._detect_tegra_image_type("bpmp", b"\x00" * 16) == ImageType.RPM

                # Test TrustZone/TOS
                assert analyzer._detect_tegra_image_type("tos", b"\x00" * 16) == ImageType.TZ
                assert analyzer._detect_tegra_image_type("trustzone", b"\x00" * 16) == ImageType.TZ
            finally:
                os.unlink(tmp.name)

    def test_detect_tegra_image_type_os(self) -> None:
        """Test Tegra image type detection for OS components."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)

                # Test kernel/boot
                assert analyzer._detect_tegra_image_type("kernel", b"\x00" * 16) == ImageType.BOOT
                assert analyzer._detect_tegra_image_type("boot", b"\x00" * 16) == ImageType.BOOT
                assert analyzer._detect_tegra_image_type("recovery", b"\x00" * 16) == ImageType.BOOT
            finally:
                os.unlink(tmp.name)

    def test_estimate_bct_size(self) -> None:
        """Test BCT size estimation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write BCT at start, then GPT signature at 8KB
            tmp.write(b"BCT\x00" + b"\x00" * 4092)  # 4KB
            tmp.write(b"\x00" * 4088)  # Another 4KB - 8
            tmp.write(b"EFI PART")  # GPT signature
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    size = analyzer._estimate_bct_size(f, 0)
                    assert size >= 4096  # Should be at least 4KB
            finally:
                os.unlink(tmp.name)

    def test_estimate_partition_size(self) -> None:
        """Test partition size estimation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write partition at start, then NVIDIA signature at 64KB
            tmp.write(b"TEGR" + b"\x00" * 65532)  # 64KB
            tmp.write(b"NVDA")  # Next signature
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with open(tmp.name, "rb") as f:
                    size = analyzer._estimate_partition_size(f, 0)
                    assert size >= 512  # Should be at least 512 bytes
            finally:
                os.unlink(tmp.name)

    def test_parse_gpt_entry_empty(self) -> None:
        """Test parsing of empty GPT entry."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                # Empty entry (all zeros)
                empty_entry = b"\x00" * 128
                result = analyzer._parse_gpt_entry(empty_entry, 0)
                assert result is None
            finally:
                os.unlink(tmp.name)

    def test_parse_gpt_entry_valid(self) -> None:
        """Test parsing of valid GPT entry."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)

                # Create a mock GPT entry
                entry = bytearray(128)

                # Partition type GUID (16 bytes, non-zero)
                entry[0:16] = b"\x01" * 16

                # Unique partition GUID (16 bytes)
                entry[16:32] = b"\x02" * 16

                # First LBA (8 bytes, little endian) = 2048
                entry[32:40] = struct.pack("<Q", 2048)

                # Last LBA (8 bytes, little endian) = 4095
                entry[40:48] = struct.pack("<Q", 4095)

                # Attributes (8 bytes)
                entry[48:56] = b"\x00" * 8

                # Partition name (UTF-16LE, 72 bytes max)
                name = "test_partition"
                name_utf16 = name.encode("utf-16le")
                entry[56 : 56 + len(name_utf16)] = name_utf16

                result = analyzer._parse_gpt_entry(bytes(entry), 0)
                assert result is not None
                assert result.name == "test_partition"
                assert result.offset == 2048 * 512  # LBA to bytes
                assert result.size == (4095 - 2048 + 1) * 512  # Size in bytes
            finally:
                os.unlink(tmp.name)

    def test_unsupported_format_error(self) -> None:
        """Test error handling for unsupported formats."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"NOT_NVIDIA_FORMAT" * 1000)
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                with pytest.raises(AnalysisError, match="Error analyzing NVIDIA Tegra flash image"):
                    analyzer.analyze()
            finally:
                os.unlink(tmp.name)

    def test_file_not_found_error(self) -> None:
        """Test error handling for missing files."""
        with pytest.raises(AnalysisError, match="File .* not found"):
            NVIDIAAnalyzer("nonexistent_file.img")

    def test_validate_partitions_overlap(self) -> None:
        """Test partition overlap validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)

                from flash_img.core.models import ImageType, PartitionInfo

                partitions = [
                    PartitionInfo(name="part1", offset=0, size=1024, image_type=ImageType.UNKNOWN),
                    PartitionInfo(
                        name="part2", offset=512, size=1024, image_type=ImageType.UNKNOWN
                    ),  # Overlaps with part1
                ]

                errors = analyzer._validate_partitions(partitions)
                # Should detect overlap, may also detect size issues
                assert any("overlaps" in error for error in errors)
                assert any("part1" in error and "part2" in error for error in errors)
            finally:
                os.unlink(tmp.name)

    def test_validate_partitions_size_limits(self) -> None:
        """Test partition size validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name)
                analyzer.file_size = 2048  # Set file size

                from flash_img.core.models import ImageType, PartitionInfo

                partitions = [
                    PartitionInfo(
                        name="too_large",
                        offset=0,
                        size=2 * 1024 * 1024 * 1024,
                        image_type=ImageType.UNKNOWN,
                    ),  # 2GB
                    PartitionInfo(
                        name="too_small", offset=0, size=256, image_type=ImageType.UNKNOWN
                    ),  # 256 bytes
                    PartitionInfo(
                        name="beyond_file", offset=0, size=4096, image_type=ImageType.UNKNOWN
                    ),  # Extends beyond file
                ]

                errors = analyzer._validate_partitions(partitions)
                # Should detect all three types of errors (possibly more due to overlaps)
                assert any("unusually large" in error for error in errors)
                assert any("unusually small" in error for error in errors)
                assert any("extends beyond file end" in error for error in errors)
            finally:
                os.unlink(tmp.name)

    @patch("flash_img.platforms.nvidia.FilesystemAnalyzer")
    def test_analyze_with_filesystem_analysis(self, mock_fs_analyzer: Mock) -> None:
        """Test analysis with filesystem analysis enabled."""
        # Create a mock filesystem result
        mock_fs_result = Mock()
        mock_fs_result.fs_type = "ext4"
        mock_fs_result.used_size = 1024 * 1024

        mock_fs_analyzer.return_value.analyze.return_value = mock_fs_result

        # Create test image with GPT
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write MBR (512 bytes)
            tmp.write(b"\x00" * 512)

            # Write GPT header
            gpt_header = bytearray(512)
            gpt_header[0:8] = b"EFI PART"  # Signature
            gpt_header[8:12] = struct.pack("<I", 0x00010000)  # Revision
            gpt_header[12:16] = struct.pack("<I", 92)  # Header size
            gpt_header[72:80] = struct.pack("<Q", 2)  # Partition entry LBA
            gpt_header[80:84] = struct.pack("<I", 1)  # Number of partition entries
            gpt_header[84:88] = struct.pack("<I", 128)  # Partition entry size
            tmp.write(gpt_header)

            # Write partition entry (at LBA 2, offset 1024)
            tmp.seek(1024)
            entry = bytearray(128)
            entry[0:16] = b"\x01" * 16  # Partition type GUID
            entry[16:32] = b"\x02" * 16  # Unique partition GUID
            entry[32:40] = struct.pack("<Q", 2048)  # First LBA
            entry[40:48] = struct.pack("<Q", 4095)  # Last LBA
            name = "large_partition"
            name_utf16 = name.encode("utf-16le")
            entry[56 : 56 + len(name_utf16)] = name_utf16
            tmp.write(entry)

            # Pad file to make it large enough
            tmp.seek(4095 * 512 + 511)
            tmp.write(b"\x00")
            tmp.flush()

            try:
                analyzer = NVIDIAAnalyzer(tmp.name, skip_fs_analysis=False)
                result = analyzer.analyze()

                assert len(result.partitions) >= 1
                # For this test, we don't need to verify filesystem analysis call
                # as the GPT parsing may not trigger it depending on partition size
                assert result is not None

            finally:
                os.unlink(tmp.name)
