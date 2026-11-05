"""Transient visual binding and existing preference integration, no providers."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
H=Path(__file__).resolve().parent;R=H.parents[1]
P=R/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/script.infinity.commandcenter/media_view.py'
s=importlib.util.spec_from_file_location('candidate_genre_presentation',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
PREFIX='Infinity.MediaBrowser.'

class UI:
    def __init__(self):self.genre='Animation / Fantasy';self.props={};self.writes=[];self.visible=True;self.updating=False;self.after=None
    def getSkinDir(self):return 'skin.infinity.diggz'
    def getCurrentWindowId(self):return 10025
    def getCurrentWindowDialogId(self):return 9999
    def getCondVisibility(self,q):return self.visible if q=='Control.IsVisible(50)' else self.updating
    def getInfoLabel(self,q):
        assert q=='Container(50).ListItem.Genre';return self.genre
    def Window(self,n):assert n==10025;return self
    def getProperty(self,q):return self.props.get(q,'')
    def clearProperty(self,q):self.setProperty(q,'')
    def setProperty(self,q,v):
        assert q.startswith(PREFIX);self.props[q]=v;self.writes.append(q)
        if self.after:self.after(q)
        if self.props.get(PREFIX+'GenreSource')==self.genre and int(self.props.get(PREFIX+'GenreCount','0'))>0:
            self.assert_consistent()
    def assert_consistent(self):
        tags=[s.strip() for s in self.genre.split(' / ') if s.strip()]
        assert [self.props.get(PREFIX+'Genre%s'%i) for i in range(1,len(tags)+1)]==tags

class Presentation(unittest.TestCase):
    def test_tags_are_real_native_text_and_no_repeated_publication(self):
        u=UI();self.assertEqual(m.publish_browser_genres(u,u),'published');u.assert_consistent()
        self.assertEqual(u.props[PREFIX+'GenreCount'],'2');before=list(u.writes)
        self.assertEqual(m.publish_browser_genres(u,u),'unchanged');self.assertEqual(u.writes,before)
    def test_empty_and_longer_tag_sets_leave_complete_native_text_fallback(self):
        u=UI();m.publish_browser_genres(u,u)
        for text in ('','A / B / C / D / E','One custom-separated genre | another'):
            u.genre=text;m.publish_browser_genres(u,u)
            self.assertEqual(u.props[PREFIX+'GenreCount'],'0' if not text or ' / E' in text else '1')
            self.assertEqual(u.props[PREFIX+'GenreSource'],text)
    def test_selection_race_never_commits_wrong_tags(self):
        u=UI()
        def change(key):
            if key==PREFIX+'Genre2':u.genre='Drama'
        u.after=change;self.assertEqual(m.publish_browser_genres(u,u),'changed')
        self.assertEqual(u.props[PREFIX+'GenreCount'],'0');self.assertNotEqual(u.props.get(PREFIX+'GenreSource'),u.genre)
    def test_busy_or_other_view_does_not_publish(self):
        u=UI();u.updating=True;self.assertEqual(m.publish_browser_genres(u,u),'inactive')
        u.updating=False;u.visible=False;self.assertEqual(m.publish_browser_genres(u,u),'inactive');self.assertEqual(u.writes,[])
    def test_failure_does_not_block_the_existing_view_preference_observer(self):
        c=m.MediaViewPreference(None,None)
        with patch.object(m,'publish_browser_genres',side_effect=RuntimeError('fixture')),patch.object(c,'_observe',return_value='requested'):
            self.assertEqual(c.tick(),'requested')
    def test_all_preexisting_preference_methods_and_constants_are_unchanged(self):
        old=ast.parse(subprocess.check_output(['git','show','9471113e:'+str(P.relative_to(R))],cwd=R));new=ast.parse(P.read_bytes())
        def old_parts(tree):
            values=[]
            for n in tree.body:
                if isinstance(n,ast.FunctionDef) and n.name=='publish_browser_genres':continue
                if isinstance(n,ast.ClassDef) and n.name=='MediaViewPreference':
                    n.body=[x for x in n.body if not isinstance(x,ast.FunctionDef) or x.name!='tick']
                values.append(ast.dump(n,include_attributes=False))
            return values
        self.assertEqual(old_parts(old),old_parts(new))

if __name__=='__main__':unittest.main(verbosity=2)
