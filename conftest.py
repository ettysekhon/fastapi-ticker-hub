import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(ROOT, "packages/api/src"))
sys.path.insert(0, os.path.join(ROOT, "packages/poller/src"))
