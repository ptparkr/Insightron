#!/usr/bin/env python3
"""
Insightron dependency installer wrapper.

Keeps older docs/commands working:
  python install_dependencies.py
"""

from __future__ import annotations

from pathlib import Path
import runpy


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    target = repo_root / "automation" / "setup" / "install_dependencies.py"
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()

