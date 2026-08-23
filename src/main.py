import sys

from modules.app import Dashify


def main() -> int:
    """Run Dashify and return a process-compatible exit code."""
    exit_code = Dashify().run()
    return int(exit_code) if exit_code is not None else 0


if __name__ == "__main__":
    sys.exit(main())
