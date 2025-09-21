"""Formatting utilities for output display."""

from typing import List

from ..core.models import AnalysisResult, PartitionInfo


def format_size(size: int) -> str:
    """Format size in human readable format."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/1024/1024:.1f}MB"
    else:
        return f"{size/1024/1024/1024:.1f}GB"


def format_output(result: AnalysisResult, verbose: bool = False, fs_only: bool = False) -> str:
    """Format analysis result for display."""
    output = []

    # Filter partitions if requested
    partitions = result.partitions
    if fs_only:
        partitions = [p for p in partitions if p.filesystem]

    # Header
    output.append(f"Analyzing flash image: {result.filename}")
    output.append(f"File size: {result.file_size} bytes ({format_size(result.file_size)})")
    output.append("-" * 60)

    # Warnings
    if result.warnings:
        for warning in result.warnings:
            output.append(f"Warning: {warning}")
        output.append("-" * 60)

    # Partition table
    output.append(f"\nFound {len(partitions)} partitions:")
    output.append("-" * 120)
    output.append(
        f"{'Name':<15} {'Type':<10} {'Offset':<12} {'Size':<12} {'Load Addr':<12} {'FS Type':<10} {'FS Size':<12} {'Used':<10}"
    )
    output.append("-" * 120)

    for partition in partitions:
        # Format filesystem info
        fs_type = "N/A"
        fs_size_str = "N/A"
        used_str = "N/A"

        if partition.filesystem:
            fs = partition.filesystem
            fs_type = fs.fs_type
            fs_size_str = format_size(fs.fs_size)
            used_str = format_size(fs.used_size)

        output.append(
            f"{partition.name:<15} {partition.image_type.value:<10} "
            f"0x{partition.offset:08x}   {format_size(partition.size):<10}   "
            f"0x{partition.load_addr:08x}   {fs_type:<10} {fs_size_str:<10} {used_str:<10}"
        )

    output.append("-" * 120)
    output.append(f"Total partition size: {format_size(result.total_partition_size)}")
    output.append(f"Total filesystem used: {format_size(result.total_filesystem_used)}")
    output.append(f"File size: {format_size(result.file_size)}")

    if result.total_partition_size < result.file_size:
        unused = result.file_size - result.total_partition_size
        output.append(f"Unused space: {format_size(unused)}")

    # Detailed filesystem analysis
    fs_partitions = [p for p in partitions if p.filesystem]
    if fs_partitions:
        output.append("\nFilesystem Details:")
        output.append("-" * 100)
        output.append(
            f"{'Partition':<15} {'FS Type':<10} {'Total':<12} {'Used':<12} {'Free':<12} {'Usage%':<8} {'Block Size':<10}"
        )
        output.append("-" * 100)

        for partition in fs_partitions:
            if not partition.filesystem:
                continue
            fs = partition.filesystem
            usage_pct = (fs.used_size / fs.fs_size * 100) if fs.fs_size > 0 else 0

            output.append(
                f"{partition.name:<15} {fs.fs_type:<10} "
                f"{format_size(fs.fs_size):<10} {format_size(fs.used_size):<10} "
                f"{format_size(fs.free_size):<10} {usage_pct:>6.1f}%   "
                f"{format_size(fs.block_size):<10}"
            )

        output.append("-" * 100)

    # Overlap analysis
    output.append("\nOverlap Analysis:")
    output.append("-" * 40)

    overlaps = check_overlaps(partitions)
    if overlaps:
        output.append("⚠️  Overlaps detected:")
        for part1, part2, size in overlaps:
            output.append(f"  {part1} overlaps with {part2} by {size} bytes")
    else:
        output.append("✅ No overlaps detected")

    # Validation results
    output.append("\nPartition Validation:")
    output.append("-" * 40)

    if result.validation_errors:
        output.append("⚠️  Validation errors:")
        for error in result.validation_errors:
            output.append(f"  {error}")
    else:
        output.append("✅ All partitions validated successfully")

    return "\n".join(output)


def check_overlaps(partitions: List[PartitionInfo]) -> List[tuple]:
    """Check for partition overlaps."""
    overlaps = []
    sorted_partitions = sorted(partitions, key=lambda p: p.offset)

    for i in range(len(sorted_partitions) - 1):
        current = sorted_partitions[i]
        next_part = sorted_partitions[i + 1]

        current_end = current.offset + current.size
        if current_end > next_part.offset:
            overlap_size = current_end - next_part.offset
            overlaps.append((current.name, next_part.name, overlap_size))

    return overlaps
