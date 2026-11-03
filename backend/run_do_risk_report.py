#!/usr/bin/env python
"""
D&O Public Risk Report Single-Instruction CLI Entrypoint.
Usage:
    python backend/run_do_risk_report.py <TICKER> [OPTIONS]
"""

import os
import sys
from dotenv import load_dotenv

# Load backend environment variables
backend_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(backend_dir, ".env")
if os.path.isfile(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

# Ensure backend root is on sys.path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.workflows.do_risk_report.cli import main

if __name__ == "__main__":
    main()
