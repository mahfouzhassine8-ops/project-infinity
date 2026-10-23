"""Build the pinned Kodi libzip source for host reader execution only."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tarfile

PIN='fe94a26a2797dff7c9b27334f29982f8e523dd5095bf32ebcadc6443726864f0ff7b2e8bf243e52cad8f79297bc7a87d73fdbc35edae4ffc8ab6aa0bcc93b03e'

def run(tarballs,out):
    matches=[p for p in tarballs.rglob('libzip-1.8.0.tar.xz') if hashlib.sha512(p.read_bytes()).hexdigest()==PIN]
    if len(matches)!=1:raise RuntimeError('Exactly one pinned libzip 1.8.0 source archive required')
    if out.exists():raise RuntimeError('Fresh host reader build directory required')
    out.mkdir(parents=True)
    with tarfile.open(matches[0]) as archive:
        for m in archive.getmembers():
            if Path(m.name).is_absolute() or '..' in Path(m.name).parts or m.issym() or m.islnk():
                raise RuntimeError('Unexpected libzip archive member')
        archive.extractall(out)
    command=['cmake','-S',str(out/'libzip-1.8.0'),'-B',str(out/'build'),'-DBUILD_SHARED_LIBS=OFF']
    for flag in ('BUILD_TOOLS','BUILD_REGRESS','BUILD_EXAMPLES','BUILD_DOC','ENABLE_COMMONCRYPTO',
                 'ENABLE_GNUTLS','ENABLE_MBEDTLS','ENABLE_OPENSSL','ENABLE_BZIP2','ENABLE_LZMA','ENABLE_ZSTD'):
        command.append('-D'+flag+'=OFF')
    subprocess.run(command,check=True)
    subprocess.run(['cmake','--build',str(out/'build'),'--target','zip','-j','4'],check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('tarballs','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.tarballs,a.out)
