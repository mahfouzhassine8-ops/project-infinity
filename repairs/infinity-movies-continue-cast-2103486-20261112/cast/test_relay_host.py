"""Selected actual HTTP/privacy/retirement tests; no APK, Kodi or receiver PASS."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
from provided_http import obtain

here=Path(__file__).resolve().parent
work=Path(sys.argv[1]).resolve();out=work/'relay-host';out.mkdir(exist_ok=True)
proof=json.loads((work/'maven/SDK-DEPENDENCIES.json').read_text())
jars=obtain(work)
for row in proof['artifacts']:
    if row['coordinate'].startswith('org.jetbrains.kotlin:') and row['type']=='jar':
        data=(work/'maven'/row['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256']
        # Maven coordinate directories include colons, which are Java's Unix
        # classpath separator. This is a byte-identical host-test copy only.
        jar=out/Path(row['file']).name;jar.write_bytes(data);jars.append(jar)
cp=os.pathsep.join(map(str,jars))
sources=[here/'java/com/projectinfinity/kodi'/n for n in ('InfinityCastSource.java','InfinityCastRelay.java')]
sources.append(here/'tests/InfinityCastRelayTest.java')
subprocess.run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-cp',cp,'-d',str(out),*map(str,sources)],check=True)
subprocess.run(['java','-cp',str(out)+os.pathsep+cp,'com.projectinfinity.kodi.InfinityCastRelayTest'],check=True)
