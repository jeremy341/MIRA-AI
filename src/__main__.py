import sys
import traceback

from .cli import main

try:
    main()
except KeyboardInterrupt:
    sys.exit(130)
except Exception:
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
