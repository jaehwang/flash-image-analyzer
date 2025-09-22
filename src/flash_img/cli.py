"""Command-line interface for flash_img flash image analyzer."""

import argparse
import sys
from pathlib import Path

from .core.analyzer import ImageAnalyzer
from .core.exceptions import FlashImgError
from .core.models import AnalysisResult
from .platforms.nvidia import NVIDIAAnalyzer
from .platforms.qualcomm import QualcommAnalyzer
from .utils.formatting import format_output


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze embedded system flash images", prog="flash_img"
    )

    parser.add_argument("image", help="Flash image file to analyze")

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser.add_argument(
        "--extract", help="Extract partition to file (format: partition_name:output_file)"
    )

    parser.add_argument(
        "--fs-only", action="store_true", help="Show only partitions with filesystems"
    )

    parser.add_argument(
        "--no-fs-analysis",
        action="store_true",
        help="Skip filesystem analysis for faster processing",
    )

    parser.add_argument(
        "--platform",
        choices=["qualcomm", "nvidia", "broadcom", "mediatek", "marvell", "auto"],
        default="auto",
        help="Force specific platform analyzer (default: auto-detect)",
    )

    parser.add_argument(
        "--output-format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format for results",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    return parser


def select_analyzer(image_path: str, platform: str, skip_fs_analysis: bool) -> ImageAnalyzer:
    """Select appropriate analyzer for the image."""
    if platform != "auto":
        # Force specific platform
        if platform == "qualcomm":
            return QualcommAnalyzer(image_path, skip_fs_analysis)
        elif platform == "nvidia":
            return NVIDIAAnalyzer(image_path, skip_fs_analysis)
        else:
            raise FlashImgError(f"Platform '{platform}' not yet implemented")

    # Auto-detect platform
    analyzers = [
        QualcommAnalyzer(image_path, skip_fs_analysis),
        NVIDIAAnalyzer(image_path, skip_fs_analysis),
    ]

    try:
        with open(image_path, "rb") as f:
            for analyzer in analyzers:
                if analyzer.can_handle(f):
                    return analyzer
    except Exception:
        pass

    # If no analyzer can handle it, default to Qualcomm for backward compatibility
    return QualcommAnalyzer(image_path, skip_fs_analysis)


def handle_extraction(analyzer: ImageAnalyzer, extract_spec: str) -> None:
    """Handle partition extraction."""
    try:
        partition_name, output_file = extract_spec.split(":", 1)
        analyzer.extract_partition(partition_name, output_file)
        print(f"Extracted {partition_name} to {output_file}")
    except ValueError:
        print("Error: Extract format should be partition_name:output_file")
        sys.exit(1)
    except Exception as e:
        print(f"Error extracting partition: {e}")
        sys.exit(1)


def output_results(
    result: AnalysisResult, output_format: str, verbose: bool, fs_only: bool
) -> None:
    """Output analysis results in the specified format."""
    if output_format == "text":
        print(format_output(result, verbose, fs_only))
    elif output_format == "json":
        import json

        # Convert result to dict for JSON serialization
        data = {
            "filename": result.filename,
            "file_size": result.file_size,
            "partitions": [
                {
                    "name": p.name,
                    "offset": p.offset,
                    "size": p.size,
                    "image_type": p.image_type.value,
                    "load_addr": p.load_addr,
                    "filesystem": (
                        {
                            "fs_type": p.filesystem.fs_type,
                            "fs_size": p.filesystem.fs_size,
                            "used_size": p.filesystem.used_size,
                            "free_size": p.filesystem.free_size,
                            "block_size": p.filesystem.block_size,
                        }
                        if p.filesystem
                        else None
                    ),
                }
                for p in (
                    result.partitions
                    if not fs_only
                    else [p for p in result.partitions if p.filesystem]
                )
            ],
            "total_partition_size": result.total_partition_size,
            "total_filesystem_used": result.total_filesystem_used,
            "validation_errors": result.validation_errors,
            "warnings": result.warnings,
        }
        print(json.dumps(data, indent=2))
    elif output_format == "csv":
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            ["Name", "Type", "Offset", "Size", "Load_Addr", "FS_Type", "FS_Size", "Used_Size"]
        )

        # Data rows
        partitions = (
            result.partitions if not fs_only else [p for p in result.partitions if p.filesystem]
        )
        for p in partitions:
            writer.writerow(
                [
                    p.name,
                    p.image_type.value,
                    f"0x{p.offset:08x}",
                    p.size,
                    f"0x{p.load_addr:08x}",
                    p.filesystem.fs_type if p.filesystem else "N/A",
                    p.filesystem.fs_size if p.filesystem else "N/A",
                    p.filesystem.used_size if p.filesystem else "N/A",
                ]
            )

        print(output.getvalue().strip())


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate input file
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: File '{args.image}' not found")
        sys.exit(1)

    try:
        # Select and create analyzer
        analyzer = select_analyzer(str(image_path), args.platform, args.no_fs_analysis)

        # Analyze the image
        result = analyzer.analyze()

        # Handle extraction if requested
        if args.extract:
            handle_extraction(analyzer, args.extract)
            return

        # Output results
        output_results(result, args.output_format, args.verbose, args.fs_only)

        # Exit with error code if validation failed
        if result.validation_errors:
            sys.exit(1)

    except FlashImgError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
