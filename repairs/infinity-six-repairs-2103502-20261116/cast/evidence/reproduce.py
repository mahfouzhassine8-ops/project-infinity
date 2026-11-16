import pathlib as P,hashlib as H,json,os,subprocess as S,zipfile,urllib.request,re,struct
W=P.Path('/dev/shm/infinity502-cast-ptl-repro'); R=P.Path('/workspace/infinity-cast96-root-cause'); F=P.Path('/dev/shm/infinity-cast-mkv-local'); J='/usr/lib/jvm/java-21-openjdk-amd64/bin/java'
def sha(p):return H.sha256(P.Path(p).read_bytes()).hexdigest()
def run(args,**kw):
 p=S.run(list(map(str,args)),capture_output=True,text=True,**kw);(W/'commands.log').open('a').write(json.dumps(list(map(str,args)))+'\n'+p.stdout+'\n'+p.stderr+'\n');p.check_returncode();return p.stdout
native=R/'repairs/infinity-cast-mkv-2103494-20261113/native/InfinityCastRemux.cpp'
receipt=P.Path('/dev/shm/cast498-hls-43630707565/cast-hls-native/CAST-HLS-NATIVE.json'); binding=json.loads(receipt.read_text()); expected=binding['source_hashes'][str(native.relative_to(R))];assert sha(native)==expected=='8d6db252f299f2da738e8842046c6082a4e3294b2defc992c1ba9f3247ef403d'
apk=P.Path('/dev/shm/infinity500-signed-502/Infinity-2103502-Combined-Original-Signer.apk')
with zipfile.ZipFile(apk) as z:libhash=H.sha256(z.read('lib/arm64-v8a/libinfinitycastremux.so')).hexdigest()
assert libhash==binding['new_library_sha256']=='613907f98b2a180f372413c70e2369d52872fcc9dc04385583c1c6515f28d53a'
sourceDir=R/'repairs/infinity-movies-continue-cast-2103486-20261112/cast/java/com/projectinfinity/kodi'
assert sha(sourceDir/'InfinityCastRemux.java')=='9e9d132d1fb0bb457e49b711ee77a624e1862b63499027f7316d2bf62518c623'
# Exact source included; harness limits output to first fragment required by master generation.
driver=(native.parent.parent/'tests/native_driver.cpp').read_text().replace('#include "../native/InfinityCastRemux.cpp"','#include "'+str(native)+'"')
start=driver.index(' for(size_t n=0;n<s.keys.size();n++)');end=driver.index('\n std::cout',start)
driver=driver[:start]+' save(out/"seg0.m4s",s.segment(0));'+driver[end:]
(W/'driver.cpp').write_text(driver)
run(['g++','-std=c++17','-O2','-Wno-deprecated-declarations','-I'+str(F/'ffmpeg-6.0.1'),'-I'+str(F/'host-ffmpeg'),W/'driver.cpp','-ldl','-o',W/'driver'])
control=W/'control.mkv';mutant=W/'ptl01.mkv'
run(['ffmpeg','-v','error','-i',F/'fixtures/hevc-eac3_6ch.mkv','-map','0:v:0','-map','0:a:0','-c','copy','-write_crc32','0',control])
# Read known hvcC payload from retained output; find the same exact bytes in copied MKV.
b=(F/'hevc-eac3_6ch-contract/init.mp4').read_bytes();i=b.index(b'hvcC');size=int.from_bytes(b[i-4:i],'big');hvcc=b[i+4:i-4+size];assert hvcc[0]==1 and hvcc[1]&31==1 and hvcc[12]==30
raw=control.read_bytes();assert raw.count(hvcc)==1;at=raw.index(hvcc);changed=bytearray(raw);changed[at+1]&=0xe0;changed[at+12]=1;mutant.write_bytes(changed)
diffs=[i for i,(a,b) in enumerate(zip(raw,changed)) if a!=b];assert diffs==[at+1,at+12]
# All hvcC NAL arrays (from byte23 onward) remain bit-identical, as does the entire rest of MKV, including cues.
assert raw[at+23:at+len(hvcc)]==changed[at+23:at+len(hvcc)]
env=dict(os.environ,LD_LIBRARY_PATH=':'.join(str(F/'host-ffmpeg'/x) for x in ['libavformat','libavcodec','libavutil']))
rows=[]
for name,p in [('control',control),('ptl01',mutant)]:
 out=W/name;run([W/'driver',p,out],env=env)
 probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_packets','-show_data_hash','sha256','-of','json',p]));(out/'probe.json').write_text(json.dumps(probe,indent=2))
 init=(out/'init.mp4').read_bytes();n=init.index(b'hvcC');l=int.from_bytes(init[n-4:n],'big');got=init[n+4:n-4+l]
 assert got==bytes(changed[at:at+len(hvcc)]) if name=='ptl01' else got==hvcc
 rows.append(dict(name=name,fixture_sha256=sha(p),inspection=json.loads((out/'inspection.json').read_text()),hvcC_profile=got[1]&31,hvcC_level=got[12],hvcC_sha256=H.sha256(got).hexdigest(),init_sha256=sha(out/'init.mp4'),first_fragment_sha256=sha(out/'seg0.m4s'),parsed_streams=[{k:x.get(k) for k in ['codec_name','profile','level','codec_type']} for x in probe['streams']]))
a=json.loads((W/'control/probe.json').read_text());b=json.loads((W/'ptl01/probe.json').read_text());assert a['packets']==b['packets'];assert (W/'control/seg0.m4s').read_bytes()==(W/'ptl01/seg0.m4s').read_bytes();assert rows[0]['inspection']['starts_us']==rows[1]['inspection']['starts_us']
assert rows[0]['inspection']['codecs']=='hev1.1.6.L30.90,ec-3';assert rows[1]['inspection']['codecs']=='hev1.0.6.L1.90,ec-3'
report=dict(status='NATIVE_REPRODUCED',native_source_sha256=sha(native),artifact_receipt_sha256=sha(receipt),exact502_native_library_sha256=libhash,synthetic_only=True,actual_phone_VPS_SPS='UNAVAILABLE',fixture_diff_offsets=diffs,fixture_diff_bytes=[dict(offset=i,before=raw[i],after=changed[i]) for i in diffs],NAL_arrays_identical=True,all_other_MKV_bytes_including_cues_identical=True,all_packets_with_hashes_timestamps_positions_identical=True,first_fragments_identical=True,rows=rows,host_libraries={x:sha(F/'host-ffmpeg'/x/y) for x,y in [('libavformat','libavformat.so.60'),('libavcodec','libavcodec.so.60'),('libavutil','libavutil.so.58')]},tools={p:sha(p) for p in ['/usr/bin/ffmpeg','/usr/bin/ffprobe','/usr/bin/g++',J]},driver_sha256=sha(W/'driver'),driver_source_sha256=sha(W/'driver.cpp'))
(W/'NATIVE-RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
