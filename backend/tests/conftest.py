import os
import sys

# Absolute path to the backend directory
BACKEND_ROOT = os.path.dirname(os.path.dirname(__file__))

# Ensure backend root is on sys.path so that `import app` works
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
