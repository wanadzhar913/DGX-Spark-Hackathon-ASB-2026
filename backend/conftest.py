"""Pytest bootstrap: ensure both `backend/` and the repo root are importable.

- `backend/` on the path  -> `import app...`
- repo root on the path   -> `import models...`
"""

import os
import sys

_BACKEND = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_BACKEND, ".."))

for p in (_BACKEND, _REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
