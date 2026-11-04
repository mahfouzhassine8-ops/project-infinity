"""First-entry registration and preserved List variants; no native modifications."""
import copy
from functools import lru_cache
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE / 'overlay/assets/addons/skin.infinity.diggz/unified'
BASE = Path('/tmp/kodi453-ui-baseline/assets/addons/skin.infinity.diggz/unified')
MEDIA = ('movies','tvshows','seasons','episodes','sets','musicvideos')
NAMES = {'VideoList':50, 'SlimVideoList':50, 'InfinityCoreDirectory':65050,
         'InfinityPluginDirectoryRegular':65051, 'InfinityPluginDirectoryCompact':65052}
FAMILY = '[Control.IsVisible(50) | Control.IsVisible(65050) | Control.IsVisible(65051) | Control.IsVisible(65052)]'


@lru_cache(maxsize=8)
def read(path):return E.parse(path).getroot()


def predicate(text, content, plugin='', mode='auto', slim=False):
    for atom, value in {
        'String.IsEqual(Skin.String(Infinity.HomeView),cinema)':mode=='cinema',
        'String.IsEqual(Skin.String(Infinity.HomeView),compact)':mode=='compact',
        'Skin.HasSetting(Enable.SlimList)':slim,
        'String.IsEmpty(Container.PluginName)':not plugin,
    }.items():text = text.replace(atom, str(value))
    text = re.sub(r'Container.Content\(([^)]*)\)', lambda m: str(content == m[1]), text)
    text = text.replace('[','(').replace(']',')').replace('!',' not ').replace('+',' and ').replace('|',' or ')
    if re.sub(r'True|False|and|or|not|[()\s]', '', text):raise ValueError(text)
    return bool(eval(text, {'__builtins__':{}}, {}))


def available(initial, current, plugin='', mode='auto', slim=False):
    video = read(ROOT / 'MyVideoNav.xml')
    old = read(BASE / 'View_50_List.xml')
    file = ROOT / 'Includes_InfinityMediaLists.xml'
    new = read(file) if file.exists() else E.Element('includes')
    selected = []
    for n in video.iter('include'):
        name = n.text or ''
        original = name.removeprefix('InfinityMedia_')
        if name == 'InfinityCinemaBrowseList':
            if predicate(n.get('condition','True'), initial, plugin, mode, slim):selected.append((name,50))
        elif original in NAMES and predicate(n.get('condition','True'), initial, plugin, mode, slim):
            root = new if name.startswith('InfinityMedia_') else old
            definition = root.find("include[@name='%s']" % name)
            cid = NAMES[original] if root is new else 50
            control = definition.find(".//control[@id='%s']" % cid)
            if predicate(control.findtext('visible','True'), current, plugin, mode, slim):
                selected.append((original,cid))
    return selected


def canonical(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(),
            tuple(canonical(n) for n in node))


