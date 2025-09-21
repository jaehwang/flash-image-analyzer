#!/usr/bin/env python3
"""Create a very simple test sample."""

import struct

def create_mbn_partition(data: bytes, load_addr: int, image_id: int = 1) -> bytes:
    """Create MBN partition with header."""
    image_size = len(data) + 40  # MBN header size + data

    # AI-NOTE: MBN (Multi-Boot Image) is Qualcomm's standard format for bootloader images
    # Each MBN has a 40-byte header followed by the actual binary data
    header = bytearray(40)
    struct.pack_into('<I', header, 0, 0)           # AI-NOTE: image_id=0 for analyzer recognition (matches magic check)
    struct.pack_into('<I', header, 4, 0x3)          # header_vsn_num
    struct.pack_into('<I', header, 8, 0x0)          # image_src
    struct.pack_into('<I', header, 12, load_addr)   # AI-NOTE: load address determines partition type (SBL, TZ, etc.)
    struct.pack_into('<I', header, 16, image_size)  # image_size
    struct.pack_into('<I', header, 20, len(data))   # code_size
    struct.pack_into('<I', header, 24, 0x0)         # signature_ptr
    struct.pack_into('<I', header, 28, 0x0)         # signature_size
    struct.pack_into('<I', header, 32, 0x0)         # cert_chain_ptr
    struct.pack_into('<I', header, 36, 0x0)         # cert_chain_size

    # Combine header + data
    result = bytearray()
    result.extend(header)
    result.extend(data)

    return bytes(result)

def create_sbl_partition():
    """Create SBL (Secondary Boot Loader) partition."""
    # AI-NOTE: SBL is the first bootloader that runs after Boot ROM
    # It initializes basic hardware like DDR, clocks, and loads the next stage
    code = bytearray()
    code.extend(b'SBL_CODE' * 100)  # Fake SBL code

    # Pad to reasonable size
    while len(code) < 4096:
        code.append(0)

    # AI-NOTE: 0x40000000 is the typical SBL load address in Qualcomm memory map
    return create_mbn_partition(bytes(code), 0x40000000, 1)

def create_appsbl_partition():
    """Create APPSBL partition with fake boot code."""
    # AI-NOTE: APPSBL (Application SBL) is the second-stage bootloader
    # It typically loads the Linux kernel and handles advanced features
    code = bytearray()
    code.extend(b'APPSBL' * 150)  # Fake APPSBL code

    # Pad to reasonable size
    while len(code) < 2048:
        code.append(0)

    # AI-NOTE: 0x8F600000 is the typical APPSBL load address in Qualcomm memory map
    return create_mbn_partition(bytes(code), 0x8F600000, 2)

def create_squashfs_rootfs():
    """Create a simple SquashFS filesystem with README.md."""
    # AI-NOTE: SquashFS is a compressed read-only filesystem commonly used for rootfs
    # It's popular in embedded systems due to small size and fast boot times
    data = bytearray()

    # AI-NOTE: SquashFS magic number - "hsqs" for little endian, "sqsh" for big endian
    data.extend(b'hsqs')  # Magic number

    # AI-NOTE: SquashFS 4.0 superblock structure (simplified version for testing)
    data.extend(struct.pack('<I', 1))         # inodes
    data.extend(struct.pack('<I', 0))         # mkfs_time (low)
    data.extend(struct.pack('<I', 131072))    # block_size
    data.extend(struct.pack('<I', 1))         # fragments
    data.extend(struct.pack('<H', 4))         # compression (ZLIB)
    data.extend(struct.pack('<H', 16))        # block_log
    data.extend(struct.pack('<H', 0))         # flags
    data.extend(struct.pack('<H', 1))         # no_ids
    data.extend(struct.pack('<H', 4))         # s_major
    data.extend(struct.pack('<H', 0))         # s_minor
    data.extend(struct.pack('<Q', 0))         # root_inode
    data.extend(struct.pack('<Q', 1024))      # bytes_used
    data.extend(struct.pack('<Q', 0))         # id_table_start
    data.extend(struct.pack('<Q', 0))         # xattr_id_table_start
    data.extend(struct.pack('<Q', 0))         # inode_table_start
    data.extend(struct.pack('<Q', 0))         # directory_table_start
    data.extend(struct.pack('<Q', 0))         # fragment_table_start
    data.extend(struct.pack('<Q', 0))         # export_table_start

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

def create_rootfs_partition():
    """Create rootfs as MBN partition with SquashFS."""
    rootfs_data = create_squashfs_rootfs()
    # AI-NOTE: 0x90000000 is used for rootfs - different from bootloader addresses
    # This helps the analyzer distinguish partition types by load address
    return create_mbn_partition(rootfs_data, 0x90000000, 3)

def create_gang_image():
    """Create a Qualcomm gang image with proper MBN partitions."""
    gang_image = bytearray()

    # AI-NOTE: Create partitions according to Qualcomm boot sequence and memory layout
    # SBL -> APPSBL -> Rootfs is the typical boot order
    sbl = create_sbl_partition()
    appsbl = create_appsbl_partition()
    rootfs = create_rootfs_partition()

    # Add SBL partition first
    gang_image.extend(sbl)

    # AI-NOTE: Align to 4KB boundaries for better memory management
    # This is common practice in embedded systems for MMU page alignment
    while len(gang_image) % 4096 != 0:
        gang_image.append(0)

    # Add APPSBL partition
    gang_image.extend(appsbl)

    # Align to 4KB boundary
    while len(gang_image) % 4096 != 0:
        gang_image.append(0)

    # Add rootfs partition
    gang_image.extend(rootfs)

    return bytes(gang_image)

def main():
    gang_image = create_gang_image()

    with open('samples/simple_gang.img', 'wb') as f:
        f.write(gang_image)

    print(f"Created gang image: {len(gang_image)} bytes")

if __name__ == '__main__':
    main()