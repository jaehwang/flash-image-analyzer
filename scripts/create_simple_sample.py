#!/usr/bin/env python3
"""Create a very simple test sample."""

import argparse
import os
import struct
from typing import Optional


def create_mbn_partition(data: bytes, load_addr: int, image_id: int = 1) -> bytes:
    """Create MBN partition with header."""
    image_size = len(data) + 40  # MBN header size + data

    # AI-NOTE: MBN (Multi-Boot Image) is Qualcomm's standard format for bootloader images
    # Each MBN has a 40-byte header followed by the actual binary data
    header = bytearray(40)
    struct.pack_into(
        "<I", header, 0, 0
    )  # AI-NOTE: image_id=0 for analyzer recognition (matches magic check)
    struct.pack_into("<I", header, 4, 0x3)  # header_vsn_num
    struct.pack_into("<I", header, 8, 0x0)  # image_src
    struct.pack_into(
        "<I", header, 12, load_addr
    )  # AI-NOTE: load address determines partition type (SBL, TZ, etc.)
    struct.pack_into("<I", header, 16, image_size)  # image_size
    struct.pack_into("<I", header, 20, len(data))  # code_size
    struct.pack_into("<I", header, 24, 0x0)  # signature_ptr
    struct.pack_into("<I", header, 28, 0x0)  # signature_size
    struct.pack_into("<I", header, 32, 0x0)  # cert_chain_ptr
    struct.pack_into("<I", header, 36, 0x0)  # cert_chain_size

    # Combine header + data
    result = bytearray()
    result.extend(header)
    result.extend(data)

    return bytes(result)


def create_sbl_partition() -> bytes:
    """Create SBL (Secondary Boot Loader) partition."""
    # AI-NOTE: SBL is the first bootloader that runs after Boot ROM
    # It initializes basic hardware like DDR, clocks, and loads the next stage
    code = bytearray()
    code.extend(b"SBL_CODE" * 100)  # Fake SBL code

    # Pad to reasonable size
    while len(code) < 4096:
        code.append(0)

    # AI-NOTE: 0x40000000 is the typical SBL load address in Qualcomm memory map
    return create_mbn_partition(bytes(code), 0x40000000, 1)


def create_appsbl_partition() -> bytes:
    """Create APPSBL partition with fake boot code."""
    # AI-NOTE: APPSBL (Application SBL) is the second-stage bootloader
    # It typically loads the Linux kernel and handles advanced features
    code = bytearray()
    code.extend(b"APPSBL" * 150)  # Fake APPSBL code

    # Pad to reasonable size
    while len(code) < 2048:
        code.append(0)

    # AI-NOTE: 0x8F600000 is the typical APPSBL load address in Qualcomm memory map
    return create_mbn_partition(bytes(code), 0x8F600000, 2)


def create_squashfs_rootfs() -> bytes:
    """Create a simple SquashFS filesystem with README.md."""
    # AI-NOTE: SquashFS is a compressed read-only filesystem commonly used for rootfs
    # It's popular in embedded systems due to small size and fast boot times
    data = bytearray()

    # AI-NOTE: SquashFS magic number - "hsqs" for little endian, "sqsh" for big endian
    data.extend(b"hsqs")  # Magic number

    # AI-NOTE: SquashFS 4.0 superblock structure (simplified version for testing)
    data.extend(struct.pack("<I", 1))  # inodes
    data.extend(struct.pack("<I", 0))  # mkfs_time (low)
    data.extend(struct.pack("<I", 131072))  # block_size
    data.extend(struct.pack("<I", 1))  # fragments
    data.extend(struct.pack("<H", 4))  # compression (ZLIB)
    data.extend(struct.pack("<H", 16))  # block_log
    data.extend(struct.pack("<H", 0))  # flags
    data.extend(struct.pack("<H", 1))  # no_ids
    data.extend(struct.pack("<H", 4))  # s_major
    data.extend(struct.pack("<H", 0))  # s_minor
    data.extend(struct.pack("<Q", 0))  # root_inode
    data.extend(struct.pack("<Q", 1024))  # bytes_used
    data.extend(struct.pack("<Q", 0))  # id_table_start
    data.extend(struct.pack("<Q", 0))  # xattr_id_table_start
    data.extend(struct.pack("<Q", 0))  # inode_table_start
    data.extend(struct.pack("<Q", 0))  # directory_table_start
    data.extend(struct.pack("<Q", 0))  # fragment_table_start
    data.extend(struct.pack("<Q", 0))  # export_table_start

    # Pad superblock to 96 bytes
    while len(data) < 96:
        data.append(0)

    # Add fake compressed data representing README.md file
    readme_content = b"# Simple Root Filesystem\n\nThis is a minimal root filesystem for testing.\n"

    # Simple "compressed" data (just the content + some padding)
    data.extend(readme_content)

    # AI-NOTE: Pad to >1MB because analyzer only checks filesystems in large partitions
    # This is a performance optimization - small partitions are usually bootloaders
    while len(data) < 1024 * 1024 + 1024:  # 1MB + 1KB
        data.append(0)

    return bytes(data)


