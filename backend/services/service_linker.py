"""Compatibility alias for :mod:`vectordb.service_linker`."""
import sys
from vectordb import service_linker as _implementation
sys.modules[__name__] = _implementation
