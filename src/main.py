import sys
from modules.app import Dashify


def main() -> int:
    exitcode = Dashify().run()
    return int(exitcode) if exitcode is not None else 0


if __name__ == "__main__":
    sys.exit(main())