def create_rootfs_partition() -> bytes:
    """Create rootfs as MBN partition with SquashFS."""
    rootfs_data = create_squashfs_rootfs()
    # AI-NOTE: 0x90000000 is used for rootfs - different from bootloader addresses
    # This helps the analyzer distinguish partition types by load address
    return create_mbn_partition(rootfs_data, 0x90000000, 3)


# NVIDIA Tegra sample generation functions


def create_bct_partition() -> bytes:
    """Create BCT (Boot Configuration Table) for NVIDIA Tegra."""
    # AI-NOTE: BCT contains boot configuration parameters like memory timings, clock settings
    # It's the first thing read by Tegra Boot ROM to configure SDRAM and other hardware
    bct = bytearray()

    # BCT signature
    bct.extend(b"BCT\x00")

    # BCT version and configuration data (simplified)
    bct.extend(struct.pack("<I", 0x01000000))  # version
    bct.extend(struct.pack("<I", 0))  # oem_data_size
    bct.extend(struct.pack("<I", 0))  # customer_data_size
    bct.extend(struct.pack("<I", 0))  # reserved

    # Add fake SDRAM configuration
    bct.extend(b"SDRAM_CONFIG" * 10)

    # Pad to 4KB (typical BCT size)
    while len(bct) < 4096:
        bct.append(0)

    return bytes(bct)


def create_gpt_header() -> bytes:
    """Create GPT header for NVIDIA Tegra image."""
    # AI-NOTE: GPT (GUID Partition Table) is the standard partitioning scheme for Tegra
    # It provides a more flexible and robust partitioning than MBR
    gpt_header = bytearray(512)

    # GPT signature
    gpt_header[0:8] = b"EFI PART"

    # GPT revision (1.0)
    struct.pack_into("<I", gpt_header, 8, 0x00010000)

    # Header size
    struct.pack_into("<I", gpt_header, 12, 92)

    # Header CRC32 (dummy)
    struct.pack_into("<I", gpt_header, 16, 0x12345678)

    # Current LBA (1)
    struct.pack_into("<Q", gpt_header, 24, 1)

    # Backup LBA
    struct.pack_into("<Q", gpt_header, 32, 100)

    # First usable LBA
    struct.pack_into("<Q", gpt_header, 40, 34)

    # Last usable LBA
    struct.pack_into("<Q", gpt_header, 48, 99)

    # Partition entry LBA (2)
    struct.pack_into("<Q", gpt_header, 72, 2)

    # Number of partition entries
    struct.pack_into("<I", gpt_header, 80, 4)

    # Partition entry size
    struct.pack_into("<I", gpt_header, 84, 128)

    return bytes(gpt_header)


def create_gpt_partition_entry(
    name: str, first_lba: int, last_lba: int, type_guid: Optional[bytes] = None
) -> bytes:
    """Create a GPT partition entry."""
    entry = bytearray(128)

    # Partition type GUID (generic if not specified)
    if type_guid:
        entry[0:16] = type_guid
    else:
        entry[0:16] = b"\x01\x02\x03\x04" * 4  # Dummy GUID

    # Unique partition GUID
    entry[16:32] = os.urandom(16)

    # First and last LBA
    struct.pack_into("<Q", entry, 32, first_lba)
    struct.pack_into("<Q", entry, 40, last_lba)

    # Attributes (none)
    struct.pack_into("<Q", entry, 48, 0)

    # Partition name (UTF-16LE)
    name_utf16 = name.encode("utf-16le")
    entry[56 : 56 + len(name_utf16)] = name_utf16

    return bytes(entry)


