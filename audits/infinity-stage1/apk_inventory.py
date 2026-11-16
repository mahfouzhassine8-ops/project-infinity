#!/usr/bin/env python3
"""Read-only contents inventory for Infinity QA/recovery APKs. No guest/device execution."""
from __future__ import annotations
import collections
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET

KEYWORDS = (
 "ambient","silent","cobra","health","control","center","trakt","watchlist",
 "search","resume","continue","episode","collection","favorite","movie",
 "shows","home","rail","drawer","appearance","oled","theme","network",
 "ipv4","ipv6","cast","notification","pip","subtitle","audio","player",
 "touch","gesture","rotation","fold","background","keyboard","shutdown",
 "exit","skin","addon","provider","updater","diagnostic","recovery",
 "backup","weather","sports","music","artwork","preview","cache",
 "download","history","watched","viewmode","view_mode","fullscreen","power",
 "refresh","splash","loading","progress","live","brightness","mute",
 "motion","voice","animation","startup","widget","systemhub"
)
EXTS = (".xml",".po",".json",".py",".properties",".ini",".cfg",".txt",".yml",".yaml",".md",".strings")
SMALL_TEXT_MAX = 500_000

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def safe_decode(data):
    try: return data.decode("utf-8", errors="replace")
    except Exception: return ""

def source_metadata(out):
    source=subprocess.run(['git','ls-files'],capture_output=True,text=True,check=True).stdout.splitlines()
    with gzip.open(out/'repository-tracked-paths.txt.gz','wt',encoding='utf8') as f:
        f.write('\n'.join(source)+'\n')
    categories=collections.Counter(p.split('/',1)[0] for p in source)
    sha=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    return {'source_commit':sha,'tracked_files':len(source),'top_level_file_counts':dict(categories),
            'audit_scope':'static source paths and QA/recovery package contents; not physical operation'}

def scan_apk(apk,out):
    label=apk.stem.split('-Combined')[0]
    matched=[]
    addon_descriptors=[]
    xml_labels=[]
    xml_settings=[]
    names=[]
    top=collections.Counter()
    ext=collections.Counter()
    prefix=collections.Counter()
    native=[]
    potential=[]
    nested=[]
    entries={}
    processed_text=0
    with zipfile.ZipFile(apk) as z:
        infos=z.infolist()
        with gzip.open(out/f'{label}-members.csv.gz','wt',encoding='utf8',newline='') as f:
            writer=csv.writer(f)
            writer.writerow(["path","size_uncompressed","size_compressed","crc32","compression"])
            for info in infos:
                path=info.filename
                if info.is_dir(): continue
                names.append(path)
                writer.writerow([path,info.file_size,info.compress_size,format(info.CRC,'08x'),info.compress_type])
                entries[path]=(info.file_size,info.CRC)
                p=path.lower()
                parts=p.split('/')
                top[parts[0]]+=1
                prefix['/'.join(parts[:min(4,len(parts))])]+=1
                suff=Path(p).suffix
                ext[suff]+=1
                if p.startswith('lib/') and (p.endswith('.so') or p.endswith('.jar')):
                    native.append({'path':path,'size':info.file_size})
                terms=[t for t in KEYWORDS if t in p]
                if terms:
                    matched.append({'path':path,'keywords':terms[:9],'bytes':info.file_size})
                if p.endswith(('.zip','.apk','.jar','.obb')) and info.file_size>0:
                    nested.append({'path':path,'size':info.file_size})
                if (p.endswith(EXTS) or p.endswith('/addon.xml')) and info.file_size <= SMALL_TEXT_MAX:
                    # Read only likely packaged extension data and within human-review budget.
                    try:
                        data=z.read(info)
                    except (RuntimeError, NotImplementedError):
                        continue
                    processed_text+=1
                    text=safe_decode(data)
                    if p.endswith('addon.xml'):
                        try:
                            root=ET.fromstring(data)
                            addon_descriptors.append({'path':path,'id':root.attrib.get('id'),
                                'name':root.attrib.get('name'),'version':root.attrib.get('version'),
                                'provider_name':root.attrib.get('provider-name'),
                                'extensions':[e.attrib.get('point') for e in root.findall('extension')]})
                        except ET.ParseError: pass
                    if p.endswith('.xml') or p.endswith('.json'):
                        for m in re.finditer(r'\b(?:label|name|id|description|heading|title)\s*=\s*["\x27]([^"\x27]{2,140})',text,re.I):
                            v=m.group(1).strip()
                            if v and (any(t in v.lower() for t in KEYWORDS) or 'settings' in p or 'skin' in p):
                                if len(xml_labels)<85000: xml_labels.append([path,v])
                        if p.endswith('settings.xml'):
                            for m in re.finditer(r'<setting\b[^>]{0,600}',text,re.I):
                                t=m.group(0)
                                sid=re.search(r'\bid\s*=\s*["\x27]([^"\x27]+)',t)
                                if sid and len(xml_settings)<85000:
                                    xml_settings.append([path,sid.group(1)])
                    if p.endswith('.po') and any(x in p for x in ['resource.language.en','english','en_gb','en_us','english']):
                        for ln in text.splitlines():
                            if ln.startswith('msgstr "') or ln.startswith('msgid "'):
                                v=ln[7:].strip().strip('"')
                                if any(t in v.lower() for t in KEYWORDS) and len(xml_labels)<85000:
                                    xml_labels.append([path,v])
                elif p.endswith('.zip') and 0<info.file_size<100_000_000:
                    # Nested add-ons: list metadata (do not execute code).
                    try:
                        nestedbytes=z.read(info)
                        with zipfile.ZipFile(io.BytesIO(nestedbytes)) as inz:
                            ids=inz.namelist()
                            nested[-1]['member_count']=len(ids)
                            for inn in ids:
                                if inn.lower().endswith('/addon.xml'):
                                    raw=inz.read(inn)
                                    try:
                                        rr=ET.fromstring(raw)
                                        addon_descriptors.append({'path':path+'!'+inn,
                                            'id':rr.attrib.get('id'),'name':rr.attrib.get('name'),
                                            'version':rr.attrib.get('version'),
                                            'extensions':[e.attrib.get('point') for e in rr.findall('extension')]})
                                    except ET.ParseError: pass
                    except Exception: pass

    def write_csv(filename,head,rows):
        with gzip.open(out/filename,'wt',encoding='utf8',newline='') as f:
            w=csv.writer(f);w.writerow(head);w.writerows(rows)
    write_csv(f'{label}-matched-filename-features.csv.gz',
              ['path','keyword_matches','bytes'],
              [[a['path'],';'.join(a['keywords']),a['bytes']] for a in matched])
    write_csv(f'{label}-ui-label-candidates.csv.gz',['path','label'],
              list(dict.fromkeys((x[0],x[1]) for x in xml_labels)))
    write_csv(f'{label}-xml-settings-ids.csv.gz',['path','setting_id'],
              list(dict.fromkeys((x[0],x[1]) for x in xml_settings)))
    (out/f'{label}-addon-descriptors.json').write_text(json.dumps(addon_descriptors,indent=2,ensure_ascii=False))
    (out/f'{label}-native-libraries.json').write_text(json.dumps(native,indent=2))
    report={'label':label,'apk_file':apk.name,'bytes':apk.stat().st_size,'sha256':sha256(apk),
        'total_zip_members':len(infos),'file_members':len(names),
        'top_level_members':dict(top),'extension_counts':dict(ext.most_common(75)),
        'largest_prefixes_4levels':dict(prefix.most_common(140)),
        'native_library_count':len(native),'addon_descriptor_count':len(addon_descriptors),
        'matched_feature_filename_count':len(matched),'label_candidate_count':len(xml_labels),
        'settings_id_count':len(xml_settings),'nested_archives':nested[:120],
        'processed_small_text_files':processed_text,
        'name_sample_head':names[:60],
        'matching_file_examples':matched[:200]}
    return report,entries

