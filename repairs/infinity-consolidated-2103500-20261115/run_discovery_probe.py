"""Reuse the disposable Android runner; accurately narrow its reported scope."""
from pathlib import Path
import subprocess
import sys
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
result = subprocess.run([sys.executable, str(ROOT / 'repairs/infinity-movies-continue-cast-2103486-20261112/cast/run_probe.py'), *sys.argv[1:]])
receipt = Path(sys.argv[1]) / 'ANDROID-CAST-COMPONENT.json'
if receipt.exists():
    data = json.loads(receipt.read_bytes())
    data['scope'] = 'Real pinned SDK initialization and discovery callback lifecycle only; no receiver transfer, media probe, native observer or Infinity shutdown'
    receipt.write_text(json.dumps(data, indent=2) + '\n')
raise SystemExit(result.returncode)
