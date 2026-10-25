#!/usr/bin/env python3
"""Entry point: python3 tools/college.py <command> (see --help)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.scholarship.cli import main  # noqa: E402

sys.exit(main())
