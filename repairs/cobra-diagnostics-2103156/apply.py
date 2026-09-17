#!/usr/bin/env python3
"""Strict 2103155 -> 2103156 diagnostic observer patch. No native or layout-policy edits."""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'cobra-epg-rc1'))
from apply_epg_repair import span
BASE='4d1ed032df7e13fd27cc2170fc5e028f5059ec32'
ACTIVITY='42b36566929293ea8a3848e1ef099b736dfdbd09842d5cd98d73d6b30a5ba1e3'
INSTALL='c4ef0ab5cc6ea5e577b7857b94e1594ed81f83fab83d7ebc75e0006910e53fb0'
FEATURE='d76fffe4669ba308aae67077d6f74bcb27f938f8c916141491b8af4d5a33b34f'
SRC=Path('tools/android/packaging/xbmc/src')
def sha(b):return hashlib.sha256(b.encode() if isinstance(b,str) else b).hexdigest()
def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Exact diagnostic anchor mismatch: '+old[:100])
    return text.replace(old,new,1)

def patch_activity(before):
    if sha(before)!=ACTIVITY:raise ValueError('Not the locked 2103155 Activity')
    text=once(before,'    mFeatures = new InfinityCobraFeatureRuntime(this);','    mFeatures = new InfinityCobraFeatureRuntime(this);\n    InfinityCobraDiagnostics.start(this);\n    if(state!=null){mCobraDiagnosticsPicker=state.getBoolean("cobra_diagnostics_picker",false);mCobraDiagnosticsSnapshot=state.getString("cobra_diagnostics_snapshot");}')
    text=once(text,'    loadPersistedState();','    loadPersistedState();\n    cobraDiagnosticSecrets();')
    old='    health.setOnClickListener(v -> showError("Cobra diagnostics (redacted)", mFeatures.healthSnapshot()));'
    text=once(text,old,'    health.setOnClickListener(v -> showCobraHealthSnapshot());\n    Button exportDiagnostics = action("EXPORT CRASH & DIAGNOSTICS ZIP");\n    exportDiagnostics.setOnClickListener(v -> showCobraDiagnosticExport());')
    text=once(text,'    list.addView(customEpg, new LinearLayout.LayoutParams(','    list.addView(exportDiagnostics, new LinearLayout.LayoutParams(-1, dp(64)));\n    list.addView(customEpg, new LinearLayout.LayoutParams(')
    old='    super.onActivityResult(requestCode, resultCode, data);'
    text=once(text,old,old+'''
    if(requestCode==REQUEST_COBRA_DIAGNOSTICS){
      boolean requested=mCobraDiagnosticsPicker;mCobraDiagnosticsPicker=false;
      String snapshot=mCobraDiagnosticsSnapshot;mCobraDiagnosticsSnapshot=null;
      if(!requested)return;
      if(resultCode!=RESULT_OK){toast("Diagnostics export cancelled");return;}
      if(data==null||data.getData()==null){toast("No save destination returned; export not saved");return;}
      cobraDiagnosticSecrets();
      toast("Saving redacted diagnostics ZIP…");
      InfinityCobraDiagnostics.export(getApplicationContext(),data.getData(),snapshot);
      return;
    }''')
    # The source's regex matched the XML declaration version=1.0, not <addon version>.
    x,y=span(text,'activeCobraUiLabel')
    text=text[:x]+'''  private String activeCobraUiLabel() {
    try {
      File external=getExternalFilesDir(null);
      if(external==null)return "ACTIVE UI  •  APK DEFAULT  •  RUNTIME 3";
      File addon=new File(external,".kodi/addons/script.infinity.cobra.theme/addon.xml");
      if(!addon.isFile())return "ACTIVE UI  •  APK DEFAULT  •  RUNTIME 3";
      if(addon.length()>65536)return "ACTIVE UI  •  METADATA UNAVAILABLE  •  RUNTIME 3";
      try(InputStream input=new java.io.FileInputStream(addon)){
        XmlPullParser parser=Xml.newPullParser();parser.setInput(input,"UTF-8");
        int event=parser.getEventType();
        while(event!=XmlPullParser.END_DOCUMENT){
          if(event==XmlPullParser.START_TAG){
            if(!"addon".equals(parser.getName())||!"script.infinity.cobra.theme".equals(parser.getAttributeValue(null,"id")))break;
            String version=parser.getAttributeValue(null,"version");
            if(version!=null&&version.matches("[0-9]+(?:\\\\.[0-9]+){1,4}"))return "ACTIVE UI  •  "+version+"  •  RUNTIME 3";
            break;
          }
          event=parser.next();
        }
      }
    }catch(Exception ignored){}
    return "ACTIVE UI  •  METADATA UNAVAILABLE  •  RUNTIME 3";
  }'''+text[y:]
    # Capture the existing error at its listener, without changing fallback/session decisions.
    old='      error=failure==null?"UNKNOWN":failure.getErrorCodeName();'
    text=once(text,old,old+'\n      cobraDiagnosticSecrets();\n      InfinityCobraDiagnostics.failure(InfinityLiveActivity.this,"player",failure);')
    old='  private void showError(String title, String message) {'
    text=once(text,old,old+'\n    cobraDiagnosticSecrets();\n    InfinityCobraDiagnostics.record(this,"error","ui-error",title+"\\n"+message);')
    text=once(text,'\n}', '\n'+(ROOT/'activity.java.inc').read_text()+'\n}')
    allowed={'onCreate','onActivityResult','activeCobraUiLabel','showSettings','showError'}
    names=set(re.findall(r'^  (?:private|public|protected) [^\n;=(){}]*\b([A-Za-z0-9_]+)\s*\(',before,re.M))
    protected=[]
    for name in sorted(names-allowed):
      try:a,b=span(before,name);c,d=span(text,name)
      except ValueError:continue
      if before[a:b]!=text[c:d]:raise ValueError('Protected method changed: '+name)
      protected.append(name)
    for name in ('CobraModeLayout','CobraBroadcastRow','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow'):
      a,b=span(before,name,'class');c,d=span(text,name,'class');assert before[a:b]==text[c:d],name
    return text,{'changed_activity_methods':sorted(allowed),'observer_listener':'CobraPlayerBinding.onPlayerError','protected_methods':protected,'before':sha(before),'after':sha(text)}

