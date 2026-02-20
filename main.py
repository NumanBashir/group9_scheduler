#!/usr/bin/env python3
"""
Real-Time Scheduling Analysis Tool - TUI Version

A modern text-based user interface for analyzing real-time scheduling algorithms.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ui.tui import main
    main()
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("\nPlease install required packages:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n\nExiting...")
    sys.exit(0)
