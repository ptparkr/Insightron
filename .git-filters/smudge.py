#!/usr/bin/env python3
"""
Git smudge filter: replaces USER with mshan in local working copy.
Run via: git config filter.username-filter.smudge "python .git-filters/smudge.py"
"""
import sys

for line in sys.stdin.buffer:
    sys.stdout.buffer.write(line.replace(b'C:\\\\Users\\\\USER', b'C:\\\\Users\\\\mshan'))
