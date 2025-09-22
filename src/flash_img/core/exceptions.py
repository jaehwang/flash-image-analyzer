"""Custom exceptions for flash_img."""


class FlashImgError(Exception):
    """Base exception for flash_img errors."""

    pass


class AnalysisError(FlashImgError):
    """Error during flash image analysis."""

    pass


class ValidationError(FlashImgError):
    """Error during flash image validation."""

    pass


class UnsupportedFormatError(FlashImgError):
    """Flash image format is not supported."""

    pass


class PartitionNotFoundError(FlashImgError):
    """Requested partition was not found."""

    pass


class FilesystemError(FlashImgError):
    """Error analyzing filesystem."""

    pass
