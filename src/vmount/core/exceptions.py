"""Custom exceptions for v-mount."""


class VmountError(Exception):
    """Base exception for v-mount errors."""

    pass


class AnalysisError(VmountError):
    """Error during gang image analysis."""

    pass


class ValidationError(VmountError):
    """Error during gang image validation."""

    pass


class UnsupportedFormatError(VmountError):
    """Gang image format is not supported."""

    pass


class PartitionNotFoundError(VmountError):
    """Requested partition was not found."""

    pass


class FilesystemError(VmountError):
    """Error analyzing filesystem."""

    pass
