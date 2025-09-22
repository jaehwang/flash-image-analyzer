"""Platform-specific analyzers for different chipsets."""

from .nvidia import NVIDIAAnalyzer
from .qualcomm import QualcommAnalyzer

__all__ = ["QualcommAnalyzer", "NVIDIAAnalyzer"]
