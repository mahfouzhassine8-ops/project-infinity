from pathlib import Path
import ast,subprocess,tempfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
prior=ROOT/'repairs/infinity-cast-repair-2103490-20261112/tests'
module=ast.parse((prior/'test_session.py').read_text())
STUBS=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='STUBS' for x in n.targets))
STUBS['com/google/android/gms/cast/MediaError']='package com.google.android.gms.cast;public class MediaError {public Integer getDetailedErrorCode(){return 321;}}'
relay=STUBS['com/projectinfinity/kodi/InfinityCastRelay']
relay=relay.replace('static long delay;', 'static long delay,retireDelay;Runnable done;boolean retired;')
relay=relay.replace('void close(){closed=true;}', 'void close(){if(closed)return;closed=true;new Handler(Looper.getMainLooper()).postDelayed(()->{retired=true;if(done!=null){Runnable r=done;done=null;r.run();}},retireDelay);}void closeWhenRetired(Runnable r){done=r;close();if(retired&&done!=null){done=null;r.run();}}')
STUBS['com/projectinfinity/kodi/InfinityCastRelay']=relay
STUBS['com/projectinfinity/kodi/InfinityCastChannel']='package com.projectinfinity.kodi;import org.json.JSONObject;import android.os.*;final class InfinityCastChannel {static long retireDelay;InfinityCastChannel(String t,String f,String o){}void publish(JSONObject o){}boolean acknowledged(){return true;}void close(){}void closeWhenRetired(Runnable r){new Handler(Looper.getMainLooper()).postDelayed(r,retireDelay);}}'
gateway=STUBS['com/projectinfinity/kodi/InfinityCastGateway']
gateway=gateway.replace('int releases;','int releases;static boolean refuseRelease;')
gateway=gateway.replace('if(op.equals("release"))releases++;cb.done(', 'if(op.equals("release")){releases++;if(refuseRelease){cb.done(new JSONObject().put("status","error").put("reason","fixture_refusal"));return;}}cb.done(')
STUBS['com/projectinfinity/kodi/InfinityCastGateway']=gateway
with tempfile.TemporaryDirectory(prefix='cast92-cleanup-') as td:
 work=Path(td);out=work/'classes';out.mkdir()
 for n,b in STUBS.items():
  p=work/(n+'.java');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(b)
 java=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast/java/com/projectinfinity/kodi'
 sources=[java/n for n in ('InfinityCastSession.java','InfinityCastSource.java','InfinityCastDiagnostics.java')]+list(work.rglob('*.java'))+[prior/'SessionContractTest.java',HERE/'SessionCleanupTest.java']
 subprocess.run(['java','com.sun.tools.javac.Main','-d',str(out),*map(str,sources)],check=True)
 subprocess.run(['java','-cp',str(out),'com.projectinfinity.kodi.SessionCleanupTest'],check=True)
