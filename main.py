import os
os.environ["INQUIRERPY_MOUSE_SUPPORT"] = "true"

import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
