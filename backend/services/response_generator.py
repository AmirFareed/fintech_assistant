"""Compatibility alias for :mod:`prompts.response_generator`."""
import sys
from prompts import response_generator as _implementation
sys.modules[__name__] = _implementation
