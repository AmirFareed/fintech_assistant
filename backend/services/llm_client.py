"""Compatibility alias for :mod:`llm.client`."""
import sys
from llm import client as _implementation
sys.modules[__name__] = _implementation
