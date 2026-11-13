"""Selected source-container boundary probe, no receiver or owner source claim.
Compiles the actual frozen Cast source parser and tests genuine FFmpeg containers.
"""
from pathlib import Path
import hashlib,json,subprocess,tempfile
root=Path(__file__).resolve().parents[3]
source=root/'repairs/infinity-movies-continue-cast-2103486-20261112/cast/java/com/projectinfinity/kodi/InfinityCastSource.java'
def run(args):return subprocess.check_output([str(a) for a in args],stderr=subprocess.STDOUT,text=True)
with tempfile.TemporaryDirectory(prefix='infinity90-container-') as td:
 work=Path(td);out=work/'classes';out.mkdir()
 for name,codecs in [('actual-matroska.mkv',['-c:v','libx264','-c:a','aac']),('actual-webm.webm',['-c:v','libvpx-vp9','-c:a','libopus'])]:
  run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','testsrc2=size=64x64:rate=5','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1',*codecs,'-y',work/name])
 test=work/'ContainerProbe.java';test.write_text('''package com.projectinfinity.kodi;
import java.nio.file.*;import java.util.*;
public final class ContainerProbe {public static void main(String[] paths)throws Exception{
for(String path:paths){byte[] bytes=Files.readAllBytes(Paths.get(path));System.out.println(Paths.get(path).getFileName()+"="+InfinityCastSource.sniff(Arrays.copyOf(bytes,Math.min(8192,bytes.length)),"application/octet-stream",null));}
}}
''')
 run(['java','com.sun.tools.javac.Main','-d',out,source,test])
 names=['actual-matroska.mkv','actual-webm.webm'];results=dict(line.split('=',1) for line in run(['java','-cp',out,'com.projectinfinity.kodi.ContainerProbe',*[work/n for n in names]]).splitlines())
 probes={}
 for name in names:
  data=(work/name).read_bytes();assert (b'matroska' if name.endswith('.mkv') else b'webm') in data[:128]
  probes[name]=json.loads(run(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type:format=format_name','-of','json',work/name]))
 report=dict(schema=1,test='Actual production sniff against genuine FFmpeg Matroska and WebM',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),containers=probes,classifications=results,matroska_misclassified_as_webm=results['actual-matroska.mkv']=='video/webm',valid_webm_retained=results['actual-webm.webm']=='video/webm',owner_stream_container='UNKNOWN_FROM_VIDEO',real_receiver=False,production_modified=False)
 print(json.dumps(report,indent=2))
