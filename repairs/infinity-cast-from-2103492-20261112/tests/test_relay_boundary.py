from pathlib import Path
import subprocess,sys,os
ROOT=Path(__file__).resolve().parents[3]
CAST=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast'
sys.path.insert(0,str(CAST));from provided_http import obtain
work=Path(sys.argv[1]);out=work/'relay92-boundary';out.mkdir(exist_ok=True)
cp=os.pathsep.join(map(str,obtain(work)))
sources=[CAST/'java/com/projectinfinity/kodi'/n for n in ('InfinityCastRelay.java','InfinityCastSource.java','InfinityCastAdaptive.java','InfinityCastDiagnostics.java')]+[Path(__file__).with_name('RelayBoundaryTest.java')]
subprocess.run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-cp',cp,'-d',str(out),*map(str,sources)],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+cp,'com.projectinfinity.kodi.RelayBoundaryTest'],check=True)
