"""
V-Mount: Gang Image Analysis Tool

A CLI tool to analyze and validate embedded system gang images
across multiple platforms (Qualcomm, Broadcom, MediaTek, Marvell).
"""

__version__ = "0.1.0"
__author__ = "V-Mount Development Team"

from .core.analyzer import GangImageAnalyzer
from .platforms.qualcomm import QualcommAnalyzer

__all__ = ["GangImageAnalyzer", "QualcommAnalyzer"]
