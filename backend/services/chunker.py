"""Compatibility alias for :mod:`chunking.splitter`."""
import sys
from chunking import splitter as _implementation
sys.modules[__name__] = _implementation
