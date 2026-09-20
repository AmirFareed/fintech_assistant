"""Compatibility alias for :mod:`utils.language`."""
import sys
from utils import language as _implementation
sys.modules[__name__] = _implementation
