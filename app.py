"""Backward-compatible WSGI module; prefer ``api.application`` or ``main.py``."""

import sys


if __name__ == "__main__":
    from main import main

    main()
else:
    from api import application as _implementation

    sys.modules[__name__] = _implementation
