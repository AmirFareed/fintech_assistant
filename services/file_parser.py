"""Compatibility alias for :mod:`ingestion.parsers`."""
import sys
from ingestion import parsers as _implementation
sys.modules[__name__] = _implementation
