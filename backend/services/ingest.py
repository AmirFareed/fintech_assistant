"""Compatibility alias for :mod:`ingestion.pipeline`."""
import sys
from ingestion import pipeline as _implementation
sys.modules[__name__] = _implementation
