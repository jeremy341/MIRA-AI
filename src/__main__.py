import sys

from .cli import main

try:
    main()
except KeyboardInterrupt:
    sys.exit(130)
except Exception:
    import sys
    import traceback

    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
