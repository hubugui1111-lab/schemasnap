"""SchemaSnap domain errors."""


class SchemaSnapError(Exception):
    """Base class for expected operational errors."""


class UnsafeQueryError(SchemaSnapError):
    """Raised when DuckDB SQL exceeds the read-only query boundary."""


class UnsupportedSourceError(SchemaSnapError, ValueError):
    """Raised when an input format is not supported."""
