import sys
import os

# Add current directory to sys.path so 'app' package is found locally
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app
