"""Compatibility alias for :mod:`embeddings.generator`."""
import sys
from embeddings import generator as _implementation
sys.modules[__name__] = _implementation