def create_tegra_bootloader(name: str, content: str) -> bytes:
    """Create a Tegra bootloader partition."""
    # AI-NOTE: Tegra bootloaders don't use MBN format like Qualcomm
    # They're typically raw binary images with NVIDIA-specific headers
    data = bytearray()

    # Add NVIDIA signature
    data.extend(b"NVDA")

    # Version and size info
    data.extend(struct.pack("<I", 0x01000000))  # version
    data.extend(struct.pack("<I", len(content.encode())))  # content size
    data.extend(struct.pack("<I", 0))  # reserved

    # Add the actual content
    data.extend(content.encode() * 100)  # Repeat content for size

    # Pad to reasonable size (64KB)
    while len(data) < 64 * 1024:
        data.append(0)

    return bytes(data)


def create_tegra_filesystem() -> bytes:
    """Create ext4 filesystem for Tegra rootfs."""
    # AI-NOTE: Tegra typically uses ext4 for writable partitions like system/userdata
    # SquashFS is used for read-only partitions like rootfs
    data = bytearray()

    # ext4 superblock (simplified)
    # Pad to superblock location (1024 bytes from start)
    data.extend(b"\x00" * 1024)

    # Create ext4 superblock structure
    superblock = bytearray(1024)  # Superblock is typically 1024 bytes

    # ext4 magic number at offset 56 in superblock
    struct.pack_into("<H", superblock, 56, 0xEF53)

    # Basic superblock fields (in proper ext4 layout)
    struct.pack_into("<I", superblock, 0, 1000)  # s_inodes_count
    struct.pack_into("<I", superblock, 4, 4000)  # s_blocks_count_lo
    struct.pack_into("<I", superblock, 8, 400)  # s_r_blocks_count_lo
    struct.pack_into("<I", superblock, 12, 3600)  # s_free_blocks_count_lo
    struct.pack_into("<I", superblock, 16, 990)  # s_free_inodes_count
    struct.pack_into("<I", superblock, 20, 1)  # s_first_data_block
    struct.pack_into("<I", superblock, 24, 2)  # s_log_block_size (4KB blocks)

    # Add the superblock to data
    data.extend(superblock)

    # Add fake file content
    readme_content = (
        b"# NVIDIA Tegra Root Filesystem\n\nThis is a test ext4 filesystem for Tegra.\n"
    )
    data.extend(readme_content)

    # Pad to >1MB for filesystem analysis
    while len(data) < 1024 * 1024 + 1024:  # 1MB + 1KB
        data.append(0)

    return bytes(data)


def create_qualcomm_flash_image() -> bytes:
    """Create a Qualcomm flash image with proper MBN partitions."""
    flash_image = bytearray()

    # AI-NOTE: Create partitions according to Qualcomm boot sequence and memory layout
    # SBL -> APPSBL -> Rootfs is the typical boot order
    sbl = create_sbl_partition()
    appsbl = create_appsbl_partition()
    rootfs = create_rootfs_partition()

    # Add SBL partition first
    flash_image.extend(sbl)

    # AI-NOTE: Align to 4KB boundaries for better memory management
    # This is common practice in embedded systems for MMU page alignment
    while len(flash_image) % 4096 != 0:
        flash_image.append(0)

    # Add APPSBL partition
    flash_image.extend(appsbl)

    # Align to 4KB boundary
    while len(flash_image) % 4096 != 0:
        flash_image.append(0)

    # Add rootfs partition
    flash_image.extend(rootfs)

    return bytes(flash_image)


