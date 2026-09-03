"""Compatibility alias for :mod:`retrieval.router`."""
import sys
from retrieval import router as _implementation
sys.modules[__name__] = _implementation
