"""Compatibility alias for :mod:`vectordb.supabase`."""
import sys
from vectordb import supabase as _implementation
sys.modules[__name__] = _implementation
