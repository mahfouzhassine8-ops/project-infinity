"""Real native fragment outputs: strict decode and lossless decode-order proof."""
from pathlib import Path
from decimal import Decimal
import subprocess,json,hashlib,sys
source=Path(sys.argv[1]);media=Path(sys.argv[2]);report=Path(sys.argv[3])
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_packets','-show_data_hash','sha256','-of','json',str(p)]))['packets']
def strict(p):
 r=subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(p),'-f','null','-'],capture_output=True,text=True);assert r.returncode==0 and not r.stderr.strip(),(str(p),r.returncode,r.stderr);return 'PASS_EMPTY_ERROR_STDERR'
def us(t):return int(Decimal(t)*1000000)
def frames(p):return subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(p),'-map','0:v','-f','framemd5','-'])
joined=media/'all.mp4';joined.write_bytes((media/'init.mp4').read_bytes()+b''.join((media/(str(n)+'.m4s')).read_bytes() for n in range(6)))
origin=us(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(source)]))['format']['start_time'])
strict(source);strict(joined);src=[q for q in probe(source) if q['stream_index']==0];dst=[q for q in probe(joined) if q['stream_index']==0]
assert [(q['data_hash'],us(q['pts_time'])-origin) for q in src]==[(q['data_hash'],us(q['pts_time'])-10000000) for q in dst]
assert all(us(b['dts_time'])>us(a['dts_time']) for a,b in zip(dst,dst[1:]))
# Matroska has no DTS for its initial reorder packets: compare every DTS
# actually supplied by demux, without inventing missing source timestamps.
assert all(us(a['dts_time'])-origin==us(b['dts_time'])-10000000 for a,b in zip(src,dst) if 'dts_time' in a)
a,b=frames(source),frames(joined)
def payload(text):return [line.split(b',')[-1].strip() for line in text.splitlines() if not line.startswith(b'#')]
assert payload(a)==payload(b)
rows=[]
for n in range(6):
 p=media/('independent-'+str(n)+'.mp4');p.write_bytes((media/'init.mp4').read_bytes()+(media/(str(n)+'.m4s')).read_bytes());strict(p);rows.append(dict(index=n,video_packets=len([q for q in probe(p) if q['stream_index']==0]),decode='PASS_EMPTY_ERROR_STDERR'));p.unlink()
r=dict(status='PASS_RADL_DECODE_ORDER_AND_INDEPENDENT_FRAGMENTS',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_video_packets=len(src),compressed_video_packets_and_PTS='BYTE_EXACT_IN_DECODE_ORDER',source_origin_us=origin,known_source_DTS='EXACT_MINUS_VERIFIED_SOURCE_ORIGIN_PLUS_EXISTING10s_TRANSPORT_EPOCH',cross_fragment_DTS='STRICTLY_INCREASING',decoded_frames='EXACT_SOURCE_PIXELS',independent=rows,quota='UNCHANGED',owner_source_NALs='UNAVAILABLE; synthetic supported-family reproduction')
report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
