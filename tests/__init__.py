import os
import sys

# Ensure repository root is on sys.path for test imports
root = os.path.dirname(os.path.dirname(__file__))
if root not in sys.path:
    sys.path.insert(0, root)
