#!/usr/bin/env python3
"""Deprecated alias — prefer scripts/seed_pinyin_course.py."""

from __future__ import annotations

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("seed_pinyin_course.py")), run_name="__main__")
