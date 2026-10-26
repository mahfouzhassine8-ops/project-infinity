"""Exact local QA bitmap paint on the actual Android surface, not a placeholder."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time
import zlib

COLOURS=((17,203,91),(237,49,174),(44,97,233),(243,176,33))
NAME='infinity-qa-poster.png'
URI='special://profile/'+NAME


def png(width=200,height=300,order=(0,1,2,3)):
    def chunk(kind,raw):
        return struct.pack('!I',len(raw))+kind+raw+struct.pack('!I',zlib.crc32(kind+raw)&0xffffffff)
    rows=[]
    for y in range(height):
        row=bytearray()
        for x in range(width):row.extend(COLOURS[order[(2 if y>=height//2 else 0)+(1 if x>=width//2 else 0)]])
        rows.append(b'\x00'+row)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows),9))+chunk(b'IEND',b'')


def stage(device,args,state):
    target=device.PROFILE+'/'+NAME
    device.shell('test','!','-e',target);device.shell('test','!','-L',target)
    local=args.out/NAME
    with local.open('xb') as f:f.write(png())
    device.adb('push',local,target)
    raw=device.adb('exec-out','cat',target,binary=True)
    if not isinstance(raw,bytes) or raw!=local.read_bytes():raise ValueError('Actual cached poster readback differs')
    for row in state['items'].values():row['poster']=URI
    return dict(source=URI,sha256=hashlib.sha256(raw).hexdigest(),width=200,height=300,
                synthetic_QA_bitmap=True,actual_remote_artwork=False,before_first_launch=True,readback_matches=True)


def inspect(raw,timeout=10):
    if not isinstance(raw,bytes) or raw[:8]!=b'\x89PNG\r\n\x1a\n' or raw[12:16]!=b'IHDR':
        raise ValueError('Actual Android PNG required')
    width,height=struct.unpack('!II',raw[16:24])
    if not 16<=width<=8192 or not 16<=height<=8192 or width*height>16*1024*1024:
        raise ValueError('Unexpected screenshot geometry')
    decoded=subprocess.run(['ffmpeg','-v','error','-f','image2pipe','-i','pipe:0',
        '-f','rawvideo','-pix_fmt','rgb24','pipe:1'],input=raw,capture_output=True,timeout=timeout,check=True).stdout
    if len(decoded)!=width*height*3:raise ValueError('Actual screenshot decode differs')
    channels=[decoded[i::3] for i in range(3)]
    pixel_step=max(1,(width*height)//262144)
    regions=[]
    for colour in COLOURS:
        masks=[int.from_bytes(channel.translate(bytes(int(abs(v-wanted)<=8) for v in range(256))),'little')
               for channel,wanted in zip(channels,colour)]
        mask=(masks[0]&masks[1]&masks[2]).to_bytes(width*height,'little')
        count=mask.count(b'\x01')
        if count<64:return None
        sampled=mask[::pixel_step];at=-1;samples=total_x=total_y=0;left=width;right=-1;top=height;bottom=-1
        while True:
            at=sampled.find(b'\x01',at+1)
            if at<0:break
            pixel=at*pixel_step;x=pixel%width;y=pixel//width
            samples+=1;total_x+=x;total_y+=y;left=min(left,x);right=max(right,x);top=min(top,y);bottom=max(bottom,y)
        if samples<4:return None
        regions.append(dict(colour=list(colour),pixels=count,sampled_pixels=samples,
            x=total_x/samples,y=total_y/samples,bounds=[left,top,right,bottom]))
    a,b,c,d=regions
    if not (a['x']<b['x'] and c['x']<d['x'] and a['y']<c['y'] and b['y']<d['y']):return None
    span_x=max(r['bounds'][2] for r in regions)-min(r['bounds'][0] for r in regions)
    span_y=max(r['bounds'][3] for r in regions)-min(r['bounds'][1] for r in regions)
    if (span_x<16 or span_y<16 or abs(a['x']-c['x'])>span_x*.25 or abs(b['x']-d['x'])>span_x*.25 or
            abs(a['y']-b['y'])>span_y*.25 or abs(c['y']-d['y'])>span_y*.25):return None
    return dict(width=width,height=height,regions=regions,sample_stride=pixel_step,actual_surface_bitmap_verified=True)


def observe(device,out,began,deadline):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    sample=0;raw=None
    while time.monotonic()<deadline:
        sample+=1
        raw=device.adb('exec-out','screencap','-p',binary=True)
        captured=time.monotonic()
        remaining=deadline-captured
        if remaining<=0:break
        try:value=inspect(raw,timeout=min(10,remaining))
        except Exception:
            (out/'last-unmatched-poster-surface.png').write_bytes(raw)
            raise
        if value:
            if time.monotonic()>deadline:break
            (out/'cached-poster-surface.png').write_bytes(raw)
            value.update(first_observed_poster_capture_ms=(captured-began)*1000,
                paint_verification_finished_ms=(time.monotonic()-began)*1000,samples=sample,
                observation='Actual cached synthetic bitmap on Android surface; conservative captured upper bound, not GPU first-paint timestamp')
            (out/'CACHED-POSTER-PAINT.json').write_text(json.dumps(value,indent=2)+'\n')
            return value
        time.sleep(.1)
    if isinstance(raw,bytes):(out/'last-unmatched-poster-surface.png').write_bytes(raw)
    raise AssertionError('Actual cached poster paint not observed within original20sec saved-card deadline')
