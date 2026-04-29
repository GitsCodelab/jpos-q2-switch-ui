#!/usr/bin/env python3
"""
Unified test runner for jPOS Backend API.

Runs all unit tests in the tests/ directory and generates a summary report.
Exit code: 0 if all tests pass, 1 if any test fails.

Usage:
    python run_tests.py              # Run all tests with summary
    python run_tests.py --verbose    # Run with detailed output
    python run_tests.py --quiet      # Run with minimal output
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def main():
    args = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    quiet = "--quiet" in args or "-q" in args
    
    # Determine pytest flags
    pytest_args = [
        "-v" if verbose else ("-q" if quiet else ""),
        "--tb=short",
        "tests/",
    ]
    pytest_args = [arg for arg in pytest_args if arg]  # Remove empty strings
    
    print("=" * 80)
    print(f"jPOS Backend API — Unit Tests")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Run pytest using current Python executable
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + pytest_args,
        cwd=Path(__file__).parent,
    )
    
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. See output above for details.")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
