"""Base gang image analyzer class."""

import os
from abc import ABC, abstractmethod
from typing import BinaryIO

from .exceptions import AnalysisError
from .models import AnalysisResult


class GangImageAnalyzer(ABC):
    """Base class for gang image analyzers."""

    def __init__(self, filename: str, skip_fs_analysis: bool = False):
        self.filename = filename
        self.skip_fs_analysis = skip_fs_analysis

        if not os.path.exists(filename):
            raise AnalysisError(f"File {filename} not found")

        self.file_size = os.path.getsize(filename)

    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """Analyze the gang image and return results."""
        pass

    @abstractmethod
    def can_handle(self, f: BinaryIO) -> bool:
        """Check if this analyzer can handle the given file format."""
        pass

    def extract_partition(self, partition_name: str, output_file: str) -> None:
        """Extract a partition to a file."""
        result = self.analyze()

        partition = None
        for p in result.partitions:
            if p.name == partition_name:
                partition = p
                break

        if not partition:
            available = [p.name for p in result.partitions]
            raise AnalysisError(
                f"Partition '{partition_name}' not found. " f"Available: {', '.join(available)}"
            )

        try:
            with open(self.filename, "rb") as infile:
                infile.seek(partition.offset)
                data = infile.read(partition.size)

            with open(output_file, "wb") as outfile:
                outfile.write(data)

        except Exception as e:
            raise AnalysisError(f"Error extracting partition: {e}") from e
