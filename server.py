#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Compatibility module exposing `app` at repository root.

Keeps existing entrypoints working (`uvicorn server:app`, Cloudflare `main = "server.py"`,
and scripts importing `server`).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_MODULES_DIR = ROOT_DIR / "python_modules"
SRC_DIR = ROOT_DIR / "src"
if str(PYTHON_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_MODULES_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ops_plat_azure_devops_gateway.app import app  # noqa: E402

try:  # noqa: E402
    from ops_plat_azure_devops_gateway.app import Default
except Exception:  # pragma: no cover
    Default = None

__all__ = ["app", "Default"]
