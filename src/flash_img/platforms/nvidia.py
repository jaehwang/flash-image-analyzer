"""NVIDIA Tegra platform-specific flash image analyzer."""

import struct
from dataclasses import dataclass
from typing import BinaryIO, List, Optional

from ..analyzers.filesystem import FilesystemAnalyzer
from ..core.analyzer import ImageAnalyzer
from ..core.exceptions import AnalysisError, UnsupportedFormatError
from ..core.models import AnalysisResult, ImageType, PartitionInfo


@dataclass
class BCTHeader:
    """NVIDIA Boot Configuration Table header structure."""

    magic: bytes
    version: int
    oem_data_size: int
    customer_data_size: int
    reserved: int


@dataclass
class TegraPartitionEntry:
    """NVIDIA Tegra partition table entry."""

    name: str
    offset: int
    size: int
    attributes: int
    image_type: ImageType


class NVIDIAAnalyzer(ImageAnalyzer):
    """Analyzer for NVIDIA Tegra flash images."""

    # Known NVIDIA/Tegra magic signatures
    NVIDIA_MAGICS = [
        b"NVDA",  # NVIDIA signature
        b"TEGR",  # Tegra signature
        b"BCT\x00",  # Boot Configuration Table
        b"NV3P",  # NV3P protocol signature
    ]

    # GPT header signature
    GPT_SIGNATURE = b"EFI PART"

    def can_handle(self, f: BinaryIO) -> bool:
        """Check if this is an NVIDIA Tegra flash image."""
        f.seek(0)

        # Check for NVIDIA signatures at the beginning
        header = f.read(512)

        # Check for known NVIDIA magic numbers
        for magic in self.NVIDIA_MAGICS:
            if magic in header:
                return True

        # Check for GPT signature (common in Tegra images)
        f.seek(512)  # GPT header is typically at LBA 1 (512 bytes)
        gpt_header = f.read(8)
        if gpt_header == self.GPT_SIGNATURE:
            return True

        # Check for BCT pattern anywhere in first 64KB
        f.seek(0)
        chunk = f.read(65536)
        return any(magic in chunk for magic in self.NVIDIA_MAGICS)

    def analyze(self) -> AnalysisResult:
        """Analyze the NVIDIA Tegra flash image."""
        partitions = []
        warnings = []
        validation_errors = []

        try:
            with open(self.filename, "rb") as f:
                if not self.can_handle(f):
                    raise UnsupportedFormatError("Not a recognized NVIDIA Tegra flash image format")

                # Try to detect BCT first
                bct_info = self._detect_bct(f)
                if bct_info:
                    partitions.append(bct_info)

                # Try GPT partition table
                gpt_partitions = self._parse_gpt_partitions(f)
                if gpt_partitions:
                    partitions.extend(gpt_partitions)
                else:
                    # Fallback to scanning for known partition patterns
                    warnings.append("GPT not found, scanning for partition signatures")
                    partitions.extend(self._scan_nvidia_partitions(f))

            # Calculate totals
            total_partition_size = sum(p.size for p in partitions)
            total_filesystem_used = sum(p.filesystem.used_size for p in partitions if p.filesystem)

            # Validate partitions
            validation_errors.extend(self._validate_partitions(partitions))

        except Exception as e:
            raise AnalysisError(f"Error analyzing NVIDIA Tegra flash image: {e}") from e

        return AnalysisResult(
            filename=self.filename,
            file_size=self.file_size,
            partitions=partitions,
            total_partition_size=total_partition_size,
            total_filesystem_used=total_filesystem_used,
            validation_errors=validation_errors,
            warnings=warnings,
        )

    def _detect_bct(self, f: BinaryIO) -> Optional[PartitionInfo]:
        """Detect and parse Boot Configuration Table."""
        f.seek(0)

        # BCT is typically at the beginning or after some padding
        for offset in [0, 512, 1024, 2048, 4096]:
            f.seek(offset)
            header = f.read(16)

            if len(header) >= 4 and header[:4] in [b"BCT\x00", b"NVDA"]:
                # Found potential BCT
                bct_size = self._estimate_bct_size(f, offset)

                return PartitionInfo(
                    name="BCT",
                    offset=offset,
                    size=bct_size,
                    image_type=ImageType.UNKNOWN,  # BCT is configuration, not code
                )

        return None

    def _estimate_bct_size(self, f: BinaryIO, offset: int) -> int:
        """Estimate BCT size by looking for next partition or data."""
        # BCT is typically 4KB-16KB in size
        # Look for non-zero data patterns to estimate size
        f.seek(offset)
        default_size = 4096  # Default minimum

        for test_size in [4096, 8192, 16384]:
            f.seek(offset + test_size)
            next_data = f.read(512)

            # If we find structured data, BCT likely ends here
            if any(magic in next_data for magic in self.NVIDIA_MAGICS + [self.GPT_SIGNATURE]):
                return test_size

        return default_size * 4  # Maximum reasonable BCT size (16KB)

    def _parse_gpt_partitions(self, f: BinaryIO) -> List[PartitionInfo]:
        """Parse GPT partition table."""
        f.seek(512)  # GPT header at LBA 1
        gpt_header = f.read(92)

        if len(gpt_header) < 92 or gpt_header[:8] != self.GPT_SIGNATURE:
            return []

        # Parse GPT header
        try:
            # GPT header structure (simplified)
            # revision = struct.unpack("<I", gpt_header[8:12])[0]  # Not used
            # header_size = struct.unpack("<I", gpt_header[12:16])[0]  # Not used
            partition_entry_lba = struct.unpack("<Q", gpt_header[72:80])[0]
            num_partition_entries = struct.unpack("<I", gpt_header[80:84])[0]
            partition_entry_size = struct.unpack("<I", gpt_header[84:88])[0]

            partitions = []

            # Read partition entries
            f.seek(partition_entry_lba * 512)
            for i in range(num_partition_entries):
                entry = f.read(partition_entry_size)
                if len(entry) < 128:  # Standard GPT entry size
                    break

                partition = self._parse_gpt_entry(entry, i)
                if partition:
                    # Analyze filesystem if applicable
                    if not self.skip_fs_analysis and partition.size > 1024 * 1024:
                        fs_analyzer = FilesystemAnalyzer()
                        partition.filesystem = fs_analyzer.analyze(
                            f, partition.offset, partition.size
                        )

                    partitions.append(partition)

            return partitions

        except (struct.error, ValueError):
            return []

    def _parse_gpt_entry(self, entry: bytes, index: int) -> Optional[PartitionInfo]:
        """Parse a single GPT partition entry."""
        if len(entry) < 128:
            return None

        # Check if entry is empty (all zeros)
        if entry[:16] == b"\x00" * 16:
            return None

        try:
            # GPT entry structure
            partition_type_guid = entry[:16]
            # unique_partition_guid = entry[16:32]  # Not used
            first_lba = struct.unpack("<Q", entry[32:40])[0]
            last_lba = struct.unpack("<Q", entry[40:48])[0]
            # attributes = struct.unpack("<Q", entry[48:56])[0]  # Not used

            # Partition name is UTF-16LE encoded (72 bytes max)
            name_bytes = entry[56:128]
            name = name_bytes.decode("utf-16le").rstrip("\x00")

            if not name:
                name = f"partition_{index}"

            # Calculate size
            partition_size = (last_lba - first_lba + 1) * 512

            # Detect image type based on name and GUID
            image_type = self._detect_tegra_image_type(name, partition_type_guid)

            return PartitionInfo(
                name=name,
                offset=first_lba * 512,
                size=partition_size,
                image_type=image_type,
            )

        except (struct.error, UnicodeDecodeError):
            return None

    def _detect_tegra_image_type(self, name: str, guid: bytes) -> ImageType:
        """Detect Tegra-specific image types based on partition name and GUID."""
        name_lower = name.lower()

        # NVIDIA Tegra specific partition types
        if "bct" in name_lower:
            return ImageType.UNKNOWN  # Boot Configuration Table
        elif any(x in name_lower for x in ["mb1", "bootloader"]):
            return ImageType.SBL  # First stage bootloader
        elif "mb2" in name_lower or "tegraboot" in name_lower:
            return ImageType.APPSBL  # TegraBoot
        elif "cboot" in name_lower:
            return ImageType.APPSBL  # CPU bootloader
        elif "bpmp" in name_lower:
            return ImageType.RPM  # Boot and Power Management Processor
        elif any(x in name_lower for x in ["tos", "trustzone"]):
            return ImageType.TZ  # Trusted OS
        elif any(x in name_lower for x in ["kernel", "boot"]):
            return ImageType.BOOT
        elif any(x in name_lower for x in ["rootfs", "system", "app"]):
            return ImageType.UNKNOWN  # Filesystem
        elif "recovery" in name_lower:
            return ImageType.BOOT
        else:
            return ImageType.UNKNOWN

    def _scan_nvidia_partitions(self, f: BinaryIO) -> List[PartitionInfo]:
        """Scan for NVIDIA partition signatures when GPT is not available."""
        partitions = []
        offset = 0
        partition_count = 0

        while offset < self.file_size - 512:
            f.seek(offset)
            chunk = f.read(512)

            if len(chunk) < 512:
                break

            # Look for known signatures
            for magic in self.NVIDIA_MAGICS:
                if magic in chunk:
                    magic_offset = chunk.find(magic)
                    actual_offset = offset + magic_offset

                    # Estimate partition size
                    size = self._estimate_partition_size(f, actual_offset)

                    partition = PartitionInfo(
                        name=f"nvidia_partition_{partition_count}",
                        offset=actual_offset,
                        size=size,
                        image_type=ImageType.UNKNOWN,
                    )

                    partitions.append(partition)
                    partition_count += 1

                    # Skip past this partition
                    offset = actual_offset + size
                    break
            else:
                offset += 4096  # Skip 4KB if no signature found

        return partitions

    def _estimate_partition_size(self, f: BinaryIO, offset: int) -> int:
        """Estimate partition size by looking for next signature or end of file."""
        max_scan = min(64 * 1024 * 1024, self.file_size - offset)  # Scan up to 64MB

        f.seek(offset + 512)  # Skip initial signature

        for scan_offset in range(512, max_scan, 4096):
            f.seek(offset + scan_offset)
            chunk = f.read(512)

            # Look for next partition signature
            for magic in self.NVIDIA_MAGICS + [self.GPT_SIGNATURE]:
                if magic in chunk:
                    return scan_offset

        # Default to reasonable size if no next signature found
        return int(min(16 * 1024 * 1024, self.file_size - offset))

    def _validate_partitions(self, partitions: List[PartitionInfo]) -> List[str]:
        """Validate NVIDIA Tegra partition integrity."""
        errors = []

        for partition in partitions:
            # Check if partition fits in file
            if partition.offset + partition.size > self.file_size:
                errors.append(f"{partition.name}: extends beyond file end")

            # Check reasonable size limits (Tegra specific)
            if partition.size > 1024 * 1024 * 1024:  # 1GB seems reasonable max
                errors.append(f"{partition.name}: unusually large ({partition.size} bytes)")

            if partition.size < 512:  # Too small
                errors.append(f"{partition.name}: unusually small ({partition.size} bytes)")

        # Check for overlaps
        sorted_partitions = sorted(partitions, key=lambda p: p.offset)
        for i in range(len(sorted_partitions) - 1):
            current = sorted_partitions[i]
            next_part = sorted_partitions[i + 1]

            current_end = current.offset + current.size
            if current_end > next_part.offset:
                overlap_size = current_end - next_part.offset
                errors.append(
                    f"{current.name} overlaps with {next_part.name} by {overlap_size} bytes"
                )

        return errors
