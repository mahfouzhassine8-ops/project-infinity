import sys,subprocess,re
from pathlib import Path
sys.path.insert(0,'/workspace/project-infinity/repairs/dual-experience-isolation-2103420')
from inventory import HERE,load,save,file_sha,CERT_SHA,canonical,digest
from release_gate import inspect_candidate,validate_runtime_ownership,require
from release_authority import verify
root=Path(sys.argv[1]);apk=root/'Infinity-2103423-Combined-Original-Signer.apk';receipt=load(root/'BUILD-RECEIPT.json');authority=load(root/'release-authority.json')
require(authority==load(HERE/'release-authority.json'),'DELIVERED_AUTHORITY_MISMATCH')
require(receipt['source']=='0b0538374a2420255a372dc02879feb692da15dc','SIGNED_SOURCE')
require(receipt['generation']==6 and authority['guard_schema']==2,'FINAL_GUARD_SCHEMA')
require(receipt['registry_sha256']==digest(canonical(authority)),'SIGNED_AUTHORITY_HASH')
require(file_sha(apk)==receipt['signed_apk_sha256'],'SIGNED_APK_HASH')
require((root/'SHA256SUMS').read_text().split()[0]==file_sha(apk),'SHA256SUMS')
sdk=Path('/workspace/infinity-artifacts/android-sdk/android-15')
cert=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(apk)],text=True)
require(re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)',cert)==[CERT_SHA],'ORIGINAL_CERTIFICATE')
for v in ('v1','v2','v3'):require(re.search(r'Verified using '+v+r' scheme.*: true',cert) is not None,'SIGNATURE_SCHEME:'+v)
subprocess.run([str(sdk/'zipalign'),'-c','-P','16','4',str(apk)],check=True)
audit=root/'actual-dex';actual,version=inspect_candidate(apk,Path('/workspace/infinity-artifacts/tools/receipt-evidence/tool-jars'),audit)
validate_runtime_ownership(authority,audit);verified=verify(authority,actual,version,6)
lock=subprocess.check_output(['git','-C','/workspace/project-infinity','ls-remote','origin','refs/heads/lock/infinity-2103420-user-approved-baseline-20261026'],text=True).split()[0]
require(lock=='883c64a4de6f87077893921454de71bba850235b','PROTECTED_BASELINE_MOVED')
require(file_sha(HERE/'accepted-combined-release.json')==authority['accepted_registry_sha256'],'ACCEPTED_POINTER_CHANGED')
verified.update(status='READY_FOR_FOLD_CHECK',signed_apk_sha256=file_sha(apk),bytes=apk.stat().st_size,
 certificate_sha256=CERT_SHA,versionCode=version,build_run=40486072720,source=receipt['source'],
 protected_lock=lock,accepted_pointer_updated=False,physical_Fold='PENDING',original_signature_schemes=['v1','v2','v3'],
 actual_packaged_identities_verified=len(actual),one_original_launcher=True)
save(root/'DELIVERY-VERIFICATION.json',verified);print(verified)
