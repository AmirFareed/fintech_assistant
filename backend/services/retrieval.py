"""Compatibility alias for :mod:`retrieval.search`."""
import sys
from retrieval import search as _implementation
sys.modules[__name__] = _implementation
