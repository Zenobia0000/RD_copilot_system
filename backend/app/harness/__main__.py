"""Entry point for `python -m app.harness`."""

import sys

from app.harness.cli import main

if __name__ == "__main__":
    sys.exit(main())
