"""CI-only Android output proof: exact packet bytes and source clock, no relaxed tolerance."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast/run_probe.py'
error=None
try:exec(compile(prior.read_text(),str(prior),'exec'),{'__file__':str(prior),'__name__':'__main__'})
except BaseException as failure:error=failure
out=Path(sys.argv[1]);target=out/'mkv-remux.mp4'
subprocess.run(['adb','pull','/sdcard/Android/data/com.projectinfinity.castqa/files/mkv-remux.mp4',str(target)],check=False)
report_path=out/'ANDROID-CAST-COMPONENT.json';report=json.loads(report_path.read_text());report['scope']='Actual original94 ARM64 FFmpeg via Cast JNI, private authenticated relay, every output packet timing/quality, compatible Android HLS playback/seek and cancellation. Separate CI package only.'
try:
 def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-show_packets','-show_data_hash','sha256','-of','json',str(p)]))
 source=probe(ROOT/'cast-sdk-work/mkv/h264-aac.mkv');actual=probe(target);evidence={}
 source_origin=float(source['format']['start_time']);output_origin=float(actual['format']['start_time'])
 for kind in ['video','audio']:
  a_index=next(s['index'] for s in source['streams'] if s['codec_type']==kind);b_index=next(s['index'] for s in actual['streams'] if s['codec_type']==kind)
  a=[p for p in source['packets'] if p['stream_index']==a_index];b=[p for p in actual['packets'] if p['stream_index']==b_index]
  assert [p['data_hash'] for p in a]==[p['data_hash'] for p in b],kind+' Android encoded packets changed'
  delta=max(abs(float(x['pts_time'])-source_origin-(float(y['pts_time'])-output_origin)) for x,y in zip(a,b))
  assert delta<0.002,kind+' Android source-clock error: '+str(delta)
  evidence[kind]=dict(packets=len(a),encoded_bytes_identical=True,max_source_pts_error_seconds=delta)
 report['actual_Android_output_packet_proof']=evidence;report['exact_packet_quality_timing']=True
except BaseException as failure:
 report['pass']=False;report['exact_packet_quality_timing']=False;report['packet_proof_failure']=str(failure)
 if error is None:error=failure
finally:report_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if error is not None:raise error
assert report['pass']
