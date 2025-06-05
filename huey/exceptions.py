# huey/exceptions.py


class HueyError(Exception):
    """Base exception class for Huey project."""

    pass


class DataNotFoundError(HueyError):
    """Exception raised when expected data is not found."""

    pass


class InvalidInputError(HueyError):
    """Exception raised for invalid input."""

    pass
