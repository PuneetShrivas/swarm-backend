#!/usr/bin/env python
"""
D&O Public Risk Report Single-Instruction CLI Entrypoint.
Usage:
    python backend/run_do_risk_report.py <TICKER> [OPTIONS]
"""

import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.workflows.do_risk_report.cli import main

if __name__ == "__main__":
    main()
