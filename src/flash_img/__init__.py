"""
Flash Image Analysis Tool

A CLI tool to analyze and validate embedded system flash images
across multiple platforms (Qualcomm, NVIDIA Tegra, Broadcom, MediaTek, Marvell).
"""

__version__ = "0.1.0"
__author__ = "Flash Image Analysis Development Team"

from .core.analyzer import ImageAnalyzer
from .platforms.nvidia import NVIDIAAnalyzer
from .platforms.qualcomm import QualcommAnalyzer

__all__ = ["ImageAnalyzer", "QualcommAnalyzer", "NVIDIAAnalyzer"]