def main():
    src=Path(sys.argv[1]); out=Path(sys.argv[2])
    out.mkdir(parents=True,exist_ok=True)
    repo=source_metadata(out)
    reports={}; entries={}
    for apk in sorted(src.glob('*.apk')):
        report,flat=scan_apk(apk,out)
        reports[report['label']]=report
        entries[report['label']]=flat
    if len(entries)>=2:
        names=list(entries)
        a,b=entries[names[0]],entries[names[1]]
        diff={'side_a':names[0],'side_b':names[1],
              'only_a':sorted(set(a)-set(b)),'only_b':sorted(set(b)-set(a)),
              'changed_content':sorted(x for x in a.keys() & b.keys() if a[x]!=b[x])}
        (out/'release-candidate-vs-recovery-member-diff.json').write_text(json.dumps(diff,indent=2))
        reports['apk_member_comparison_summary']={key:len(value) for key,value in diff.items() if isinstance(value,list)}
    qa=[]
    for p in src.glob('*.zip'):
        with zipfile.ZipFile(p) as z:
            qa=[{'path':n.filename,'bytes':n.file_size,'crc':format(n.CRC,'08x')}
                for n in z.infolist() if not n.is_dir()]
            # Only small nonprivate known verification records; no secret keys, caches or user data.
            qadir=out/'public-qa-verification'
            qadir.mkdir(exist_ok=True)
            for v in z.infolist():
                n=v.filename
                if v.is_dir() or v.file_size>125000:continue
                if Path(n).suffix.lower() in ('.json','.md','.txt','.csv') and not any(
                    x in n.lower() for x in ['token','key','secret','password','private']):
                    target=qadir/Path(n).name
                    if not target.exists():
                        try: target.write_bytes(z.read(v))
                        except Exception: pass
        break
    for p in src.glob('*.md'):
        (out/('release-'+p.name)).write_bytes(p.read_bytes())
    for p in src.glob('SHA256SUMS'):
        (out/'release-SHA256SUMS').write_bytes(p.read_bytes())
    (out/'qa-contents.json').write_text(json.dumps(qa,indent=2))
    (out/'stage1-apk-source-summary.json').write_text(json.dumps({
        'audit': 'Infinity Stage 1: source and package content only; no dynamic acceptance',
        'repository':repo,'packages':reports,
        'warnings':['The repository main branch includes builder and legacy tools and is not independently equivalent to the packaged APK',
                    'Published QA APK and recovery APK are not proof of user-approved installed baseline',
                    'Static package evidence cannot establish whether any feature works on a physical Fold',
                    'Do not promote tests or release gates without explicit user approval']},indent=2))
    print('STAGE1 INVENTORY OK',json.dumps({k: {a:b for a,b in v.items() if a in ('apk_file','file_members','native_library_count','addon_descriptor_count','matched_feature_filename_count','label_candidate_count')} for k,v in reports.items() if isinstance(v,dict)}))

if __name__=='__main__':
    main()
