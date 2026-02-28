#!/usr/bin/env python3
"""
Insightron - legacy script entry point.

Note: This file exists because a root-level `insightron.py` would shadow the
installed `insightron/` package and break `pip install -e .` console scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    # Ensure repo root is on path for local runs
    sys.path.insert(0, str(Path(__file__).parent))
    from insightron.app.main import main as app_main

    app_main()


if __name__ == "__main__":
    main()

