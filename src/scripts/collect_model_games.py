
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from xg_model.collect import get_model_replays
get_model_replays(count=200, pages=5)
