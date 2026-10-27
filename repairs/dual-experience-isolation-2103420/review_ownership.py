"""Assign explicit owners and check actual post-transform dependency edges.

Classification does not approve a release. Runtime, module-combination and
original-signer gates remain separate required evidence.
"""
import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile
from inventory import HERE,APP,APK_SHA,MEMBER,SIGNATURE,load,save,digest,file_sha
from prepare_runtime import methods

TYPES=re.compile(r'L[^;\s"<>:(),{}]+;')

def class_owner(name,text,policy):
    if 'ExternalSyntheticApiModelOutline' in name:
        if re.search(r'^\.field ',text,re.M):raise ValueError('Stateful OS outline: '+name)
        return 'MINIMAL_ANDROID_CONTRACT'
    if name.startswith(APP):
        root=name[len(APP):].split('$')[0].rstrip(';')
        if root not in policy['project_roots']:raise ValueError('Unreviewed project class: '+name)
        return policy['project_roots'][root]
    matches=[owner for prefix,owner in policy['library_families'].items() if name.startswith(prefix)]
    if len(matches)!=1:raise ValueError('Unreviewed dependency: '+name)
    return matches[0]

def member_owner(name):
    if name in SIGNATURE:return 'MINIMAL_ANDROID_CONTRACT'
    if re.fullmatch(r'classes\d*\.dex',name):return 'DEX_CONTAINER'
    if name.startswith('assets/addons/script.infinity.cobra.theme/'):return 'COBRA'
    if name.startswith(('assets/addons/','assets/python3.11/','assets/system/','assets/media/','assets/userdata/','assets/infinity/','lib/')):return 'INFINITY'
    if re.fullmatch(r'assets/infinity-\d+-components.json',name):return 'INFINITY'
    if name.startswith('kotlin/'):return 'COBRA'
    if name=='META-INF/androidx.exifinterface_exifinterface.version':return 'COBRA'
    if name=='META-INF/androidx.tvprovider_tvprovider.version':return 'INFINITY'
    if name in ('AndroidManifest.xml','resources.arsc','assets/privacy-policy.txt') or name.startswith(('res/','META-INF/')):return 'MINIMAL_ANDROID_CONTRACT'
    raise ValueError('Unreviewed package member: '+name)

