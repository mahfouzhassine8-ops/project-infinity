"""Positive and negative tests for the actual approved unified Rotate/Repeat mapping."""
import importlib.util
from pathlib import Path
import unittest

modpath=Path(__file__).with_name('player_rotate_226.py')
spec=importlib.util.spec_from_file_location('rotate_repair',modpath)
rotate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(rotate)

def fixture():
    return ('''<window><controls>
      <control type="button" id="255"><onright>265</onright></control>
      <control type="label"><label>$VAR[InfinityPlayerRepeatLabel]</label><visible>Control.HasFocus(265)</visible></control>
        <control type="group">
          <width>96</width><height>96</height>
          <control type="button" id="265">
            <description>$VAR[InfinityPlayerRepeatLabel]</description>
            <onleft>255</onleft><onright>262</onright>
            <enable>!Skin.HasSetting(Infinity.PlayerDrawerOpen)</enable>
            <onclick>PlayerControl(Repeat)</onclick>
          </control>
          <control type="image"><texture colordiffuse="$VAR[InfinityGlassTextSecondary]">osd_modern/osdrepeat.png</texture><visible>!Playlist.IsRepeatOne + !Playlist.IsRepeat</visible></control>
          <control type="image"><texture colordiffuse="$VAR[InfinityGlassFocus]">osd_modern/osdrepeatone.png</texture><visible>Playlist.IsRepeatOne</visible></control>
          <control type="image"><texture>osd_modern/osdrepeatall.png</texture></control>
        </control>
        <control type="group"><control type="button" id="262"><onleft>265</onleft></control></control>
      </controls></window>''').encode()

class RotateSource(unittest.TestCase):
    def test_replaces_repeat_with_native_rotate_and_focus_routes(self):
        fixed=rotate.patch_osd(fixture()).decode()
        for token in ('PLAYER_ROTATION_UNLOCKED','PLAYER_ROTATION_FOLLOW_DEVICE',
                      'Skin.ToggleSetting(Infinity.PlayerRotationUnlocked)',
                      '<onright>263</onright>','<onleft>263</onleft>',
                      'infinity_reference/rotate.png'):
            self.assertIn(token,fixed)
        self.assertNotIn('PlayerControl(Repeat)',fixed)
        self.assertNotIn('id="265"',fixed)
    def test_rejects_unexpected_preimage(self):
        with self.assertRaises(AssertionError):
            rotate.patch_osd(fixture().replace(b'id="265"',b'id="264"'))
if __name__=='__main__':
    unittest.main(verbosity=2)
