"""Compatibility alias for :mod:`vectordb.postgres`."""
import sys
from vectordb import postgres as _implementation
sys.modules[__name__] = _implementation
