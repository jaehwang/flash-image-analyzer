"""Integration tests using sample files."""

import os
import tempfile

from gangimg.platforms.qualcomm import QualcommAnalyzer


class TestSampleAnalysis:
    """Test analysis with sample files."""

    def test_sample_generation_and_analysis(self) -> None:
        """Test creating and analyzing a sample."""
        # Create a simple ELF-like sample
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
            # ELF header (simplified)
            elf_header = bytearray(52)
            elf_header[0:4] = b"\x7f\x45\x4c\x46"  # ELF magic
            elf_header[16:20] = b"\x02\x00\x28\x00"  # ET_EXEC, EM_ARM

            # Add minimal ELF structure
            tmp.write(elf_header)
            tmp.write(b"BOOTCODE" * 100)  # Fake boot code
            tmp.flush()

            try:
                analyzer = QualcommAnalyzer(tmp.name, skip_fs_analysis=True)

                # Test can_handle
                with open(tmp.name, "rb") as f:
                    assert analyzer.can_handle(f)

                # Test analysis - might not find partitions but shouldn't crash
                result = analyzer.analyze()
                assert result is not None
                assert result.filename == tmp.name
                assert result.file_size > 0

            finally:
                os.unlink(tmp.name)
