"""Compatibility alias for :mod:`llm.chatbot`."""
import sys
from llm import chatbot as _implementation
sys.modules[__name__] = _implementation
