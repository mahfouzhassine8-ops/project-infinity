import hashlib,importlib.util,json,pathlib,zipfile
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
root=pathlib.Path('/workspace/infinity-network-family'); base=pathlib.Path('/workspace/scratch/network-baseline-2103477'); apk=base/'files/Infinity-2103477-Combined-Original-Signer.apk'; old=pathlib.Path('/workspace/scratch/tracking-signed-42615752695/files/Infinity-2103474-Combined-Original-Signer.apk')
h=lambda b:hashlib.sha256(b).hexdigest()
assert hashlib.file_digest(apk.open('rb'),'sha256').hexdigest()=='93eb081cd6a86ff9cf1cb9aa75bc6d9087cd9c982fb46e0a9baa12c12aa9af22'
spec=importlib.util.spec_from_file_location('retest',root/'repairs/infinity-exact74-retest-2103477/exact74_retest.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
proof=m.verify_members(old,apk)
with zipfile.ZipFile(apk) as z:
    manifest=z.read(m.MANIFEST);sig=z.read(m.SIGNATURE)
    public=load_pem_public_key((root/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_bytes())
    public.verify(sig,manifest,padding.PKCS1v15(),hashes.SHA256())
    lines=[line.split('\t') for line in manifest.decode().splitlines() if line.startswith('file\t')];assert len(lines)==80
    records={name:h(z.read('assets/addons/'+name)) for _,sha,name in lines};assert all(records[name]==sha for _,sha,name in lines)
    extract=base/'source'; wanted=[i.filename for i in z.infolist() if i.filename.startswith('assets/addons/script.infinity.commandcenter/') or i.filename.endswith('Custom_1191_InfinitySystemHub.xml') or i.filename in ['assets/addons/skin.infinity.diggz/addon.xml','assets/experience-component-updates.properties']]
    for name in wanted:
        p=extract/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    maps={}
    for prefix in ['lib/','classes','assets/addons/script.module.tmdbhelper.sync.trakt/']:
        maps[prefix]={i.filename:h(z.read(i.filename)) for i in z.infolist() if i.filename.startswith(prefix)}
    source_check={}
    for name in ['plugin.py','service.py','resume_hub.py']:
        path=root/'repairs/infinity-tracking-integration-2103469-20261108/overlay/script.infinity.commandcenter'/name
        source_check[name]={'apk_sha256':h(z.read(m.PREFIX+name)),'git_source_present':path.exists(),'matches':path.exists() and h(path.read_bytes())==h(z.read(m.PREFIX+name))}
    result={'status':'PASS_SIGNED_BASELINE_ARTIFACT','apk_sha256':hashlib.file_digest(apk.open('rb'),'sha256').hexdigest(),'versionCode':2103477,'Command_Center':'0.3.5.75','APK_signature':'PASS_ORIGINAL_CERT_V1_V2_V3_LOCAL_APKSIG','module_signature':'PASS_ORIGINAL_PUBLIC_KEY_RSA_SHA256','module_manifest_sha256':h(manifest),'module_files':len(lines),'module_integrity':'PASS_ALL_80','source_checkpoint':'80f9c78e5c133ef63abe95af359c3e4e7366153f','sign_run':42724088145,'artifact_id':13721668270,'owner_accepted_working_baseline':True,'owner_acceptance_source':'Current user instruction; no new automated playback claim','metadata_only_proof':proof,'production_overlay_checks':source_check,'labels':z.read('assets/experience-component-updates.properties').decode(),'component_fingerprints':maps}
(base/'BASELINE-VERIFICATION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['component_fingerprints','metadata_only_proof']},indent=2))
