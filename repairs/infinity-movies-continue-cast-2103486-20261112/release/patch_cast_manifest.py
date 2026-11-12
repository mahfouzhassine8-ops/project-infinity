"""Stage only Cast SDK metadata/query over the exact accepted86 binary manifest.

Every original binary node/chunk and attribute is preserved. This is NOT an
authority exception, APK builder, signer or permission to mutate shared runtime.
The final original-owner gate must separately admit this exact transformation.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse,hashlib,json,struct,subprocess,types

ROOT=Path(__file__).resolve().parents[3]
LOCK='e1ef672a6f24aed6c19a14ab96d2df6fe3380460'
BASE='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
def original_tool():
    raw=subprocess.check_output(['git','show',LOCK+':repairs/infinity-final-closure-2103407/p0/manifest.py'],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()=='d4664d19b60683ca816a537ecfc6629199500ed3e1cde59fded2632d394a2f12'
    tool=types.ModuleType('unchanged_original_AXML');exec(compile(raw,'immutable-original-AXML','exec'),tool.__dict__);return tool
def patch(raw):
    m=original_tool();parts=list(m.chunks(raw));pool=next(p for _,kind,p in parts if kind==1);old=m.string_pool(pool)
    required=['meta-data','package','application','queries','name','value']
    assert all(n in old for n in required),'Exact86 manifest structure required'
    sdk='com.google.android.gms.version';options='com.google.android.gms.cast.framework.OPTIONS_PROVIDER_CLASS_NAME'
    provider='com.projectinfinity.kodi.InfinityCastOptions';query='com.google.android.gms.policy_cast_dynamite'
    assert sdk not in old and options not in old and query not in old,'Already extended/unknown manifest generation'
    revised=m.append_strings(pool,[s for s in (sdk,options,provider,query) if s not in old]);strings=m.string_pool(revised)
    resource_map=next(p for _,kind,p in parts if kind==0x180)
    ids=list(struct.unpack('<'+'I'*((len(resource_map)-8)//4),resource_map[8:]))
    def node(tag,attrs):
        return m.start(tag,sorted(attrs,key=lambda x:ids[strings.index(x[0])]),strings)+m.end(tag,strings)
    metadata=node('meta-data',[('name',3,sdk),('value',0x10,12451000)])+node('meta-data',[('name',3,options),('value',3,provider)])
    visibility=node('package',[('name',3,query)])
    output=[];app=queries=0;original_chunks=[];after_chunks=[]
    for _,kind,part in parts:
        if kind==1:output.append(revised);continue
        if kind==0x103:
            tag=strings[struct.unpack_from('<I',part,20)[0]]
            if tag=='application':output.append(metadata);app+=1
            if tag=='queries':output.append(visibility);queries+=1
        output.append(part);original_chunks.append(part)
    assert app==queries==1,'Exactly one existing application/query boundary'
    body=b''.join(output);result=struct.pack('<HHI',3,8,len(body)+8)+body
    # Remove ONLY our exact inserted node pairs from the derived stream. The
    # remaining original bytes, including permissions/components/attributes,
    # resources map, startup/close declarations and typed version, must match.
    remaining=result[8:];assert remaining.count(metadata)==remaining.count(visibility)==1
    remaining=remaining.replace(metadata,b'',1).replace(visibility,b'',1).replace(revised,pool,1)
    assert struct.pack('<HHI',3,8,len(remaining)+8)+remaining==raw,'Protected manifest bytes changed'
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apk',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    with args.apk.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==BASE
    with ZipFile(args.apk) as z:raw=z.read('AndroidManifest.xml')
    value=patch(raw);args.out.mkdir(exist_ok=False)
    (args.out/'AndroidManifest.xml').write_bytes(value)
    (args.out/'MANIFEST-TRANSFORMATION.json').write_text(json.dumps(dict(schema=1,
        status='PASS_EXACT_BINARY_ADDITIONS_ONLY_NOT_RELEASE_ADMITTED',baseline=2103486,
        original_sha256=hashlib.sha256(raw).hexdigest(),derived_sha256=hashlib.sha256(value).hexdigest(),
        additions=['Cast SDK version metadata','Infinity-only OptionsProvider metadata','One Cast Dynamite package visibility query'],
        new_permissions=False,new_components=False,existing_attribute_changes=False,APK=False,
        original_release_authority_exception='PENDING_EXACT_CAST_ADMISSION'),indent=2)+'\n')
    print('PASS_EXACT_CAST_METADATA_QUERY_ONLY; ORIGINAL_RELEASE_ADMISSION_STILL_REQUIRED')