class ListRegistration(unittest.TestCase):
    def test_registered_media_list_exists_before_provider_content(self):
        # Fails in ca5153cb: include expansion captures empty/file content and
        # leaves the generic plugin list registered for later movie results.
        self.assertEqual(available('', 'movies', 'plugin.video.qa'), [('VideoList',50)])
        self.assertEqual(available('files', 'movies', 'plugin.video.qa'), [('VideoList',50)])

    def test_one_family_across_initial_content_and_later_content_changes(self):
        for initial in ('','files','movies','tvshows'):
            for content in ('','files','playlists','addons','studios') + MEDIA:
                for plugin in ('','plugin.video.qa'):
                    for mode in ('auto','compact','cinema'):
                        for slim in (False,True):
                            if mode == 'cinema':wanted = ('InfinityCinemaBrowseList',50)
                            elif content in MEDIA or (not plugin and content not in ('','files','playlists','addons')):
                                wanted = ('SlimVideoList' if slim else 'VideoList',50)
                            elif not plugin:wanted = ('InfinityCoreDirectory',65050)
                            elif mode == 'compact':wanted = ('InfinityPluginDirectoryCompact',65052)
                            else:wanted = ('InfinityPluginDirectoryRegular',65051)
                            self.assertEqual(available(initial,content,plugin,mode,slim), [wanted],
                                             (initial,content,plugin,mode,slim))

    def test_original_view_ids_and_native_fallback_order_preserved(self):
        before = E.parse(BASE/'MyVideoNav.xml').getroot().findtext('views').split(',')
        after = E.parse(ROOT/'MyVideoNav.xml').getroot().findtext('views').split(',')
        self.assertEqual(after[:4], ['50','65050','65051','65052'])
        self.assertEqual([v for v in after if v not in ('65050','65051','65052')], before)
        self.assertEqual(len(after),len(set(after)))

    def test_original_list_visuals_metadata_and_actions_are_retained(self):
        old = E.parse(BASE/'View_50_List.xml').getroot()
        new = E.parse(ROOT/'Includes_InfinityMediaLists.xml').getroot()
        for name, cid in NAMES.items():
            a = copy.deepcopy(old.find("include[@name='%s']"%name))
            b = copy.deepcopy(new.find("include[@name='InfinityMedia_%s']"%name));b.set('name', name)
            if cid != 50:
                mapping = {str(cid):'50',str(cid+100):'95060'}
                for n in b.iter():
                    if n.tag=='control' and n.get('id') in mapping:n.set('id',mapping[n.get('id')])
                    if n.tag=='param' and n.get('name')=='control' and n.get('value') in mapping:n.set('value',mapping[n.get('value')])
                    if n.text:
                        if n.tag in ('onup','ondown','onleft','onright','pagecontrol') and n.text in mapping:n.text=mapping[n.text]
                        for k,v in mapping.items():
                            n.text=n.text.replace('('+k+')','('+v+')').replace('SetFocus('+k+',','SetFocus('+v+',')
                    for attr,value in list(n.attrib.items()):
                        for k,v in mapping.items():value=value.replace('('+k+')','('+v+')').replace('SetFocus('+k+',','SetFocus('+v+',')
                        n.set(attr,value)
            # Only the container availability predicate differs; original
            # node order/coordinates/fonts/art/metadata/actions otherwise match.
            for n in (a,b):
                c=n.find(".//control[@id='50']")
                for v in c.findall('visible'):c.remove(v)
            self.assertEqual(canonical(a),canonical(b),name)

    def test_source_selection_is_static_and_availability_is_runtime(self):
        video=E.parse(ROOT/'MyVideoNav.xml').getroot()
        for n in video.iter('include'):
            if (n.text or '').removeprefix('InfinityMedia_') in NAMES:
                self.assertNotIn('Container.',n.get('condition',''))
        self.assertFalse((ROOT/'View_50_List.xml').exists(), 'Do not rewrite shared List implementations')

    def test_explicit_list_uses_one_valid_target_for_each_context(self):
        root=E.parse(ROOT/'custom_1136_InfinityVideoViews.xml').getroot()
        item=next(i for i in root.findall('.//content/item') if i.findtext('onclick')=='Skin.SetString(Infinity.MediaView.Default,50)')
        actions=[n for n in item.findall('onclick') if (n.text or '').startswith('Container.SetViewMode(')]
        for content in ('','files','addons','studios')+MEDIA:
            for plugin in ('','plugin.video.qa'):
                for mode in ('auto','compact','cinema'):
                    active=[int(n.text.split('(')[1][:-1]) for n in actions if predicate(n.get('condition','True'),content,plugin,mode)]
                    expected=available('',content,plugin,mode)[0][1]
                    self.assertEqual(active,[expected],(content,plugin,mode))

    def test_loading_controls_cover_internal_folder_ids(self):
        root=E.parse(ROOT/'MyVideoNav.xml').getroot()
        frames=[n.text for n in root.findall('onload') if 'FrameControls' in (n.text or '')]
        self.assertEqual(len(frames),2)
        for row in frames:
            for cid in ('50','65050','65051','65052'):self.assertIn('|'+cid+'|',row)

    def test_video_list_predicates_preserve_folder_semantics(self):
        before=E.parse(BASE/'MyVideoNav.xml').getroot()
        after=E.parse(ROOT/'MyVideoNav.xml').getroot()
        def conditions(root):
            return [n.text for n in root.iter() if n.text and 'Control.IsVisible(50)' in n.text]
        old,new=conditions(before),conditions(after)
        self.assertEqual(len(old),len(new))
        for a,b in zip(old,new):
            self.assertIn(FAMILY,b)
            self.assertEqual(b.replace(FAMILY,'Control.IsVisible(50)'),a)

    def test_shared_compatibility_includes_are_not_modified(self):
        for name in ('Includes_Backgrounds.xml','Includes_InfinityRepairs.xml','Includes_Animations.xml','Variables.xml'):
            self.assertFalse((ROOT/name).exists())
        root=E.parse(ROOT/'Includes_InfinityMediaLists.xml').getroot()
        for name,file in [('Topbar','Includes.xml'),('DefaultLetterJump','Includes.xml'),('CommonBackground','Includes_Backgrounds.xml')]:
            a=E.parse(BASE/file).getroot().find("include[@name='%s']"%name)
            b=copy.deepcopy(root.find("include[@name='InfinityMedia_%s']"%name));b.set('name',name)
            for n in b.iter():
                if n.text:n.text=n.text.replace(FAMILY,'Control.IsVisible(50)')
                for k,v in list(n.attrib.items()):n.set(k,v.replace(FAMILY,'Control.IsVisible(50)'))
                if n.tag=='include':
                    if (n.text or '').startswith('InfinityMedia_'):n.text=n.text.removeprefix('InfinityMedia_')
                    if n.get('content','').startswith('InfinityMedia_'):n.set('content',n.get('content').removeprefix('InfinityMedia_'))
            self.assertEqual(canonical(a),canonical(b),name)


if __name__=='__main__':unittest.main()
