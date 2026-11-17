"""Selected host integration cases; consumes retained public synthetic fixtures."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
W=Path(sys.argv[1]).resolve();F=Path(sys.argv[2]).resolve();W.mkdir(exist_ok=True)
ENV=dict(os.environ,LD_LIBRARY_PATH=":".join(str(F/"host-ffmpeg"/p) for p in ("libavformat","libavcodec","libavutil","libswresample")))
log=W/"FINAL-COMMANDS.jsonl"
def run(args,**kw):
 start=time.monotonic();p=subprocess.run(list(map(str,args)),capture_output=True,text=True,env=ENV,**kw)
 with log.open("a") as f:f.write(json.dumps(dict(command=list(map(str,args)),exit=p.returncode,seconds=time.monotonic()-start,stdout=p.stdout,stderr=p.stderr))+"\n")
 return p
flags=["g++","-std=c++17","-Wno-deprecated-declarations","-I"+str(F/"ffmpeg-6.0.1"),"-I"+str(F/"host-ffmpeg")]
for name,source,extra in [("integrated-final","integrated_driver.cpp",["-O2"]),("audio-asan","audio_driver.cpp",["-O1","-g","-fsanitize=address,undefined","-fno-omit-frame-pointer"])]:
 if not (name=="audio-asan" and "--reuse-asan" in sys.argv):run(flags+extra+[HERE/source,"-ldl","-o",W/name]).check_returncode()
def probe(p):return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_packets","-show_data_hash","sha256","-of","json",str(p)]))
rows=[]
for name,source in [("aac-unchanged",F/"fixtures/h264-aac.mkv"),("integrated51-flags",W/"transients51.mkv"),("44100-odd-mp4",W/"44100-odd.mkv"),("delayed51-mp4",W/"delayed51.mkv"),("32000-mp4",W/"32000.mkv"),("lookahead-eof-mp4",W/"lookahead-eof.mkv"),("hevc-converted",Path("/dev/shm/infinity504-cast-matrix/main10-eac3.mkv"))]:
 out=W/name;run([W/"integrated-final",source,out]).check_returncode()
 chunks=sorted(out.glob("seg*.m4s"),key=lambda p:int(p.stem[3:]));target=out/"all.mp4";target.write_bytes((out/"init.mp4").read_bytes()+b"".join(p.read_bytes() for p in chunks))
 a,b=probe(source),probe(target);ap=[p for p in a["packets"] if p["stream_index"]==0];bp=[p for p in b["packets"] if p["stream_index"]==0]
 assert [p["data_hash"] for p in ap]==[p["data_hash"] for p in bp],name+" video packet mutation"
 meta=json.loads((out/"inspection.json").read_text());offset=10-meta["origin_us"]/1000000
 assert all(abs(float(x["pts_time"])+offset-float(y["pts_time"]))<.000002 for x,y in zip(ap,bp))
 if name!="aac-unchanged":assert all(abs(float(x["dts_time"])+offset-float(y["dts_time"]))<.000002 for x,y in zip(ap,bp) if "dts_time" in x)
 for stream in (0,1):
  packets=[p for p in b["packets"] if p["stream_index"]==stream];dts=[p.get("dts") for p in packets]
  assert all(p is not None for p in dts) and all(y>x for x,y in zip(dts,dts[1:])),name+" DTS"
 assert b["streams"][1]["codec_name"]=="aac"
 if name!="aac-unchanged":assert b["streams"][1]["channels"]==2 and all("K" in p["flags"] for p in b["packets"] if p["stream_index"]==1)
 if name=="aac-unchanged":
  old=Path("/dev/shm/infinity504-cast-matrix/h264-aac")
  for part in ("init.mp4","seg0.m4s"):assert (out/part).read_bytes()==(old/part).read_bytes(),"AAC baseline changed"
 rows.append(dict(case=name,video_packets=len(ap),video_packet_hashes_and_PTS_preserved=True,DTS=("baseline unchanged" if name=="aac-unchanged" else "available source DTS preserved"),strict_monotonic_DTS=True,codecs=meta["codecs"]))
for name in ("transients51","44100-odd","delayed51","lookahead-eof","32000"):
 run([W/"audio-asan",W/(name+".mkv"),W/(name+"-final.aac")]).check_returncode()
run([W/"audio-asan",W/"transients51.mkv",W/"cancel.aac","cancel"]).check_returncode()
negative=run([W/"integrated-final",F/"fixtures/hevc-changing-eac3.mkv",W/"reject-config-change"])
assert negative.returncode!=0 and "mkv_audio_configuration_changed" in negative.stderr,negative.stderr
sources=[R/"repairs/infinity-six-repairs-2103502-20261116/cast/native/InfinityCastRemux.cpp",HERE.parent/"native/CastAudioAdapter.h"]
# R is repairs/; bind the exact two production sources.
report=dict(status="PASS_SELECTED_CAST_AUDIO_HOST_INTEGRATION",cases=rows,ASAN_UBSAN="PASS_SELECTED_RANDOM_SEEK_AND_MID_CONVERSION_CANCELLATION",configuration_change="REFUSED_BEFORE_CONVERSION",source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},physical_TV="NOT_TESTED",Android="PENDING")
(W/"HOST-FINAL.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