def review(work,baseline,out):
    if file_sha(baseline)!=APK_SHA:raise ValueError('Exact signed baseline required')
    policy=load(HERE/'ownership-reviewed-roots.json');out.mkdir()
    definitions={}
    for p in (work/'owner-dex').glob('*/part-*/**/*.smali'):
        text=p.read_text();name=text.splitlines()[0].split()[-1]
        if name in definitions:raise ValueError('Duplicate class')
        definitions[name]=text
    classes={n:{'owner':class_owner(n,t,policy),'sha256':digest(t.encode()),'methods':{s:digest(b.encode()) for s,b in methods(t).items()}}
             for n,t in definitions.items()}
    edges=[];forbidden=[];outline_proofs=[];native=[];dynamic=[]
    for name,text in definitions.items():
        source_owner=classes[name]['owner']
        for sig,body in methods(text).items():
            if ' native ' in ' '+body.splitlines()[0]+' ':native.append({'class':name,'method':sig,'owner':source_owner})
            for line in body.splitlines():
                match=MEMBER.search(line)
                if not match:continue
                target,member=match.groups()
                if target not in classes:continue
                target_owner=classes[target]['owner']
                if source_owner!=target_owner:
                    edge={'from':name,'method':sig,'to':target,'member':member,'opcode':line.strip().split()[0],
                          'from_owner':source_owner,'to_owner':target_owner}
                    edges.append(edge)
                    if {source_owner,target_owner}=={'COBRA','INFINITY'}:forbidden.append(edge)
                if 'ExternalSyntheticApiModelOutline' in name:
                    # Calls with an app receiver may resolve to inherited OS
                    # methods. Actual app-declared methods/fields are not OS
                    # adapters and may not be relabeled as a shared contract.
                    if (member in classes[target]['methods'] and 'ExternalSyntheticApiModelOutline' not in target) or not line.strip().startswith('invoke-'):
                        raise ValueError('Feature-bearing OS outline: '+name+' '+member)
            if any(k in body for k in ('->forName(', '->loadClass(', '->loadLibrary(', '->load(Ljava/lang/String;)V')):
                dynamic.append({'class':name,'method':sig,'owner':source_owner,'sha256':digest(body.encode()),
                                'literals':re.findall(r'const-string(?:/jumbo)? [^,]+, "(.*)"',body)})
        if 'ExternalSyntheticApiModelOutline' in name:outline_proofs.append(name)
    if forbidden:
        save(out/'FORBIDDEN-CROSS-FEATURE-EDGES.json',forbidden)
        raise ValueError('Direct cross-experience feature dependencies remain: '+str(len(forbidden)))
    if any(x['owner']=='COBRA' and x['class'].startswith(APP) for x in native):raise ValueError('Unreviewed Cobra JNI')
    members={};native_members={};python_members={}
    with ZipFile(baseline) as apk,tempfile.TemporaryDirectory(prefix='infinity-native-inventory-') as temp:
        for info in apk.infolist():
            raw=apk.read(info);owner=member_owner(info.filename)
            members[info.filename]={'owner':owner,'sha256':digest(raw),'size':len(raw)}
            if info.filename.endswith('.so'):
                p=Path(temp)/Path(info.filename).name;p.write_bytes(raw)
                symbols=subprocess.check_output(['readelf','--dyn-syms','--wide',str(p)],text=True)
                functions=[]
                for line in symbols.splitlines():
                    values=line.split()
                    if len(values)>=8 and values[3]=='FUNC' and values[6]!='UND':
                        functions.append({'symbol':values[7],'address':values[1],'size':values[2],'owner':owner})
                dependencies=subprocess.check_output(['readelf','--dynamic','--wide',str(p)],text=True)
                native_members[info.filename]={'owner':owner,'whole_library_sha256':digest(raw),'defined_dynamic_functions':functions,
                   'needed':re.findall(r'\(NEEDED\).*\[(.*?)\]',dependencies),
                   'guard':'Whole ELF hash covers every function, relocation and stripped/inlined body; all remain baseline-identical'}
            if info.filename.endswith('.py'):
                python_members[info.filename]={'owner':owner,'sha256':digest(raw),
                  'basis':'Cobra theme resource-module initializer' if owner=='COBRA' else 'Kodi-owned Python loader/runtime/add-on namespace'}
    save(out/'CLASSES.json.gz',classes);save(out/'CROSS-OWNER-EDGES.json.gz',edges)
    save(out/'NATIVE-OWNERS.json.gz',native_members);save(out/'PYTHON-OWNERS.json.gz',python_members)
    save(out/'DYNAMIC-SITES.json',dynamic)
    save(out/'OWNERSHIP.json',{'schema':1,'status':'CLASSIFIED_NO_DIRECT_CROSS_EXPERIENCE_FEATURE_CALLS',
       'release_approved':False,'baseline_apk_sha256':APK_SHA,'classes':dict(Counter(c['owner'] for c in classes.values())),
       'members':members,'native_declarations':native,'stateless_os_outlines_verified':outline_proofs,
       'cross_owner_edge_count':len(edges),'direct_infinity_cobra_feature_edges':0,
       'policy_sha256':file_sha(HERE/'ownership-reviewed-roots.json'),
       'limitations':['Static ownership and complete payload hashes do not prove arbitrary runtime reflection targets','Read-only diagnostic export and packaged theme deployment are explicit container integration contracts','Device and physical Fold acceptance remain separate']})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('work','baseline','out'):p.add_argument('--'+n,type=Path,required=True)
    review(**vars(p.parse_args()))
