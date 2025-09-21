"""Tests for core models."""

from gangimg.core.models import AnalysisResult, FilesystemInfo, ImageType, PartitionInfo


class TestModels:
    """Test core data models."""

    def test_image_type_enum(self):
        """Test ImageType enum values."""
        assert ImageType.SBL.value == "sbl"
        assert ImageType.TZ.value == "tz"
        assert ImageType.UNKNOWN.value == "unknown"

    def test_filesystem_info(self):
        """Test FilesystemInfo dataclass."""
        fs_info = FilesystemInfo(
            fs_type="ext4",
            fs_size=1024000,
            used_size=512000,
            free_size=512000,
            block_size=4096,
            total_blocks=250,
            free_blocks=125,
        )
        assert fs_info.fs_type == "ext4"
        assert fs_info.fs_size == 1024000
        assert fs_info.used_size == 512000

    def test_partition_info(self):
        """Test PartitionInfo dataclass."""
        partition = PartitionInfo(
            name="test_partition",
            offset=0,
            size=1024,
            image_type=ImageType.SBL,
            load_addr=0x40000000,
        )
        assert partition.name == "test_partition"
        assert partition.size == 1024
        assert partition.image_type == ImageType.SBL

    def test_analysis_result(self):
        """Test AnalysisResult dataclass."""
        result = AnalysisResult(
            filename="test.bin",
            file_size=2048,
            partitions=[],
            total_partition_size=0,
            total_filesystem_used=0,
            validation_errors=[],
            warnings=[],
        )
        assert result.filename == "test.bin"
        assert result.file_size == 2048
        assert len(result.partitions) == 0
