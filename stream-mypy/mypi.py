#!/usr/bin/env python3
"""Stream-MyPI main entry point"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from stream_mypy.main import main

if __name__ == "__main__":
    main()
