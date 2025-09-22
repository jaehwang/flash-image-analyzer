"""Core data models for flash image analysis."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ImageType(Enum):
    """Types of images found in flash images."""

    SBL = "sbl"
    TZ = "tz"
    RPM = "rpm"
    APPSBL = "appsbl"
    BOOT = "boot"
    RECOVERY = "recovery"
    SYSTEM = "system"
    USERDATA = "userdata"
    UNKNOWN = "unknown"


@dataclass
class FilesystemInfo:
    """Information about a filesystem found in a partition."""

    fs_type: str
    fs_size: int
    used_size: int
    free_size: int
    block_size: int
    total_blocks: int
    free_blocks: int


@dataclass
class PartitionInfo:
    """Information about a partition in a flash image."""

    name: str
    offset: int
    size: int
    image_type: ImageType
    load_addr: int = 0
    entry_point: int = 0
    crc32: int = 0
    filesystem: Optional[FilesystemInfo] = None


@dataclass
class AnalysisResult:
    """Complete analysis result for a flash image."""

    filename: str
    file_size: int
    partitions: list[PartitionInfo]
    total_partition_size: int
    total_filesystem_used: int
    validation_errors: list[str]
    warnings: list[str]
