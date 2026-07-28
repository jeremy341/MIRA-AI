from .cli import main

try:
    main()
except KeyboardInterrupt:
    pass
except Exception:
    import sys
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
