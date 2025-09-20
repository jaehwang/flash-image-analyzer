"""Validation utilities for gang images."""

import hashlib
import zlib
from typing import BinaryIO, Union

from ..core.models import PartitionInfo


def validate_gang_image(filename: str) -> tuple[bool, list[str]]:
    """Validate basic gang image properties."""
    errors = []

    try:
        with open(filename, "rb") as f:
            file_size = f.seek(0, 2)  # Get file size

            # Basic file size checks
            if file_size < 1024:
                errors.append("File too small to be a valid gang image")
            elif file_size > 16 * 1024 * 1024 * 1024:  # 16GB limit
                errors.append("File unusually large for a gang image")

            # Check for empty file
            f.seek(0)
            first_kb = f.read(1024)
            if all(b == 0 for b in first_kb):
                errors.append("File appears to be empty (all zeros)")

    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return len(errors) == 0, errors


def calculate_checksum(f: BinaryIO, offset: int, size: int, algorithm: str = "crc32") -> Union[int, str]:
    """Calculate checksum for a section of the file."""
    current_pos = f.tell()
    f.seek(offset)
    data = f.read(size)
    f.seek(current_pos)

    if algorithm == "crc32":
        return int(zlib.crc32(data) & 0xFFFFFFFF)
    elif algorithm == "md5":
        return hashlib.md5(data).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def validate_partition_integrity(partition: PartitionInfo, file_size: int) -> list[str]:
    """Validate individual partition integrity."""
    errors = []

    # Check if partition fits in file
    if partition.offset + partition.size > file_size:
        errors.append(f"{partition.name}: extends beyond file end")

    # Check reasonable size limits
    if partition.size > 256 * 1024 * 1024:  # 256MB seems reasonable max
        errors.append(f"{partition.name}: unusually large ({partition.size} bytes)")

    if partition.size < 1024:  # Too small
        errors.append(f"{partition.name}: unusually small ({partition.size} bytes)")

    # Check alignment
    if partition.offset % 512 != 0:
        errors.append(f"{partition.name}: not aligned to 512-byte boundary")

    return errors
