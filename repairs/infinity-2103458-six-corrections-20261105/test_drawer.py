"""Exact drawer-only scope; baseline supplied independently by signed source."""
import os,re,subprocess,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
NAME='repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml'
BEFORE=subprocess.check_output(['git','show','b740fc6f:'+NAME],cwd=ROOT).decode()
AFTER=Path(os.environ.get('NAV_SOURCE',str(ROOT/NAME))).read_text()
def omit(s):
    for id in ('1198112','1198114'):
        anchor=s.index('<control type="button" id="'+id+'">')
        start=s.rfind('        <control type="group">',0,anchor)
        end=s.index('        <control type="group">',start+1)
        s=s[:start]+s[end:]
    return s
class Drawer(unittest.TestCase):
    def test_only_two_complete_groups_removed(self):self.assertEqual(AFTER,omit(BEFORE))
    def test_no_removed_id_or_label_survives(self):
        for value in ('1198112','1198114','<label>Browse Files</label>','<label>Media Sources</label>'):self.assertNotIn(value,AFTER)
    def test_all_remaining_controls_and_actions_identical(self):
        old=ET.fromstring(omit(BEFORE));new=ET.fromstring(AFTER)
        self.assertEqual(ET.tostring(new),ET.tostring(old))
    def test_direct_library_paths_preserved(self):
        root=ET.fromstring(AFTER)
        for id,path in [('1198104','movies'),('1198111','tvshows')]:
            row=root.find('.//control[@id="'+id+'"]')
            self.assertEqual([n.text for n in row.findall('onclick')],['Dialog.Close(1198)','ActivateWindow(Videos,videodb://'+path+'/titles/,return)'])
if __name__=='__main__':unittest.main(verbosity=2)
