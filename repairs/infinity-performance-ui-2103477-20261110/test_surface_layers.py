"""Focused attribution checks using the actual first-run Android layer format."""
import json
from pathlib import Path
import unittest

from surface_layers import candidates, corroborate

HERE = Path(__file__).parent
NAME = '486c52c SurfaceView[com.projectinfinity.kodi/com.projectinfinity.kodi.Main](BLAST)#250'
LAYER = dict(name=NAME, id=250, parent=249)


class SurfaceIdentityTests(unittest.TestCase):
    def test_actual_parent_background_and_buffer_list(self):
        self.assertEqual(candidates((HERE/'surface-layer-fixture.txt').read_text()), [LAYER])

    def test_plain_canonical_and_duplicate(self):
        self.assertEqual(candidates(NAME+'\n'+NAME), [dict(name=NAME,id=250,parent=None)])

    def test_two_buffers_remain_ambiguous(self):
        self.assertEqual(len(candidates(NAME+'\n'+NAME.replace('#250','#260'))),2)

    def test_wrong_component_or_background_or_malformed_is_rejected(self):
        for text in [NAME.replace('kodi.Main','kodi.CobraMain'), 'Background for '+NAME,
                     NAME.replace('(BLAST)',''), 'RequestedLayerState{'+NAME]:
            with self.subTest(text=text):
                self.assertEqual(candidates(text),[])

    def test_visible_buffer_and_matching_owner_required(self):
        raw='Layer [250] '+NAME+'\n  visible reason= buffer=22243635625993 frame=11\n ... (BLAST)#250 pid=5179 uid=10216\n'
        self.assertTrue(corroborate(raw,LAYER,5179)['confirmed'])
        self.assertFalse(corroborate(raw,LAYER,5180)['confirmed'])
        self.assertFalse(corroborate(raw.replace('visible reason=','hidden reason='),LAYER,5179)['confirmed'])
        self.assertFalse(corroborate(raw.replace('buffer=22243635625993','buffer=0'),LAYER,5179)['confirmed'])


if __name__ == '__main__':
    unittest.main()
