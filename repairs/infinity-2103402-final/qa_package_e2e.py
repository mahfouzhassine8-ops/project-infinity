"""Exact content-preserving signed 2103402 corrective QA package.

The *only* runtime APK content changes are three component source members and
the compiled ARM64 native libkodi.so. No addons, Cobra, playback, providers,
search routing, user-data, manifest or version identifiers are changed.
"""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,json,shutil,argparse
from qa_component_holds import changes as approved_changes,CC,UR,WB,PREFIX,sha

BASE="Infinity-2103402-CommandCenter-03535-Matched-QA.apk"
OUT="Infinity-2103402-Continue-Context-Favourites-QA.apk"
SO="lib/arm64-v8a/libkodi.so"
SIGNATURE={"META-INF/MANIFEST.MF","META-INF/INFINITY.RSA","META-INF/INFINITY.SF"}
COMPONENTS={
 "script.infinity.commandcenter-0.3.5.35-MATCHED-QA.zip":"script.infinity.commandcenter-0.3.5.35-FIXED-QA.zip",
 "script.infinity.uirepair-0.1.18.zip":"script.infinity.uirepair-0.1.18-FIXED-QA.zip",
 "script.infinity.watchedbridge-1.0.16-MATCHED-QA.zip":"script.infinity.watchedbridge-1.0.16-FIXED-QA.zip",
 "skin.infinity.diggz-1.0.5.243.zip":"skin.infinity.diggz-1.0.5.243.zip",
}

def copy_zip(inp,output,edits,skip_signatures=False):
    with ZipFile(inp) as parent:
        originals=parent.namelist()
        if len(set(originals))!=len(originals) or not set(edits)<=set(originals):
            raise ValueError('Unreviewed ZIP inventory')
        output.parent.mkdir(parents=True,exist_ok=True)
        with ZipFile(output,"w",allowZip64=True) as result:
            for info in parent.infolist():
                if skip_signatures and info.filename in SIGNATURE:continue
                with result.open(copy.copy(info),"w",force_zip64=info.file_size>=2**31) as dest:
                    if info.filename in edits:dest.write(edits[info.filename])
                    else:
                        with parent.open(info) as source:
                            shutil.copyfileobj(source,dest,1024*1024)

def compare(original,candidate,edits):
    with ZipFile(original) as a,ZipFile(candidate) as b:
        names_a,names_b=set(a.namelist()),set(b.namelist())
        if len(names_a)!=len(a.namelist()) or len(names_b)!=len(b.namelist()):
            raise ValueError('Duplicate package members')
        if any(not k.startswith("META-INF/") for k in names_a^names_b):
            raise ValueError('Unexpected APK member inserted/removed')
        altered=[]
        for name in sorted(names_a & names_b):
            if name in SIGNATURE:continue
            with a.open(name) as x,b.open(name) as y:
                hx=hashlib.sha256();hy=hashlib.sha256()
                for stream,dig in ((x,hx),(y,hy)):
                    for chunk in iter(lambda:stream.read(1024*1024),b''):dig.update(chunk)
            if hx.digest()!=hy.digest():
                if name not in edits or hy.hexdigest()!=sha(edits[name]):
                    raise ValueError('Out-of-scope APK change: '+name)
                altered.append(name)
        if set(altered)!=set(edits):raise ValueError('Approved files not all packaged')
        for name in ["AndroidManifest.xml","classes.dex","assets/addons/skin.infinity.diggz/unified/Home.xml"]:
            if a.read(name)!=b.read(name):raise ValueError('Protected user-accepted content changed: '+name)
    return altered

def component_packages(parent_pkg,folder,edits):
    with ZipFile(parent_pkg) as a:
        for original,dest in COMPONENTS.items():
            source=folder.parent/"input"/original
            # Match independent extracted ZIP members against prior APK before editing.
            with ZipFile(source) as s:
                for name in s.namelist():
                    if not name.endswith('/') and s.read(name)!=a.read(PREFIX+name):
                        raise ValueError('Input ZIP/APK mismatch: '+name)
            selected={n[len(PREFIX):]:blob for n,blob in edits.items()
                      if n.startswith(PREFIX) and n[len(PREFIX):].startswith(original.split('-')[0]+'/')}
            out=folder/dest
            if selected:copy_zip(source,out,selected)
            else:shutil.copyfile(source,out)
            with ZipFile(out) as s:
                for name in s.namelist():
                    if name.endswith('/'):continue
                    expected=edits.get(PREFIX+name,a.read(PREFIX+name))
                    if s.read(name)!=expected:raise ValueError('Produced ZIP content mismatch: '+name)

def run(parent,compiled,out):
    if out.exists():raise ValueError('Refusing stale QA packaging output')
    signed=parent/BASE
    entries={PREFIX+name:data for name,data in approved_changes(signed).items()}
    raw=compiled.read_bytes()
    if raw[:4]!=b'\x7fELF' or raw[4]!=2 or raw[18:20]!=b'\xb7\x00':
        raise ValueError('ARM64 native image is missing')
    if len(raw)<1000000 or entries[PREFIX+CC+'context.py'] is None:
        raise ValueError('Invalid compiled native input')
    for literal in (sha(entries[PREFIX+CC+'context.py']).encode(),b'OnInfinityFavouritesLongPress'):
        if literal not in raw:raise ValueError('Compiled native changes are absent: '+literal.decode())
    with ZipFile(signed) as old:
        if raw==old.read(SO):raise ValueError('Native Favorites build was not integrated')
    entries[SO]=raw
    unsigned=out/"unsigned-2103402.apk"
    copy_zip(signed,unsigned,entries,skip_signatures=True)
    changed=compare(signed,unsigned,entries)
    component_packages(signed,out,entries)
    record={"source_build":40153625864,"parent_apk_sha256":sha(signed.read_bytes()),
            "new_native_sha256":sha(raw),"changed_app_members":changed,
            "skin_hash":"UNCHANGED","all_5_Fold_UI_passing_edits":"BYTE_IDENTICAL",
            "Cobra":"UNTOUCHED","user_profiles":"UNTOUCHED",
            "ResumeHub":"UNTOUCHED","home_performance":"UNCHANGED",
            "Search_SIGBUS":"NOT_IN_SCOPE",
            "release_acceptance":"FOLD_PENDING"}
    (out/"PACKAGING-RECEIPT.json").write_text(json.dumps(record,indent=2)+'\n')
    print("QA staged; only three addon members and libkodi.so changed")
    return entries

def verify_signed(parent,signed):
    edits={PREFIX+name:data for name,data in approved_changes(parent/BASE).items()}
    with ZipFile(signed) as z:edits[SO]=z.read(SO)
    return compare(parent/BASE,signed,edits)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=['stage','verify'])
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--native',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--signed',type=Path)
    a=p.parse_args()
    if a.action=='stage':
        if not a.native or not a.out:p.error('Stage requires native and out')
        run(a.input,a.native,a.out)
    else:
        if not a.signed:p.error('Verify requires signed')
        print('Signed member differences:',verify_signed(a.input,a.signed))
