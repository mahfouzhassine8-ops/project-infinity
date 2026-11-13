"""Cast-only bridge, original94 API/ABI proof and pinned FFmpeg engineering tests.
No original engine rebuild, signer changes, production FFmpeg replacement or data.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,io,json,os,re,subprocess,sys,tarfile,urllib.request
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
WORK=Path(sys.argv[2]).resolve();WORK.mkdir(exist_ok=True)
BASE='fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c'
ENGINE='3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75'
PIN='945e34840092dc0fd3824eb1af2be79868af2afb4fe13159b19a9bcfc464cc4d53243c13ff065199290e9393ddbf4b1c5c8abccf83a31a31d6c7490e499fd1fc'
def run(args,**kw):subprocess.run(list(map(str,args)),check=True,**kw)
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def save(n,v): (WORK/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def sources():
 src=WORK/'ffmpeg-6.0.1'
 if not src.exists():
  raw=urllib.request.urlopen('https://ffmpeg.org/releases/ffmpeg-6.0.1.tar.gz',timeout=90).read();assert hashlib.sha512(raw).hexdigest()==PIN
  with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
   for item in t.getmembers():assert (item.name=='ffmpeg-6.0.1' or item.name.startswith('ffmpeg-6.0.1/')) and '..' not in Path(item.name).parts and not item.issym() and not item.islnk()
   t.extractall(WORK)
 return src
def native():
 apk=Path(sys.argv[3]).resolve();assert sha(apk)==BASE
 sdk=Path(os.environ['ANDROID_HOME']);ndk=sdk/'ndk/21.4.7075529';tool=ndk/'toolchains/llvm/prebuilt/linux-x86_64/bin';cc=tool/'aarch64-linux-android21-clang';cpp=tool/'aarch64-linux-android21-clang++'
 sig=subprocess.check_output([sdk/'build-tools/35.0.0/apksigner','verify','--verbose','--print-certs',apk],text=True)
 assert re.findall(r'certificate SHA-256 digest: ([a-f0-9]+)',sig)==['d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7']
 assert all(any(l.startswith('Verified using '+v+' scheme') and l.endswith(': true') for l in sig.splitlines()) for v in ('v1','v2','v3'))
 base=WORK/'base-native';base.mkdir(exist_ok=True)
 with ZipFile(apk) as z:
  for n in z.namelist():
   if n.startswith('lib/arm64-v8a/') and n.endswith('.so'):(base/Path(n).name).write_bytes(z.read(n))
 assert sha(base/'libkodi.so')==ENGINE
 table=subprocess.check_output([tool/'llvm-readelf','--dyn-syms','--wide',base/'libkodi.so'],text=True)
 names=re.findall(r'F\((av\w+)\)',next(l for l in (HERE/'native/InfinityCastRemux.cpp').read_text().splitlines() if l.startswith('#define FUNCTIONS')))
 assert all(re.search(r'\b'+n+r'$',table,re.M) for n in names), 'Existing94 must export every bound FFmpeg public API'
 src=sources();headers=WORK/'arm64-headers';headers.mkdir(exist_ok=True)
 run([src/'configure','--disable-all','--enable-avutil','--enable-avcodec','--enable-avformat','--disable-programs','--disable-doc','--disable-autodetect','--enable-cross-compile','--target-os=android','--arch=aarch64','--cc='+str(cc),'--cxx='+str(cpp),'--disable-x86asm'],cwd=headers)
 out=WORK/'native';out.mkdir(exist_ok=True);library=out/'libinfinitycastremux.so'
 run([cpp,'-std=c++17','-O2','-fPIC','-shared','-fvisibility=hidden','-Wall','-Wextra','-Wno-deprecated-declarations','-I'+str(src),'-I'+str(headers),HERE/'native/InfinityCastRemux.cpp','-ldl','-Wl,--no-undefined','-Wl,-z,max-page-size=16384','-o',library])
 elf=subprocess.check_output([tool/'llvm-readelf','-h','-d','--dyn-syms','--wide',library],text=True)
 assert 'AArch64' in elf and 'ELF64' in elf
 deps=set(re.findall(r'Shared library: \[([^\]]+)\]',elf));assert deps<={'libc.so','libm.so','libdl.so','libc++_shared.so'}
 exports=[]
 for line in elf.splitlines():
  f=line.split()
  if len(f)>=8 and f[4]=='GLOBAL' and f[5] in ['DEFAULT','PROTECTED'] and f[6]!='UND':exports.append(f[7])
 assert exports and all(n.startswith('Java_com_projectinfinity_kodi_InfinityCastRemuxNative_') for n in exports)
 save('CAST-MKV-NATIVE.json',dict(status='PASS_REAL_ARM64_BRIDGE_LINK_AND_EXACT94_EXISTING_FFMPEG_EXPORTS',baseline_APK_sha256=BASE,existing_engine_sha256=ENGINE,engine_changed=False,new_library_sha256=sha(library),exports=exports,dependencies=sorted(deps),required_FFmpeg_symbols=names,FFmpeg_source_sha512=PIN,source=os.environ['GITHUB_SHA'],source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'native/InfinityCastRemux.cpp',HERE/'build.py']},global_FFmpeg_callbacks_or_init_changed=False,existing_native_libraries_replaced=False))
 (WORK/'EXACT94-SIGNATURE.txt').write_text(sig)
def host():
 src=sources();build=WORK/'host-ffmpeg';build.mkdir(exist_ok=True)
 run([src/'configure','--disable-autodetect','--disable-everything','--enable-shared','--disable-static','--disable-programs','--disable-doc','--disable-x86asm','--enable-demuxer=matroska','--enable-muxer=mp4','--enable-protocol=file','--enable-parser=h264,hevc,aac,mpegaudio,ac3','--enable-decoder=h264,hevc,aac,mp3,ac3,eac3'],cwd=build)
 run(['make','-j4','libavformat/libavformat.so','libavcodec/libavcodec.so','libavutil/libavutil.so'],cwd=build)
 dirs=[build/n for n in ['libavformat','libavcodec','libavutil']];env=dict(os.environ,LD_LIBRARY_PATH=os.pathsep.join(map(str,dirs)))
 driver=WORK/'native-driver';run(['g++','-std=c++17','-O2','-Wno-deprecated-declarations','-I'+str(src),'-I'+str(build),HERE/'tests/native_driver.cpp','-ldl','-o',driver])
 run([sys.executable,HERE/'tests/test_native.py',WORK,driver],env=env)
if __name__=='__main__':{'native':native,'host':host}[sys.argv[1]]()