def create_nvidia_flash_image() -> bytes:
    """Create an NVIDIA Tegra flash image with GPT partitions."""
    flash_image = bytearray()

    # AI-NOTE: Tegra flash layout typically starts with BCT, then GPT, then partitions
    # BCT configures hardware, GPT defines partition layout

    # Add BCT at the beginning
    bct = create_bct_partition()
    flash_image.extend(bct)

    # Align to 512 bytes for GPT
    while len(flash_image) % 512 != 0:
        flash_image.append(0)

    # Add MBR (protective, 512 bytes)
    mbr = bytearray(512)
    mbr[510:512] = b"\x55\xAA"  # Boot signature
    flash_image.extend(mbr)

    # Add GPT header
    gpt_header = create_gpt_header()
    flash_image.extend(gpt_header)

    # Add GPT partition entries (4 partitions)
    # Note: LBA values are relative to start of the device (including BCT + MBR)
    # BCT + MBR + GPT takes 34 sectors (17408 bytes), so data starts at LBA 34

    # MB1 bootloader - 64KB = 128 sectors
    mb1_entry = create_gpt_partition_entry("mb1", 34, 161)  # LBA 34-161
    flash_image.extend(mb1_entry)

    # MB2/TegraBoot - 64KB = 128 sectors
    mb2_entry = create_gpt_partition_entry("mb2", 162, 289)  # LBA 162-289
    flash_image.extend(mb2_entry)

    # CBoot - 64KB = 128 sectors
    cboot_entry = create_gpt_partition_entry("cboot", 290, 417)  # LBA 290-417
    flash_image.extend(cboot_entry)

    # Root filesystem - remaining space (~2048 sectors)
    rootfs_entry = create_gpt_partition_entry("rootfs", 418, 2465)  # LBA 418-2465
    flash_image.extend(rootfs_entry)

    # Pad partition table to LBA 34 (where actual partitions start)
    while len(flash_image) < 34 * 512:
        flash_image.append(0)

    # Add actual partition data
    # MB1 bootloader
    mb1_data = create_tegra_bootloader("MB1", "MB1_BOOTLOADER_CODE")
    flash_image.extend(mb1_data[: 128 * 512])  # Limit to allocated size

    # MB2/TegraBoot
    mb2_data = create_tegra_bootloader("MB2", "TEGRABOOT_CODE")
    flash_image.extend(mb2_data[: 128 * 512])  # Limit to allocated size

    # CBoot
    cboot_data = create_tegra_bootloader("CBoot", "CBOOT_UBOOT_CODE")
    flash_image.extend(cboot_data[: 128 * 512])  # Limit to allocated size

    # Root filesystem
    rootfs_data = create_tegra_filesystem()
    flash_image.extend(rootfs_data[: 2048 * 512])  # Limit to allocated size

    return bytes(flash_image)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Create test flash image samples for embedded systems analysis",
        prog="create_simple_sample",
    )

    parser.add_argument(
        "--platform",
        choices=["qualcomm", "nvidia"],
        default="qualcomm",
        help="Target platform for flash image generation (default: qualcomm)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path (default: samples/{platform}_flash.img)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Create samples directory if it doesn't exist
        os.makedirs("samples", exist_ok=True)
        output_file = f"samples/{args.platform}_flash.img"

    # Generate flash image based on platform
    if args.platform == "qualcomm":
        if args.verbose:
            print("Generating Qualcomm flash image with MBN partitions...")
        flash_image = create_qualcomm_flash_image()
    elif args.platform == "nvidia":
        if args.verbose:
            print("Generating NVIDIA Tegra flash image with GPT partitions...")
        flash_image = create_nvidia_flash_image()
    else:
        print(f"Error: Unsupported platform '{args.platform}'")
        return

    # Write flash image to file
    try:
        with open(output_file, "wb") as f:
            f.write(flash_image)

        print(f"Created {args.platform} flash image: {output_file} ({len(flash_image):,} bytes)")

        if args.verbose:
            if args.platform == "qualcomm":
                print("  Contains: SBL (bootloader) + APPSBL (bootloader) + SquashFS rootfs")
            elif args.platform == "nvidia":
                print("  Contains: BCT + GPT + MB1/MB2/CBoot (bootloaders) + ext4 rootfs")

    except IOError as e:
        print(f"Error writing to {output_file}: {e}")


if __name__ == "__main__":
    main()
