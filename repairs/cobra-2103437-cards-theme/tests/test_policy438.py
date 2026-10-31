"""Exact owner review; unknown project classes must still be rejected."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from check_registered_policy import reviewed_policy
reviewed_policy()
print('PASS exact Cards root classification and unknown-class rejection')
