#!/usr/bin/env python3
"""Execute exact generated production EPG methods with disclosed host adapters.

Original 41 cases are unchanged. These are host integration/regression tests,
not real provider traffic, Android graphics/AtomicFile crash or device acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from apply_epg_repair import span,digest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    text=args.source.read_text();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    classes=['CobraGuideMath','CobraEpgData','GuideProgram','ProgramPair','Channel','LiveException','CobraBoundedGuideStream']
    methods=['parseXmlTvTime','cobraBoundedId','cobraParseGuide','cobraMergeEpg','cobraDigest','cobraEpgCacheFile','cobraReadEpgCache','cobraWriteEpgCache','cobraInstallEpg','cobraResolveEpg','cobraPrograms','cobraCurrentProgram','cobraNextProgram','cobraGuideStatus','cobraGuideFailure','cobraDownloadEpg','programFor','guideTitleAt','sourceIdForChannel','cobraLibrariesEqual','loadGuideAsync','cobraEpgRequestCurrent','cobraRefreshGuide','cobraDiscoverPlaylistGuide','cobraEpgUrls','cobraEpgIdentity','cobraStartPresentationTicker']
    extras=re.findall(r'^  private [^\n;=(){}]*\b([A-Za-z0-9_]+)\s*\(', (ROOT.parent/'guide-repair.java.inc').read_text().split('// @append\n',1)[1],re.M)
    methods+=extras+['formatTime','cobraRefreshChannelMetadata']
    parts=[];ledger=[]
    for name,kind in [(n,'class') for n in classes]+[(n,'method') for n in methods]+[('mCobraPresentationTick','field')]:
        a,b=span(text,name,kind);value=text[a:b];parts.append(value)
        ledger.append({'name':name,'kind':kind,'sha256':digest(value),'start_line':text.count('\n',0,a)+1,'end_line':text.count('\n',0,b)+1})
    support=(ROOT/'host_support.java.inc').read_text()
    extra_support='''
  // Host-only widget, visibility and metadata adapters. No player or view implementation is substituted into the release.
  private final Set<String> mCobraForceEpg=new HashSet<>();
  private final java.util.concurrent.atomic.AtomicLong mCobraEpgSequence=new java.util.concurrent.atomic.AtomicLong();
  private final java.util.concurrent.ConcurrentHashMap<String,Long> mCobraEpgGenerations=new java.util.concurrent.ConcurrentHashMap<>();
  private final Object mCobraEpgCacheLock=new Object();
  private boolean mBackgroundStopped=false;
  private final ArrayList<Channel> mChannels=new ArrayList<>();
  private Channel mCobraInspectedChannel;
  private GuideProgram mCobraInspectedProgram;
  private Object mCobraPlayerDrawer;
  private String mCobraDrawerFilter="ALL";
  private FakeShell mCobraGuideShell=new FakeShell();
  private int browserRefreshes,drawerRefreshes;
  static class FakeShell {boolean shown=true,attached=true;boolean isShown(){return shown;}boolean isAttachedToWindow(){return attached;}}
  private void cobraRenderGuideBrowser(){browserRefreshes++;}
  private void cobraRenderPlayerDrawer(String filter){drawerRefreshes++;}
'''
    cases=(ROOT/'audit_cases.java.inc').read_text()
    if (ROOT/'extra_cases.java.inc').exists():
        cases=cases.replace('    System.out.println("SUMMARY', (ROOT/'extra_cases.java.inc').read_text()+'\n    System.out.println("SUMMARY',1)
    imports='import java.io.*;import java.net.*;import java.util.*;import java.text.*;import java.util.regex.*;import java.nio.charset.StandardCharsets;import java.util.zip.*;import org.xmlpull.v1.*;import android.util.Xml;import android.net.Uri;\n'
    java=imports+'public class EpgAuditHarness {\n'+support+extra_support+'\n'+'\n\n'.join(parts)+'\n'+cases+'\n}\n'
    (out/'EpgAuditHarness.java').write_text(java)
    for directory in ('android','org'):shutil.copytree(ROOT/directory,out/directory,dirs_exist_ok=True)
    (out/'classes').mkdir(exist_ok=True)
    subprocess.run(['javac','-encoding','UTF-8','-d',str(out/'classes')]+[str(p) for p in sorted(out.rglob('*.java'))],check=True)
    result=subprocess.run(['java','-Xmx768m','-cp',str(out/'classes'),'EpgAuditHarness',str(out/'results.tsv')],capture_output=True,text=True)
    (out/'output.txt').write_text(result.stdout+result.stderr);print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
    records=[]
    if (out/'results.tsv').exists():
        for line in (out/'results.tsv').read_text().splitlines():
            row=line.split('\t',3);records.append(dict(zip(['id','status','case','detail'],row)))
    report={'source_sha256':digest(text),'test_result':result.returncode,'tests':len(records),'passed':sum(r['status']=='PASS' for r in records),
       'cases':records,'extraction':ledger,'device_verified':False,'adapters':'StAX XML, fake HTTP, host AtomicFile/URI/widgets; short HTTP JSON not included in this suite'}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(result.returncode)
if __name__=='__main__':main()
