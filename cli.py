#!/usr/bin/env python3
"""
Insightron - Legacy CLI Entry Point (Backward Compatibility)

This file maintains backward compatibility with the old CLI entry point.
It redirects to the new modern structure in insightron.app.cli.cli
"""

import sys
from pathlib import Path

# Add root directory to path to allow importing 'insightron' package
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the new main
if __name__ == "__main__":
    from insightron.app.cli.cli import main
    main()
