"""Backward-compatible alias for :mod:`utils.config`."""

import sys

from utils import config as _implementation

sys.modules[__name__] = _implementation
