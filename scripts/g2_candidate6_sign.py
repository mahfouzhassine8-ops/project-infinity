#!/usr/bin/env python3
"""Sign only with G2 #5's actual certificate. No silent throwaway-key fallback."""
from __future__ import annotations
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from g2_candidate6 import digest, inventory, spec

NAMES = ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS')

def sign(unsigned: Path, output: Path, sdk: Path, expected: str, env: dict[str,str]) -> dict:
    supplied = [bool(env.get(n)) for n in NAMES]
    if not any(supplied):
        return {'signed':False, 'install_over_g2_5':False,
                'status':'unsigned-awaiting-original-signing-key',
                'message':'Mapping build passed; no compatible signing credentials supplied. Keep testing #5; do not uninstall it.'}
    if not all(supplied):
        raise ValueError('Incomplete signing configuration. No fallback key will be generated.')
    if output.exists() or output.resolve() == unsigned.resolve():
        raise ValueError('Signing output must be a new file, distinct from the unsigned input')
    bt=sdk/'build-tools/34.0.0'
    with tempfile.TemporaryDirectory(prefix='g2-sign-') as tmp:
        root=Path(tmp)
        key=root/'private.keystore'
        key.write_bytes(base64.b64decode(env[NAMES[0]],validate=True))
        key.chmod(0o600)
        public=root/'cert.der'
        clean_env = dict(env)
        clean_env.pop('INFINITY_KEYSTORE_B64',None)
        # Never print passwords, key material or subprocess environment.
        subprocess.run(['keytool','-exportcert','-keystore',str(key),'-alias',env[NAMES[3]],
                        '-storepass:env',NAMES[1],'-file',str(public)],
                       env=clean_env,check=True,capture_output=True)
        if digest(public.read_bytes()) != expected:
            raise ValueError('Supplied certificate does not match G2 #5. Signing withheld to protect in-place updates.')
        aligned=root/'aligned.apk'
        subprocess.run([str(bt/'zipalign'),'-p','-f','4',str(unsigned),str(aligned)],check=True)
        signed=root/'signed.apk'
        subprocess.run([str(bt/'apksigner'),'sign','--ks',str(key),'--ks-key-alias',env[NAMES[3]],
                        '--ks-pass','env:'+NAMES[1],'--key-pass','env:'+NAMES[2],
                        '--out',str(signed),str(aligned)],env=clean_env,check=True,capture_output=True)
        result=subprocess.run([str(bt/'apksigner'),'verify','--verbose','--print-certs',str(signed)],
                              check=True,capture_output=True,text=True)
        certs=re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',result.stdout)
        if certs != [expected] or inventory(unsigned) != inventory(signed):
            raise ValueError('Final signer or protected APK bytes differ')
        subprocess.run([str(bt/'zipalign'),'-c','-p','4',str(signed)],check=True,capture_output=True)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(signed.read_bytes())
        output.with_suffix('.signature.txt').write_text(result.stdout)
        return {'signed':True,'install_over_g2_5':'certificate-compatible; actual device install still untested',
                'status':'signed-with-original-certificate','signer_sha256':expected,
                'apk_sha256':digest(output.read_bytes())}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--unsigned',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sdk',type=Path,required=True)
    a=p.parse_args()
    # A signature must never approve a file other than the just-verified candidate.
    report=json.loads(a.unsigned.with_suffix('.verification.json').read_text())
    if report['candidate_apk_sha256']!=digest(a.unsigned.read_bytes()) or report['candidate']!=6:
        raise ValueError('Unsigned APK is not the verified Candidate 6')
    result=sign(a.unsigned.resolve(),a.output.resolve(),a.sdk.resolve(),spec()['signer_sha256'],dict(os.environ))
    a.output.with_suffix('.signing-status.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not result['signed']:
        print('::warning::Candidate 6 built and verified, but is UNSIGNED. Keep installed #5; no throwaway key created.')

if __name__=='__main__':main()
