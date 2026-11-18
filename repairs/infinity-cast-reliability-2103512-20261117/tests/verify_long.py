"""Long timeline + sustained-byte-rate tests, preserving real coded packets."""
from pathlib import Path
p=Path(__file__).with_name('verify_stream.py');ns={'__file__':str(p)};exec(compile(p.read_text().split('source=mem')[0],str(p),'exec'),ns);globals().update({k:v for k,v in ns.items() if not k.startswith('__')})
fixtures=[('long_hevc_eac3',str(ROOT/'repairs/infinity-cast-dual-failure-2103510-20261117/fixtures/inband-main-eac3.mkv'),299,1,[0,1,2,3,4,5,6,7,8,9,10,11,895,1797,1798,1799,895]),('sustained_high_rate',None,4,2,list(range(15)))]
report={'scope':'Real coded HEVC/EAC3 one-hour timeline and H264/EAC3 high-byte-rate two-minute timeline; source bitrate/raster are disclosed, no physical4Khardware qualification','fixtures':[]}
for label,path,repeats,stride,indices in fixtures:
 original=None
 if path is None:original=mem(gzip.open('/dev/shm/cast508-reader/high.mkv.gz','rb').read());path=fdpath(original)
 source=mem();args=['ffmpeg','-nostdin','-v','error','-y','-stream_loop',str(repeats),'-i',path];args+=['-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','120','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','eac3','-b:a','640k'] if path.startswith('/proc/') else ['-map','0:v:0','-map','0:a:0','-c','copy'];command(args+['-f','matroska',fdpath(source)])
 info=json.loads(command(['ffprobe','-v','error','-show_entries','format=duration,size','-of','json',fdpath(source)]))['format'];row={'name':label,'duration_seconds':float(info['duration']),'bytes':int(info['size']),'source_sha256':hashlib.sha256(contents(source)).hexdigest(),'fragments':[]};elapsed=0;span=0;digests={}
 for index in indices:
  out,init=mem(),mem();entered=time.monotonic();r=json.loads(command(['/tmp/cast512-stream-native',fdpath(source),fdpath(out),str(stride),str(index),fdpath(init)],text=True));used=time.monotonic()-entered
  media=contents(out);full=mem(contents(init)+media);vs=packets(full,'v:0');aud=packets(full,'a:0');assert vs and aud
  assert all(float(vs[n]['dts_time'])<float(vs[n+1]['dts_time']) for n in range(len(vs)-1));assert all(float(aud[n]['dts_time'])<float(aud[n+1]['dts_time']) for n in range(len(aud)-1))
  command(['ffmpeg','-v','error','-xerror','-err_detect','explode','-i',fdpath(full),'-f','null','-'])
  digest=hashlib.sha256(media).hexdigest();assert index not in digests or digests[index]==digest;digests[index]=digest
  assert r['source_bytes']<=r['budget']<=134217728 and r['largest_chunk']<=65536
  r.update(elapsed_host_seconds=round(used,3),strict_decode=True,sha256=digest);row['fragments'].append(r);elapsed+=used
  for fd in [out,init,full]:os.close(fd)
 row['host_generation_seconds']=round(elapsed,3);report['fixtures'].append(row);os.close(source)
 if original is not None:os.close(original)
report['status']='PASS_LONG_TIMELINE_SUSTAINED_BYTE_RATE_SEEK_AND_COMPLETE_MEDIA';(H/'HOST-LONG.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:([{'name':x['name'],'duration':x['duration_seconds'],'fragments':len(x['fragments'])} for x in v] if k=='fixtures' else v)for k,v in report.items()}))
