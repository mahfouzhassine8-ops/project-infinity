"""CI-only focused Android result plus exact private synthetic output for timestamp analysis."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast/run_probe.py'
try:exec(compile(prior.read_text(),str(prior),'exec'),{'__file__':str(prior),'__name__':'__main__'})
finally:
 subprocess.run(['adb','pull','/sdcard/Android/data/com.projectinfinity.castqa/files/mkv-remux.mp4',str(Path(sys.argv[1])/'mkv-remux.mp4')],check=False)
