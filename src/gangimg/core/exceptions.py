"""Custom exceptions for gangimg."""


class GangimgError(Exception):
    """Base exception for gangimg errors."""

    pass


class AnalysisError(GangimgError):
    """Error during gang image analysis."""

    pass


class ValidationError(GangimgError):
    """Error during gang image validation."""

    pass


class UnsupportedFormatError(GangimgError):
    """Gang image format is not supported."""

    pass


class PartitionNotFoundError(GangimgError):
    """Requested partition was not found."""

    pass


class FilesystemError(GangimgError):
    """Error analyzing filesystem."""

    pass