def patch_feature(before):
    # Verify against the immutable feature template, not an arbitrary generated runtime.
    expected=(ROOT.parents[1]/'patches/infinity-cobra-v2/InfinityCobraFeatureRuntime.java.in').read_text()
    if before!=expected or sha(before)!=FEATURE:raise ValueError('FeatureRuntime differs from immutable template')
    text=once(before,'      root.put("cobra_version", "candidate-2");','      InfinityCobraDiagnostics.addIdentity(context,root);')
    text=once(text,'      root.put("schema", 2);','      root.put("schema", 3);\n      root.put("snapshot_kind", "historical_event_sample");')
    start=text.index('      File healthDir = new File(context.getFilesDir(), "health");')
    end=text.index('\n    } catch (Exception ignored) {}',start)
    text=text[:start]+'      InfinityCobraDiagnostics.saveHealth(context,json,error);'+text[end:]
    x,y=span(text,'redact');text=text[:x]+'''  public static String redact(String input) {
    String value=InfinityCobraDiagnostics.redact(input);
    return value.length()>500?value.substring(0,500):value;
  }'''+text[y:]
    x,y=span(text,'writeAtomic');text=text[:x]+'''  private static void writeAtomic(File target, byte[] data) throws Exception {
    CobraDiagnosticArchive.atomicWrite(target,data);
  }'''+text[y:]
    return text

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    source=a.source;before=(source/SRC/'InfinityLiveActivity.java.in').read_text()
    activity,report=patch_activity(before)
    feature=(source/SRC/'InfinityCobraFeatureRuntime.java.in').read_text();new_feature=patch_feature(feature)
    install=source/'cmake/scripts/android/Install.cmake';text=install.read_text()
    if sha(text)!=INSTALL:raise ValueError('Not the locked 2103155 Java source inventory')
    text=once(text,'                  src/InfinityCobraFeatureRuntime.java\n','                  src/InfinityCobraFeatureRuntime.java\n                  src/CobraDiagnosticArchive.java\n                  src/InfinityCobraDiagnostics.java\n')
    files={str(SRC/'InfinityLiveActivity.java.in'):activity,str(SRC/'InfinityCobraFeatureRuntime.java.in'):new_feature,'cmake/scripts/android/Install.cmake':text}
    for name in ('CobraDiagnosticArchive','InfinityCobraDiagnostics'):
      rel=str(SRC/(name+'.java.in'))
      if(source/rel).exists():raise ValueError('Diagnostic helper already exists')
      files[rel]=(ROOT/(name+'.java.in')).read_text()
    # Validate all inputs before any source write; record every changed file in the packaging receipt.
    receipt=Path('engine/background-resume-source.json');data=json.loads(receipt.read_text())
    if data['version_code']!=2103155:raise ValueError('Wrong source version')
    for rel,row in data['files'].items():
      if sha((source/rel).read_bytes())!=row['after']:raise ValueError('Source receipt drift: '+rel)
    report.update(base_commit=BASE,native_modified=False,device_tested=False,changes={})
    for rel,value in files.items():
      previous=sha((source/rel).read_bytes()) if (source/rel).exists() else None
      report['changes'][rel]={'before':previous,'after':sha(value)}
    for rel,value in files.items():
      (source/rel).write_text(value)
      data['files'][rel]={'before':report['changes'][rel]['before'],'after':sha(value)}
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: diagnostics applied; '+str(len(report['protected_methods']))+' Activity methods and all five layouts preserved')
if __name__=='__main__':main()
