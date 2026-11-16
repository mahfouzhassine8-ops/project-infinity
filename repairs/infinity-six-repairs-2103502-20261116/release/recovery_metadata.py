"""Forward version metadata for exact502 code, without profile restoration."""
import hashlib, json

SKIN='assets/addons/skin.infinity.diggz/'

def scalar(raw,key,before,after):
    old=('"'+key+'": '+json.dumps(before)).encode()
    new=('"'+key+'": '+json.dumps(after)).encode()
    assert raw.count(old)==1,(key,before)
    return raw.replace(old,new,1)

def replacements(archive):
    health='assets/addons/script.kodihealthcenter/addon.xml'
    original=archive.read(health);assert original.count(b'version="2.5.27"')==1
    result={health:original.replace(b'version="2.5.27"',b'version="2.5.29"',1)}
    addon=archive.read(SKIN+'addon.xml');assert addon.count(b'version="1.0.5.274"')==1
    result[SKIN+'addon.xml']=addon.replace(b'version="1.0.5.274"',b'version="1.0.5.276"',1)
    info=archive.read(SKIN+'infinity-skin.json')
    for key,before,after in [('candidate',274,276),('version','1.0.5.274','1.0.5.276'),('skin_version','1.0.5.274','1.0.5.276')]:
        info=scalar(info,key,before,after)
    result[SKIN+'infinity-skin.json']=info
    manifest=archive.read(SKIN+'Infinity-Protected-Manifest.json')
    for key,before,after in [('candidate',274,276),('candidate_version','1.0.5.274','1.0.5.276'),('skin_version','1.0.5.274','1.0.5.276')]:
        manifest=scalar(manifest,key,before,after)
    protected=json.loads(manifest)['protected_files']
    for name in ('addon.xml','infinity-skin.json'):
        manifest=scalar(manifest,name,protected[name],hashlib.sha256(result[SKIN+name]).hexdigest())
    result[SKIN+'Infinity-Protected-Manifest.json']=manifest
    return result
