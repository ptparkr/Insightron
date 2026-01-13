#!/usr/bin/env python3
"""
Insightron - Legacy Entry Point (Backward Compatibility)

This file maintains backward compatibility with the old entry point.
It redirects to the new modern structure in src/app/main.py
"""

import sys
from pathlib import Path

# Add root directory to path to allow importing 'insightron' package
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the new main
if __name__ == "__main__":
    from insightron.app.main import main
    main()
