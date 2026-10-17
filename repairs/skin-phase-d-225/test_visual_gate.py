"""Fixture-independent unit tests for the native screenshot acceptance gate."""
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from visual_gate import inspect_png, inspect_session


def png(rgb=(0, 0, 0), width=96, height=96, filter_style=0):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag+data) & 0xffffffff)
    payload = b''
    sample = bytes((*rgb, 255)) * width
    prior = bytes(len(sample))
    for _ in range(height):
        if filter_style == 0:
            row = sample
        elif filter_style == 2:
            row = bytes((sample[i] - prior[i]) & 255 for i in range(len(sample)))
        else:
            raise ValueError('unsupported fixture row filter')
        payload += bytes([filter_style]) + row
        prior = sample
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',width,height,8,6,0,0,0)) + chunk(b'IDAT', zlib.compress(payload)) + chunk(b'IEND',b'')


class NativeScreenshotGate(unittest.TestCase):
    def test_true_black_is_failure_and_visible_dark_and_light_are_not(self):
        with tempfile.TemporaryDirectory() as directory:
            for rgb, expected in [((0,0,0),False),((3,7,12),False),((220,220,220),True),((0,60,200),True)]:
                f=Path(directory)/'test.png';f.write_bytes(png(rgb))
                self.assertEqual(inspect_png(f)['visibly_nonblank'],expected)

    def test_filtered_png_is_decoded_not_accepted_from_compressed_size(self):
        with tempfile.TemporaryDirectory() as directory:
            f=Path(directory)/'filtered.png'
            f.write_bytes(png((30,50,80),filter_style=2))
            self.assertTrue(inspect_png(f)['visibly_nonblank'])

    def test_corrupt_truncated_and_non_png_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            f=Path(directory)/'bad.png'
            for data in (b'no png',png()[:-9],png()[:-1],png().replace(b'IDAT',b'XDAT',1)):
                f.write_bytes(data)
                with self.assertRaises(ValueError):inspect_png(f)

    def test_exact_all_theme_screen_evidence_required(self):
        themes=('light','dark','oled')
        screens=('home','browse','settings','settings-category','command','health','system',
                 'navigation','audio','speed','display','palette','addons','select')
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);entries=[]
            for theme in themes:
                for screen in screens:
                    name=f'{theme}-{screen}'; (base/(name+'.png')).write_bytes(png((64,64,64)))
                    entries.append({'name':name,'screenshot':name+'.png'})
            self.assertTrue(inspect_session(base,{'screens':entries})['visual_evidence_passed'])
            (base/'light-settings.png').write_bytes(png())
            report=inspect_session(base,{'screens':entries})
            self.assertFalse(report['visual_evidence_passed'])
            self.assertIn('light-settings',report['failures'][0])
            entries.pop()
            self.assertFalse(inspect_session(base,{'screens':entries})['visual_evidence_passed'])


if __name__=='__main__':unittest.main()
