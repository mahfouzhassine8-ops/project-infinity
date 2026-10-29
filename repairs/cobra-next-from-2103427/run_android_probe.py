"""File entry point: emulator action executes each script line separately."""
import argparse,json
from pathlib import Path
from android_probe import probe

def main(signed,out,signature):
 files=list(signed.glob('Infinity-*-Combined-Original-Signer.apk'));assert len(files)==1
 receipt=json.loads((signed/'BUILD-RECEIPT.json').read_text());assert receipt['versionCode'] in (2103427,2103428,2103429,2103430)
 assert 'Signer #1 certificate SHA-256 digest: d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' in signature.read_text()
 probe(files[0],out,receipt['signed_apk_sha256'])
 if receipt['versionCode']==2103430:
  from icon.android_observe import observe
  observe(out.parent/'icon',receipt['signed_apk_sha256'],receipt['versionCode'])
  from android_button_journey import journey
  journey(out.parent/'functional')
 elif receipt['versionCode']>=2103428:
  from android_candidate_journey import journey
  journey(out.parent/'functional')
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('signed','out','signature'):p.add_argument('--'+n,type=Path,required=True)
 main(**vars(p.parse_args()))
