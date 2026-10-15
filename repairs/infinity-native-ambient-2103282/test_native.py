"""Product-level synthetic frame/illumination checks, NOT Kodi/device acceptance."""
import ctypes as C
import io
import os
from pathlib import Path
import sys
import time
import unittest
from PIL import Image

LIB=Path(os.environ.get('AMBIENT_HOST_LIB','engine/libinfinityambient-host.so')).resolve()
OUT=Path(os.environ.get('AMBIENT_TEST_EVIDENCE','audit282/native'))

class NativeTests(unittest.TestCase):
    def setUp(self):
        self.lib=C.CDLL(str(LIB));self.lib.infinity_ambient_create.restype=C.c_void_p
        self.lib.infinity_ambient_destroy.argtypes=[C.c_void_p]
        self.lib.infinity_ambient_reset.argtypes=[C.c_void_p]
        self.lib.infinity_ambient_feed.argtypes=[C.c_void_p,C.c_void_p]+[C.c_int]*4
        self.lib.infinity_ambient_tile.argtypes=[C.c_void_p]+[C.c_float]*4+[C.c_int]*2+[C.c_float]*2+[C.POINTER(C.c_void_p)]
        self.lib.infinity_ambient_set_active(1);self.h=self.lib.infinity_ambient_create()
        self.assertTrue(self.h)
    def tearDown(self):self.lib.infinity_ambient_destroy(self.h)
    def feed(self,image,light=False):
        raw=image.convert('RGBA').tobytes('raw','BGRA');buffer=C.create_string_buffer(raw)
        result=self.lib.infinity_ambient_feed(self.h,buffer,len(raw),image.width,image.height,int(light))
        self.assertEqual(buffer.raw[:-1],raw,'capture bytes must never be changed')
        return result
    def tile(self,rect=(0,0,1,1),size=(144,96),radius=0,lip=0):
        ptr=C.c_void_p();n=self.lib.infinity_ambient_tile(self.h,*rect,*size,radius,lip,C.byref(ptr))
        return Image.open(io.BytesIO(C.string_at(ptr,n))).convert('RGBA') if n else None
    def split(self):
        im=Image.new('RGB',(144,96),'blue');im.paste('orange',(72,0,144,96));return im
    def test_direction_and_visible_transmission(self):
        self.assertEqual(self.feed(self.split()),1);tile=self.tile()
        left,right=tile.getpixel((12,48)),tile.getpixel((132,48))
        self.assertGreater(left[2],left[0]+120);self.assertGreater(right[0],right[2]+120)
        self.assertGreaterEqual(left[3],80);self.assertLessEqual(left[3],105)
        OUT.mkdir(parents=True,exist_ok=True);tile.save(OUT/'directional-field-synthetic-not-device.png')
    def test_center_scene_is_not_global_dominant_tint(self):
        im=self.split();im.paste('lime',(8,8,136,88));self.feed(im)
        self.assertGreater(self.tile().getpixel((5,48))[2],180)
        self.assertGreater(self.tile().getpixel((139,48))[0],180)
    def test_top_bottom_are_distinct(self):
        im=Image.new('RGB',(144,96),'blue');im.paste('red',(0,48,144,96));self.feed(im)
        t=self.tile();self.assertGreater(t.getpixel((72,4))[2],200);self.assertGreater(t.getpixel((72,92))[0],200)
    def test_scene_change_smooths_then_converges(self):
        self.feed(Image.new('RGB',(144,96),'blue'));self.feed(Image.new('RGB',(144,96),'red'))
        t=self.tile().getpixel((72,48));self.assertGreater(t[0],40);self.assertGreater(t[2],40)
        for _ in range(20):self.feed(Image.new('RGB',(144,96),'red'))
        t=self.tile().getpixel((72,48));self.assertGreater(t[0],245);self.assertLess(t[2],5)
    def test_new_session_does_not_reuse_prior_colors(self):
        self.feed(self.split());self.lib.infinity_ambient_reset(self.h)
        self.assertIsNone(self.tile());self.assertEqual(self.feed(Image.new('RGB',(144,96),'black')),0)
        self.assertIsNone(self.tile());self.feed(Image.new('RGB',(144,96),'lime'))
        t=self.tile().getpixel((72,48));self.assertGreater(t[1],245);self.assertLess(t[2],5)
    def test_real_dark_scene_returns_to_oled(self):
        self.feed(self.split())
        for _ in range(30):self.feed(Image.new('RGB',(144,96),'black'))
        self.assertEqual(self.tile().getpixel((72,48))[3],0)
    def test_light_transmission_is_lower_and_neutral_highlights_do_not_wash(self):
        self.feed(self.split(),False);dark=self.tile().getpixel((12,48))[3]
        self.feed(self.split(),True);light=self.tile().getpixel((12,48))[3]
        self.assertLess(light,dark);self.assertGreater(light,40)
        self.lib.infinity_ambient_reset(self.h);self.assertEqual(self.feed(Image.new('RGB',(144,96),'white'),True),0)
    def test_glass_rim_stronger_than_face_and_corners_masked(self):
        self.feed(Image.new('RGB',(144,96),'red'));tile=self.tile(radius=12,lip=1.5)
        self.assertEqual(tile.getpixel((0,0))[3],0)
        self.assertGreater(tile.getpixel((72,0))[3],tile.getpixel((72,48))[3]+100)
    def test_pause_without_feed_preserves_exact_field(self):
        self.feed(self.split());a=self.tile().tobytes();time.sleep(.01)
        self.assertEqual(self.tile().tobytes(),a)
    def test_background_gate_rejects_capture_and_output(self):
        self.feed(self.split());self.lib.infinity_ambient_set_active(0)
        self.assertIsNone(self.tile());self.assertEqual(self.feed(self.split()),0)
    def test_invalid_capture_and_geometry_fail_closed(self):
        self.assertEqual(self.feed(Image.new('RGB',(128,96),'red')),0)
        self.assertEqual(self.feed(Image.new('RGB',(144,200),'red')),0)
        self.feed(self.split());self.assertIsNone(self.tile((1,0,0,1)));self.assertIsNone(self.tile(size=(145,96)))
    def test_resize_uses_normalized_current_window(self):
        self.feed(self.split());left=self.tile((0,0,.25,1),size=(40,120));right=self.tile((.75,0,1,1),size=(120,40))
        self.assertGreater(left.getpixel((20,60))[2],200);self.assertGreater(right.getpixel((60,20))[0],200)
    def test_ram_texture_has_png_signature_and_releases(self):
        fd=self.lib.infinity_ambient_memfd();self.assertGreaterEqual(fd,0)
        try:
            self.feed(self.split());b=io.BytesIO();self.tile().save(b,format='PNG');os.write(fd,b.getvalue())
            with open('/proc/self/fd/%d'%fd,'rb') as f:self.assertEqual(f.read(8),b'\x89PNG\r\n\x1a\n')
        finally:os.close(fd)
    def test_bounded_workload_budget(self):
        im=self.split();start=time.perf_counter()
        for _ in range(30):
            self.feed(im)
            for rect in [(0,.2,.2,.8),(.7,.5,1,.9),(0,.9,1,1)]:self.tile(rect)
        elapsed=(time.perf_counter()-start)/30
        OUT.mkdir(parents=True,exist_ok=True);(OUT/'host-frame-seconds.txt').write_text(str(elapsed)+'\nHost CPU only; not Android playback profiling.\n')
        self.assertLess(elapsed,.083,'host rendering exceeds entire 12fps frame budget')

if __name__=='__main__':unittest.main()
