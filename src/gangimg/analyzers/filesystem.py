"""Filesystem analysis for various embedded filesystem types."""

import struct
from typing import BinaryIO, Optional

from ..core.models import FilesystemInfo


class FilesystemAnalyzer:
    """Analyzer for embedded filesystem types."""

    def analyze(self, f: BinaryIO, offset: int, size: int) -> Optional[FilesystemInfo]:
        """Analyze filesystem in the partition."""
        current_pos = f.tell()

        try:
            f.seek(offset)
            header = f.read(min(8192, size))  # Read first 8KB for analysis

            if len(header) < 1024:
                return None

            # Try different filesystem types
            fs_info = None

            # Check for ext2/3/4
            if len(header) >= 0x464:
                ext_magic = struct.unpack("<H", header[0x438:0x43A])[0]
                if ext_magic == 0xEF53:
                    fs_info = self._analyze_ext_filesystem(f, offset, size, header)

            # Check for SquashFS
            if not fs_info and len(header) >= 96:
                if header[0:4] == b"hsqs" or header[0:4] == b"sqsh":
                    fs_info = self._analyze_squashfs_filesystem(f, offset, size, header)

            # Check for UBIFS
            if not fs_info and len(header) >= 64:
                if header[0:4] == b"UBI#":
                    fs_info = self._analyze_ubifs_filesystem(f, offset, size, header)

            # Check for JFFS2
            if not fs_info and len(header) >= 12:
                if header[0:2] == b"\x19\x85" or header[0:2] == b"\x85\x19":
                    fs_info = self._analyze_jffs2_filesystem(f, offset, size, header)

            # Check for YAFFS2
            if not fs_info:
                # YAFFS2 doesn't have a clear magic, try to detect by pattern
                if self._detect_yaffs2_pattern(header):
                    fs_info = self._analyze_yaffs2_filesystem(f, offset, size, header)

            return fs_info

        except Exception:
            # Don't raise exception, just return None and let caller handle
            return None
        finally:
            f.seek(current_pos)

    def _analyze_ext_filesystem(
        self, f: BinaryIO, offset: int, size: int, header: bytes
    ) -> FilesystemInfo:
        """Analyze ext2/3/4 filesystem."""
        # Ext superblock starts at offset 0x400 (1024 bytes)
        sb_offset = 0x400
        if len(header) < sb_offset + 96:
            f.seek(offset + sb_offset)
            sb_data = f.read(96)
        else:
            sb_data = header[sb_offset : sb_offset + 96]

        if len(sb_data) < 96:
            return FilesystemInfo("ext", size, 0, size, 4096, 0, 0)

        # Parse superblock fields
        s_blocks_count = struct.unpack("<I", sb_data[4:8])[0]
        s_free_blocks_count = struct.unpack("<I", sb_data[12:16])[0]
        s_log_block_size = struct.unpack("<I", sb_data[24:28])[0]

        block_size = 1024 << s_log_block_size
        fs_size = s_blocks_count * block_size
        free_size = s_free_blocks_count * block_size
        used_size = fs_size - free_size

        return FilesystemInfo(
            fs_type="ext",
            fs_size=fs_size,
            used_size=used_size,
            free_size=free_size,
            block_size=block_size,
            total_blocks=s_blocks_count,
            free_blocks=s_free_blocks_count,
        )

    def _analyze_squashfs_filesystem(
        self, f: BinaryIO, offset: int, size: int, header: bytes
    ) -> FilesystemInfo:
        """Analyze SquashFS filesystem."""
        if len(header) < 96:
            return FilesystemInfo("squashfs", size, size, 0, 131072, 0, 0)

        # SquashFS superblock
        magic = header[0:4]
        if magic == b"hsqs":
            # Little endian
            bytes_used = struct.unpack("<Q", header[40:48])[0]
            block_size = struct.unpack("<I", header[12:16])[0]
        else:
            # Big endian
            bytes_used = struct.unpack(">Q", header[40:48])[0]
            block_size = struct.unpack(">I", header[12:16])[0]

        return FilesystemInfo(
            fs_type="squashfs",
            fs_size=bytes_used,
            used_size=bytes_used,
            free_size=0,  # SquashFS is read-only, compressed
            block_size=block_size,
            total_blocks=bytes_used // block_size,
            free_blocks=0,
        )

    def _analyze_ubifs_filesystem(
        self, f: BinaryIO, offset: int, size: int, header: bytes
    ) -> FilesystemInfo:
        """Analyze UBIFS filesystem."""
        # UBIFS analysis is complex, provide basic info
        return FilesystemInfo(
            fs_type="ubifs",
            fs_size=size,
            used_size=size // 2,  # Rough estimate
            free_size=size // 2,
            block_size=131072,  # Common UBIFS block size
            total_blocks=size // 131072,
            free_blocks=size // 131072 // 2,
        )

    def _analyze_jffs2_filesystem(
        self, f: BinaryIO, offset: int, size: int, header: bytes
    ) -> FilesystemInfo:
        """Analyze JFFS2 filesystem."""
        # JFFS2 analysis requires scanning nodes, provide estimate
        return FilesystemInfo(
            fs_type="jffs2",
            fs_size=size,
            used_size=size // 3,  # Rough estimate
            free_size=size * 2 // 3,
            block_size=65536,  # Common erase block size
            total_blocks=size // 65536,
            free_blocks=size // 65536 * 2 // 3,
        )

    def _detect_yaffs2_pattern(self, header: bytes) -> bool:
        """Detect YAFFS2 by looking for typical patterns."""
        # YAFFS2 typically has object headers at regular intervals
        # This is a simple heuristic
        pattern_count = 0
        for i in range(0, min(len(header) - 16, 2048), 512):
            chunk = header[i : i + 16]
            if len(chunk) >= 4:
                # Look for YAFFS2 object header patterns
                obj_type = chunk[0] if len(chunk) > 0 else 0
                if obj_type in [1, 2, 3, 4, 5]:  # Valid YAFFS2 object types
                    pattern_count += 1

        return pattern_count >= 2

    def _analyze_yaffs2_filesystem(
        self, f: BinaryIO, offset: int, size: int, header: bytes
    ) -> FilesystemInfo:
        """Analyze YAFFS2 filesystem."""
        return FilesystemInfo(
            fs_type="yaffs2",
            fs_size=size,
            used_size=size // 2,  # Rough estimate
            free_size=size // 2,
            block_size=131072,  # Common NAND block size
            total_blocks=size // 131072,
            free_blocks=size // 131072 // 2,
        )
