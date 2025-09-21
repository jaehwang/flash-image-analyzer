"""Qualcomm platform-specific gang image analyzer."""

import struct
from dataclasses import dataclass
from typing import BinaryIO, Optional

from ..analyzers.filesystem import FilesystemAnalyzer
from ..core.analyzer import GangImageAnalyzer
from ..core.exceptions import AnalysisError, UnsupportedFormatError
from ..core.models import AnalysisResult, ImageType, PartitionInfo


@dataclass
class MBNHeader:
    """Qualcomm MBN Header structure."""

    image_id: int
    header_vsn_num: int
    image_src: int
    image_dest_ptr: int
    image_size: int
    code_size: int
    signature_ptr: int
    signature_size: int
    cert_chain_ptr: int
    cert_chain_size: int


class QualcommAnalyzer(GangImageAnalyzer):
    """Analyzer for Qualcomm gang images."""

    def can_handle(self, f: BinaryIO) -> bool:
        """Check if this is a Qualcomm gang image."""
        f.seek(0)
        magic = f.read(4)

        # Common Qualcomm gang image magic numbers
        known_magics = [
            b"\x7f\x45\x4c\x46",  # ELF
            b"GANG",  # Custom gang header
            b"QCOM",  # Qualcomm header
            b"\x00\x00\x00\x00",  # Some images start with zeros
        ]

        return magic in known_magics

    def analyze(self) -> AnalysisResult:
        """Analyze the Qualcomm gang image."""
        partitions = []
        warnings = []
        validation_errors = []

        try:
            with open(self.filename, "rb") as f:
                if not self.can_handle(f):
                    raise UnsupportedFormatError("Not a recognized Qualcomm gang image format")

                # Try to detect gang image format
                if self._detect_gang_format(f):
                    partitions = self._parse_gang_image(f)
                else:
                    # Fallback to scanning for MBN headers
                    warnings.append("Gang header not found, scanning for individual MBN images")
                    partitions = self._scan_mbn_images(f)

            # Calculate totals
            total_partition_size = sum(p.size for p in partitions)
            total_filesystem_used = sum(p.filesystem.used_size for p in partitions if p.filesystem)

            # Validate partitions
            validation_errors.extend(self._validate_partitions(partitions))

        except Exception as e:
            raise AnalysisError(f"Error analyzing Qualcomm gang image: {e}") from e

        return AnalysisResult(
            filename=self.filename,
            file_size=self.file_size,
            partitions=partitions,
            total_partition_size=total_partition_size,
            total_filesystem_used=total_filesystem_used,
            validation_errors=validation_errors,
            warnings=warnings,
        )

    def _detect_gang_format(self, f: BinaryIO) -> bool:
        """Detect if this is a proper gang image with header."""
        f.seek(0)
        magic = f.read(4)

        # Common Qualcomm gang image magic numbers
        known_magics = [
            b"\x7f\x45\x4c\x46",  # ELF
            b"GANG",  # Custom gang header
            b"QCOM",  # Qualcomm header
            b"\x00\x00\x00\x00",  # Some images start with zeros
        ]

        return magic in known_magics

    def _parse_gang_image(self, f: BinaryIO) -> list[PartitionInfo]:
        """Parse gang image with proper header."""
        f.seek(0)

        # Try to parse as ELF format first
        if self._try_parse_elf(f):
            return self.partitions

        # Try custom gang format
        return self._parse_custom_gang(f)

    def _try_parse_elf(self, f: BinaryIO) -> bool:
        """Try to parse as ELF format."""
        f.seek(0)
        elf_header = f.read(52)  # ELF header size

        if len(elf_header) < 52 or elf_header[:4] != b"\x7f\x45\x4c\x46":
            return False

        # Parse ELF header
        e_phoff = struct.unpack("<I", elf_header[28:32])[0]  # Program header offset
        e_phentsize = struct.unpack("<H", elf_header[42:44])[0]  # Program header entry size
        e_phnum = struct.unpack("<H", elf_header[44:46])[0]  # Number of program headers

        partitions = []

        # Parse program headers
        f.seek(e_phoff)
        for i in range(e_phnum):
            ph = f.read(e_phentsize)
            if len(ph) >= 32:
                p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz = struct.unpack(
                    "<IIIIII", ph[:24]
                )

                if p_type == 1 and p_filesz > 0:  # PT_LOAD
                    partition = PartitionInfo(
                        name=f"segment_{i}",
                        offset=p_offset,
                        size=p_filesz,
                        image_type=ImageType.UNKNOWN,
                        load_addr=p_paddr,
                    )

                    # Analyze filesystem if this looks like a filesystem partition
                    if not self.skip_fs_analysis and partition.size > 1024 * 1024:
                        fs_analyzer = FilesystemAnalyzer()
                        partition.filesystem = fs_analyzer.analyze(
                            f, partition.offset, partition.size
                        )

                    partitions.append(partition)

        self.partitions = partitions
        return True

    def _parse_custom_gang(self, f: BinaryIO) -> list[PartitionInfo]:
        """Parse custom gang format."""
        # This would be implementation specific
        # For now, fall back to MBN scanning
        return self._scan_mbn_images(f)

    def _scan_mbn_images(self, f: BinaryIO) -> list[PartitionInfo]:
        """Scan for MBN images in the gang image."""
        f.seek(0)
        offset = 0
        partition_count = 0
        partitions = []

        while offset < self.file_size - 40:  # MBN header is 40 bytes
            f.seek(offset)
            header_data = f.read(40)

            if len(header_data) < 40:
                break

            # Try to parse as MBN header
            mbn_header = self._parse_mbn_header(header_data)
            if mbn_header and self._validate_mbn_header(mbn_header, offset):
                image_type = self._detect_image_type(f, offset, mbn_header)

                partition = PartitionInfo(
                    name=f"{image_type.value}_{partition_count}",
                    offset=offset,
                    size=mbn_header.image_size,
                    image_type=image_type,
                    load_addr=mbn_header.image_dest_ptr,
                    entry_point=mbn_header.image_dest_ptr,
                )

                # AI-NOTE: Only analyze filesystem for partitions larger than 1MB for performance reasons
                # Small partitions are typically bootloaders/firmware, not filesystems
                if not self.skip_fs_analysis and partition.size > 1024 * 1024:
                    fs_analyzer = FilesystemAnalyzer()
                    # AI-NOTE: MBN partitions have a 40-byte header, so we need to skip it
                    # to find the actual filesystem data (e.g., SquashFS, ext4, etc.)
                    fs_offset = partition.offset + 40
                    fs_size = partition.size - 40
                    partition.filesystem = fs_analyzer.analyze(f, fs_offset, fs_size)

                partitions.append(partition)
                partition_count += 1

                # Skip to next potential image
                next_offset = offset + mbn_header.image_size
                # Align to 4KB boundary
                next_offset = (next_offset + 4095) & ~4095
                offset = next_offset
            else:
                offset += 4096  # Skip 4KB and try again

        return partitions

    def _parse_mbn_header(self, data: bytes) -> Optional[MBNHeader]:
        """Parse MBN header from binary data."""
        if len(data) < 40:
            return None

        try:
            fields = struct.unpack("<10I", data)
            return MBNHeader(
                image_id=fields[0],
                header_vsn_num=fields[1],
                image_src=fields[2],
                image_dest_ptr=fields[3],
                image_size=fields[4],
                code_size=fields[5],
                signature_ptr=fields[6],
                signature_size=fields[7],
                cert_chain_ptr=fields[8],
                cert_chain_size=fields[9],
            )
        except struct.error:
            return None

    def _validate_mbn_header(self, header: MBNHeader, offset: int) -> bool:
        """Validate MBN header fields."""
        # Basic sanity checks
        if header.image_size == 0 or header.image_size > self.file_size:
            return False
        if offset + header.image_size > self.file_size:
            return False
        if header.header_vsn_num > 10:  # Reasonable version limit
            return False
        if header.image_dest_ptr < 0x40000000 or header.image_dest_ptr > 0xFFFFFFFF:
            return False

        return True

    def _detect_image_type(self, f: BinaryIO, offset: int, header: MBNHeader) -> ImageType:
        """Detect the type of image based on load address and content."""
        load_addr = header.image_dest_ptr

        # Qualcomm typical load addresses
        if 0x40000000 <= load_addr <= 0x4FFFFFFF:
            return ImageType.SBL
        elif 0x86000000 <= load_addr <= 0x87FFFFFF:
            return ImageType.TZ
        elif 0x60000000 <= load_addr <= 0x6FFFFFFF:
            return ImageType.RPM
        elif 0x8F600000 <= load_addr <= 0x8F6FFFFF:
            return ImageType.APPSBL
        else:
            # Try to detect by content
            current_pos = f.tell()
            f.seek(offset + 40)  # Skip MBN header
            content = f.read(min(512, header.image_size - 40))
            f.seek(current_pos)

            if b"ANDROID!" in content:
                return ImageType.BOOT
            elif b"Linux" in content or b"vmlinuz" in content:
                return ImageType.BOOT
            else:
                return ImageType.UNKNOWN

    def _validate_partitions(self, partitions: list[PartitionInfo]) -> list[str]:
        """Validate partition integrity."""
        errors = []

        for partition in partitions:
            # Check if partition fits in file
            if partition.offset + partition.size > self.file_size:
                errors.append(f"{partition.name}: extends beyond file end")

            # Check reasonable size limits
            if partition.size > 256 * 1024 * 1024:  # 256MB seems reasonable max
                errors.append(f"{partition.name}: unusually large ({partition.size} bytes)")

            if partition.size < 1024:  # Too small
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
