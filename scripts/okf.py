"""Thin agent-facing entry point for OKF Runtime."""

import sys

from okf_runtime.cli import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
