"""Import original authorized image bytes only after archive/SHA/format checks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile
from PIL import Image
import io

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'design-locks/infinity-media-browser-20261104'
NAMES=('01_APPROVED_LOCKED_INFINITY_BROWSER.png','02_ACTUAL_BROKEN_BROWSER_LIGHT_MODE.jpg')
SHA='6786b5cadb7153bb0036a651dcfba889a58f2a5acd79a759a798302e2d70c0ad'


def main():
    p=argparse.ArgumentParser();p.add_argument('--zip',type=Path,required=True);a=p.parse_args()
    records=[];images={}
    with ZipFile(a.zip) as archive:
        bad=archive.testzip()
        if bad is not None:raise ValueError('Original archive CRC failed')
        for name in NAMES:
            entries=[n for n in archive.namelist() if Path(n).name==name]
            if len(entries)!=1:raise ValueError('Missing or ambiguous original image: '+name)
            data=archive.read(entries[0]);digest=hashlib.sha256(data).hexdigest()
            with Image.open(io.BytesIO(data)) as image:
                fmt=image.format;size=list(image.size);image.verify()
            if name==NAMES[0]:
                if digest!=SHA or fmt!='PNG' or size!=[820,1918] or len(data)!=1547339:
                    raise ValueError('Approved PNG does not match the exact locked reference')
            elif fmt!='JPEG':raise ValueError('Actual rendering evidence is not a JPEG')
            images[name]=data
            records.append({'file':'reference/'+name,'archive_member':entries[0],
                            'sha256':digest,'bytes':len(data),'format':fmt,'size':size})
    lock=subprocess.run(['git','show','745b542a:design-locks/infinity-media-browser-20261104/APPROVED-MOCKUP-LOCK.md'],
                         cwd=ROOT,capture_output=True,check=True).stdout
    target=FOLDER/'reference';target.mkdir(parents=True,exist_ok=True)
    for name,data in images.items():
        dest=target/name
        if dest.exists() and dest.read_bytes()!=data:raise ValueError('Existing reference differs; refusing overwrite')
    # No image re-encoding, crop, resize or annotation.
    for name,data in images.items():(target/name).write_bytes(data)
    doc=FOLDER/'APPROVED-MOCKUP-LOCK.md'
    if doc.exists() and doc.read_bytes()!=lock:raise ValueError('Design-lock record differs; refusing overwrite')
    doc.write_bytes(lock)
    receipt={'status':'PASS_ORIGINAL_IMAGE_BYTES_CRC_SHA_AND_FORMAT','source':'user-authorized original evidence ZIP',
             'archive_sha256':hashlib.sha256(a.zip.read_bytes()).hexdigest(),'images':records,
             'design_acceptance':'LOCKED_REFERENCE_ONLY','implementation_visual_acceptance':'PENDING',
             'physical_Fold_acceptance':'PENDING','reencoded':False}
    (FOLDER/'ORIGINAL-IMAGE-PROVENANCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
