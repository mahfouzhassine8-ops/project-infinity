"""Build-only official ASM relocation; no existing APK class is transformed."""
from pathlib import Path
import hashlib,json,os,subprocess,urllib.request

PREFIX='assets.infinity.cast.privatehttp.'
ROOTS=('okhttp3.','okio.','kotlin.','com.google.common.','androidx.','android.support.')
def rules(text):
    for root in ROOTS:text=text.replace(root,PREFIX+root)
    return text
def prepare(work):
    here=Path(__file__).resolve().parent;lock=json.loads((here.parent/'research/CAST-BUILD-ONLY-SHADER.json').read_text())
    tools=Path(work)/'shader-tools';tools.mkdir(exist_ok=True);jars=[]
    for row in lock['artifacts']:
        p=tools/row['file'];group,artifact,version=row['coordinate'].split(':')
        if not p.exists():
            with urllib.request.urlopen('https://repo.maven.apache.org/maven2/'+group.replace('.','/')+'/'+artifact+'/'+version+'/'+p.name,timeout=30) as stream:p.write_bytes(stream.read())
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];jars.append(p)
    cp=os.pathsep.join(map(str,jars))
    subprocess.run(['java','com.sun.tools.javac.Main','-classpath',cp,'-d',str(tools),str(here/'tooling/CastPrivateClasses.java')],check=True)
    return ['java','-cp',str(tools)+os.pathsep+cp,'CastPrivateClasses']
