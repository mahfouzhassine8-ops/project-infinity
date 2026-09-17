#!/usr/bin/env python3
"""Isolated EPG repair. Verify each preimage; never edit native code or APKs.

Run with --source <generated InfinityLiveActivity.java.in> --output <new file>
--receipt <JSON>. Accepted method preimages come from the verified 2103153
source inherited by 2103154. Do not use this patcher on arbitrary builds.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()

def span(text: str, name: str, kind: str = 'method') -> tuple[int, int]:
    if kind == 'class': pattern = r'^  private (?:static )?(?:final )?class ' + re.escape(name) + r'\b'
    elif kind == 'field': pattern = r'^  private final Runnable ' + re.escape(name) + r'\b'
    else: pattern = r'^  (?:private|public|protected) [^\n;=(){}]*\b' + re.escape(name) + r'\s*\('
    matches = list(re.finditer(pattern, text, re.M))
    if len(matches) != 1: raise ValueError(f'{name}: expected one declaration, got {len(matches)}')
    start = matches[0].start(); i = text.index('{', start); depth = 0; state = 'code'
    while i < len(text):
        ch, pair = text[i], text[i:i+2]
        if state in ('str','char'):
            if ch == '\\': i += 2; continue
            if ch == ('"' if state == 'str' else "'"): state = 'code'
        elif state == 'line':
            if ch == '\n': state = 'code'
        elif state == 'block':
            if pair == '*/': state = 'code'; i += 2; continue
        elif pair == '//': state = 'line'; i += 2; continue
        elif pair == '/*': state = 'block'; i += 2; continue
        elif ch == '"': state = 'str'
        elif ch == "'": state = 'char'
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: return start, i + (2 if kind == 'field' else 1)
        i += 1
    raise ValueError(name + ': unterminated declaration')

def change_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1: raise ValueError('Patch anchor mismatch: ' + old[:100])
    return text.replace(old, new, 1)

def patch(before: str) -> tuple[str, dict]:
    if digest(before) not in {'00d8984b7979db9400fd2e0799ae3736b3cb579953c6a847fd3d193ab1fa6872', '923a43943ecdf0ff096eb3206cd7ab70dcb22063d2f23f5856546b62469ff326'}:
        raise ValueError('Unsupported generated Activity: '+digest(before))
    expected = json.loads((ROOT/'preimages.json').read_text())
    for key, sha in expected.items():
        kind, name = key.split(':'); a,b = span(before,name,kind)
        if digest(before[a:b]) != sha: raise ValueError('Unsupported preimage: ' + key)
    text = before; changes = []; appended = []
    def replace(name: str, code: str, kind: str = 'method') -> None:
        nonlocal text
        a,b = span(text,name,kind); text = text[:a]+code.rstrip()+text[b:]; changes.append((kind,name))
    def transform(name: str, fn, kind: str = 'method') -> None:
        a,b=span(text,name,kind); replace(name,fn(text[a:b]),kind)
    parts = re.split(r'^// @(replace [A-Za-z0-9_]+|append)\s*\n',(ROOT/'guide-repair.java.inc').read_text(),flags=re.M)
    if parts[0].strip() or len(parts)%2 != 1: raise ValueError('Invalid repair module')
    for marker,code in zip(parts[1::2],parts[2::2]):
        if marker == 'append': appended.append(code.rstrip())
        else: replace(marker.split()[1],code)
    fields = '''  // EPG repair: main-thread force flags; cross-worker generation and disk serialization.
  private final Set<String> mCobraForceEpg = new HashSet<>();
  private final java.util.concurrent.atomic.AtomicLong mCobraEpgSequence = new java.util.concurrent.atomic.AtomicLong();
  private final java.util.concurrent.ConcurrentHashMap<String, Long> mCobraEpgGenerations = new java.util.concurrent.ConcurrentHashMap<>();
  private final Object mCobraEpgCacheLock = new Object();
'''
    text=change_once(text,'  private final Handler mMain = new Handler(Looper.getMainLooper());\n',
                    '  private final Handler mMain = new Handler(Looper.getMainLooper());\n'+fields)
    transform('CobraEpgData', lambda s: change_once(s,'    long fetched = 0L;',
              '    long fetched = 0L;\n    long requestGeneration = 0L;\n    long coverageEnd = -1L;'), 'class')
    def parse(s):
        s=change_once(s,'          programme.stop=parseXmlTvTime(parser.getAttributeValue(null,"stop"));',
         '          String end=parser.getAttributeValue(null,"stop");\n'
         '          // -1 is an explicitly unknown end, never a fabricated duration.\n'
         '          programme.stop=end==null||end.trim().isEmpty()?-1L:parseXmlTvTime(end);')
        s=change_once(s,'programme.start>0 && programme.stop>programme.start\n              && programme.stop>=min',
         'programme.start>0 && (programme.stop>programme.start || programme.stop==-1L)\n'
         '              && (programme.stop>=min || (programme.stop==-1L && programme.start>=min))')
        return change_once(s,'    return data;','    cobraEpgHasCoverage(data, System.currentTimeMillis());\n    return data;')
    transform('cobraParseGuide',parse)
    def read(s):
        s=change_once(s,'    android.util.AtomicFile file=new android.util.AtomicFile(cobraEpgCacheFile(sourceId));',
         '    synchronized(mCobraEpgCacheLock) {\n'
         '    File snapshot=cobraEpgSnapshotFile(sourceId,identity);\n'
         '    // Read legacy v3 only as a migration fallback, with the same identity check.\n'
         '    android.util.AtomicFile file=new android.util.AtomicFile((snapshot.exists()||new File(snapshot.getPath()+".bak").exists())?snapshot:cobraEpgCacheFile(sourceId));')
        s=change_once(s,'        if(p.stop<=p.start) continue;','        if(p.start<=0 || (p.stop<=p.start && p.stop!=-1L)) continue;')
        s=change_once(s,'      return data;','      cobraEpgHasCoverage(data,System.currentTimeMillis());\n      return data;')
        return s[:-1]+'}\n  }'
    transform('cobraReadEpgCache',read)
    def write(s):
        s=change_once(s,'    android.util.AtomicFile file=new android.util.AtomicFile(cobraEpgCacheFile(sourceId));',
         '    synchronized(mCobraEpgCacheLock) {\n'
         '    if(!isCobraAsyncAlive() || (data.requestGeneration!=0 && !cobraEpgGenerationCurrent(sourceId,data.requestGeneration))) return;\n'
         '    File snapshot=cobraEpgSnapshotFile(sourceId,data.identity);\n'
         '    android.util.AtomicFile file=new android.util.AtomicFile(snapshot);')
        s=change_once(s,'      out.flush();gzip.finish();file.finishWrite(stream);stream=null;',
         '      out.flush();gzip.finish();\n'
         '      if(!isCobraAsyncAlive() || (data.requestGeneration!=0 && !cobraEpgGenerationCurrent(sourceId,data.requestGeneration))){file.failWrite(stream);stream=null;return;}\n'
         '      file.finishWrite(stream);stream=null;')
        s=change_once(s,'      if(sourceId.startsWith("@short:"))cobraPruneShortGuideCache();',
         '      if(sourceId.startsWith("@short:"))cobraPruneShortGuideCache();\n'
         '      else cobraPruneSourceGuideSnapshots(sourceId,snapshot);')
        return s[:-1]+'}\n  }'
    transform('cobraWriteEpgCache',write)
    def short(s):
        s=change_once(s,'    if(cobraCurrentProgram(channel)!=null && cobraNextProgram(channel)!=null)return;',
         '    final boolean force=mCobraForceEpg.remove("@short:"+channel.id);\n'
         '')
        s=change_once(s,'    long now=System.currentTimeMillis();Long last=mCobraShortEpgAttempt.get(channel.id);\n    if(last!=null&&now-last<15L*60000L)return;',
         '    long now=System.currentTimeMillis();')
        s=change_once(s,'    if(chosen==null)return;','    if(chosen==null || !mFeatures.sourceEnabled(chosen.id))return;')
        s=change_once(s,'    final LiveSource source=chosen;final String identity=cobraEpgIdentity(source);',
         '    final LiveSource source=chosen;final String identity=cobraEpgIdentity(source);\n'
         '    CobraEpgData existing=mCobraEpg.get(sourceId);\n'
         '    if(!force && existing!=null && identity.equals(existing.identity) && cobraCurrentProgram(channel)!=null && cobraNextProgram(channel)!=null)return;\n'
         '    String attemptKey=channel.id+"|"+identity;Long last=mCobraShortEpgAttempt.get(attemptKey);\n'
         '    if(!force && last!=null && now-last>=0 && now-last<15L*60000L)return;\n'
         '    final String cacheKey="@short:"+channel.id;final long generation=cobraNextEpgGeneration(cacheKey);')
        s=change_once(s,'mCobraShortEpgAttempt.put(channel.id,now);','mCobraShortEpgAttempt.put(attemptKey,now);')
        s=change_once(s,'if(cached!=null&&System.currentTimeMillis()-cached.fetched<15L*60000L&&cached.programs.containsKey("@stream:"+channel.id))',
         'if(!force&&cached!=null&&System.currentTimeMillis()-cached.fetched<15L*60000L&&cached.programs.containsKey("@stream:"+channel.id)\n'
         '            &&cobraFindProgrammeAt(cached.programs.get("@stream:"+channel.id),System.currentTimeMillis())!=null)')
        s=change_once(s,'stored.identity=identity;stored.fetched=', 'stored.identity=identity;stored.requestGeneration=generation;stored.fetched=')
        s=change_once(s,'        mCobraShortEpgBusy.remove(channel.id);',
         '        if(!cobraEpgGenerationCurrent(cacheKey,generation))return;\n        mCobraShortEpgBusy.remove(channel.id);')
        s=change_once(s,'if(data==null){data=new CobraEpgData();data.identity=identity;',
         'if(data==null||!identity.equals(data.identity)){data=new CobraEpgData();data.identity=identity;')
        return s
    transform('cobraRequestShortEpg',short)
    def tick(s):
        s=change_once(s,'      if (!isCobraAsyncAlive()) return;','      if (!cobraGuidePresentationActive()) return;')
        return change_once(s,'      if (mCobraPreviewPlayer != null || mPlayer != null || !mCobraTiles.isEmpty())',
         '      if (cobraGuidePresentationActive())')
    transform('mCobraPresentationTick',tick,'field')
    transform('cobraStartPresentationTicker',lambda s: change_once(s,'if(isCobraAsyncAlive())mMain.postDelayed',
       'if(cobraGuidePresentationActive())mMain.postDelayed'))
    transform('showProgramGuide',lambda s: change_once(change_once(s,'if(p.stop>now-3600000L&&shown++<80)',
      'if(cobraProgrammeInSchedule(p,now-3600000L)&&shown++<80)'),
      'formatTime(p.start)+" – "+formatTime(p.stop)','cobraProgrammeTimeLabel(p)'))
    def actions(s):
        s=change_once(s,'formatTime(program.start)+" – "+formatTime(program.stop)+" • "+channel.name',
          'cobraProgrammeTimeLabel(program)+" • "+channel.name')
        s=change_once(s,'      rows.addView(cobraSheetRow("record","Schedule recording"',
          '      if(cobraProgrammeHasEnd(program))rows.addView(cobraSheetRow("record","Schedule recording"')
        return change_once(s,'if(program.stop<now&&mArchiveChannels.contains(channel.id))',
          'if(cobraProgrammeHasEnd(program)&&program.stop<now&&mArchiveChannels.contains(channel.id))')
    transform('showProgramActions',actions)
    transform('cobraGuideStatus',lambda s:change_once(s,'    return "No programme scheduled for this time";',
      '    ArrayList<GuideProgram> records=cobraPrograms(channel);\n'
      '    if(records!=null)for(GuideProgram p:records)if(p.stop==-1L)return "Schedule has unknown end times • open channel schedule";\n'
      '    return "No programme scheduled for this time";'))
    transform('loadAllEnabledSources',lambda s:change_once(s,'        mChannels.clear(); mChannels.addAll(resolved);',
      '        mChannels.clear(); mChannels.addAll(resolved);\n'
      '        if(changed && hadWarmLibrary)cobraRefreshChannelMetadata();'))
    metadata='''  private void cobraRefreshChannelMetadata() {
    for (Channel channel : mChannels) {
      if (mGuidePreviewChannel != null && channel.id.equals(mGuidePreviewChannel.id)) mGuidePreviewChannel = channel;
      if (mPlaying != null && channel.id.equals(mPlaying.id)) mPlaying = channel;
'''
    if 'mCobraInspectedChannel' in before:
        metadata+='      if (mCobraInspectedChannel != null && channel.id.equals(mCobraInspectedChannel.id)) { if(!java.util.Objects.equals(channel.epgId,mCobraInspectedChannel.epgId))mCobraInspectedProgram=null; mCobraInspectedChannel = channel; }\n'
    metadata+='''    }
    mCobraResolvedEpg.clear();
    cobraRefreshProgrammeLabels();
    if (mCobraGuideShell != null && mCobraGuideShell.isAttachedToWindow()) cobraRenderGuideBrowser();
    if (mCobraPlayerDrawer != null) cobraRenderPlayerDrawer(mCobraDrawerFilter);
  }
'''
    appended.append(metadata)
    at=text.rfind('\n}'); text=text[:at]+'\n\n'+'\n\n'.join(appended)+text[at:]
    # All non-targeted class-level methods, including native/session/render ownership, stay exact.
    names=set(re.findall(r'^  (?:private|public|protected) [^\n;=(){}]*\b([A-Za-z0-9_]+)\s*\(',before,re.M))
    changed_names={name for _,name in changes}
    protected=[]
    for name in sorted(names-changed_names):
        try: a,b=span(before,name); x,y=span(text,name)
        except ValueError: continue # Overloads are not edited; the final patch has an explicit allowlist.
        if before[a:b]!=text[x:y]: raise ValueError('Protected method changed: '+name)
        protected.append(name)
    if 'CobraModeLayout' in before:
        for name in ['CobraModeLayout','CobraBroadcastRow','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow']:
            a,b=span(before,name,'class');x,y=span(text,name,'class')
            if before[a:b]!=text[x:y]:raise ValueError('Layout class changed: '+name)
    receipt={'repair':'cobra-epg-data-rc1','before_sha256':digest(before),'after_sha256':digest(text),
      'changed_members':[kind+':'+name for kind,name in changes],
      'protected_method_count':len(protected),'protected_methods':protected,
      'adaptive_layouts_present':'CobraModeLayout' in before,'native_changed':False,
      'device_verified':False,'apk_built':False,'preimages_verified':expected}
    return text,receipt

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    args=p.parse_args()
    if args.source.resolve()==args.output.resolve():raise ValueError('Output must not overwrite the source/rollback')
    before=args.source.read_text();after,receipt=patch(before)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(after);args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: verified preimages; isolated EPG repair applied; protected methods unchanged.')
if __name__=='__main__':main()
