#!/usr/bin/env python3
"""
Git clean filter: replaces mshan with USER before committing.
Run via: git config filter.username-filter.clean "python .git-filters/clean.py"
"""
import sys

for line in sys.stdin.buffer:
    sys.stdout.buffer.write(line.replace(b'C:\\\\Users\\\\mshan', b'C:\\\\Users\\\\USER'))
