"""Synthetic AIO API/media on the host; no provider code or account changes."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import subprocess
import threading
from urllib.parse import urlsplit, parse_qs


def generate_clip(path):
    path = Path(path)
    subprocess.run(['ffmpeg','-nostdin','-y','-f','lavfi','-i','color=c=darkblue:s=320x180:r=24',
                    '-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','210',
                    '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-b:v','80k',
                    '-c:a','aac','-b:a','32k','-movflags','+faststart',str(path)], check=True, capture_output=True, timeout=180)


def result(base):
    return {'data': {'errors': [], 'results': [dict(type='http',url=base+'/fixture.mp4',requestHeaders={},
        filename='Infinity.Synthetic.Fixture.720p.WEB-DL.h264.mp4',size=1048576,cached=True,library=False,
        addon='Infinity fixture',service='direct',parsedFile=dict(seasonPack=False,quality='WEB-DL',
        resolution='720p',network='',encode='h264',visualTags=[],subtitles=[],audioTags=[],audioChannels=['2.0'],languages=[]))]}}


def start(clip, port, log):
    clip, log = Path(clip), Path(log)
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            with lock:
                with log.open('a') as stream: stream.write(json.dumps(dict(method=self.command,path=self.path,message=fmt % args))+'\n')
        def do_HEAD(self): self.respond(False)
        def do_GET(self): self.respond(True)
        def respond(self, body):
            url=urlsplit(self.path)
            if url.path == '/api/v1/search':
                expected='Basic '+base64.b64encode(b'fixture:fixture').decode()
                params=parse_qs(url.query)
                if self.headers.get('Authorization') != expected or params.get('type') not in (['movie'],['series']):
                    self.send_error(401); return
                raw=json.dumps(result('http://10.0.2.2:'+str(port))).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers()
                if body:self.wfile.write(raw)
                return
            if url.path != '/fixture.mp4': self.send_error(404); return
            size=clip.stat().st_size; start,end=0,size-1
            header=self.headers.get('Range')
            if header:
                match=re.fullmatch(r'bytes=(\d+)-(\d*)',header)
                if not match:self.send_error(416);return
                start=int(match[1]);end=min(int(match[2]) if match[2] else end,end)
                if start> end:self.send_error(416);return
            self.send_response(206 if header else 200);self.send_header('Content-Type','video/mp4')
            self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
            if header:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            if body:
                try:
                    with clip.open('rb') as stream:
                        stream.seek(start);remaining=end-start+1
                        while remaining:
                            raw=stream.read(min(65536,remaining))
                            if not raw:break
                            self.wfile.write(raw);remaining-=len(raw)
                except (BrokenPipeError,ConnectionResetError):pass
    server=ThreadingHTTPServer(('0.0.0.0',port),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    return server


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--clip',type=Path,required=True);p.add_argument('--port',type=int,default=18766);p.add_argument('--log',type=Path,required=True)
    args=p.parse_args()
    if not args.clip.exists():generate_clip(args.clip)
    server=start(args.clip,args.port,args.log)
    try: threading.Event().wait()
    except KeyboardInterrupt:server.shutdown()
