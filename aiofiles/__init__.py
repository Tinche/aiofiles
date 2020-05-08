"""Utilities for asyncio-friendly file handling."""
from .threadpool import open
from . import tempfile

__version__ = "0.7.0dev0"

__all__ = ["open", "tempfile"]
