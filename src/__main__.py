from .cli import main

try:
    main()
except KeyboardInterrupt:
    pass
except Exception as e:
    import sys
    print(f"Fatal error: {e}", file=sys.stderr)
    sys.exit(1)
