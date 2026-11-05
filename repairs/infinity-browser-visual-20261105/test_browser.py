"""Selected browser contracts; no application/provider/shutdown execution."""
import copy
import os
from pathlib import Path
import re
import subprocess
import unittest
import xml.etree.ElementTree as E
import prepare

BASE_BYTES = subprocess.run(['git', 'show', prepare.BASE + ':' + prepare.MEMBER],
                            cwd=prepare.ROOT, check=True, capture_output=True).stdout
OLD = E.fromstring(BASE_BYTES)
PATH = Path(os.environ.get('TEST_BROWSER_XML', prepare.ROOT / prepare.MEMBER))
NAMES = ('InfinityMedia_VideoList', 'InfinityMedia_SlimVideoList')


def read():
    return E.parse(PATH).getroot()


def include(root, name):
    node = root.find("include[@name='%s']" % name)
    if node is None:
        raise AssertionError('Missing existing-system browser include: ' + name)
    return node


def expand(root, node, params=None):
    """Bounded includes/params projection for geometry inspection, not Kodi."""
    params = params or {}
    node = copy.deepcopy(node)
    for n in node.iter():
        for k, v in list(n.attrib.items()):
            n.set(k, re.sub(r'\$PARAM\[([^]]+)\]', lambda m: params.get(m[1], m[0]), v))
        if n.text:
            n.text = re.sub(r'\$PARAM\[([^]]+)\]', lambda m: params.get(m[1], m[0]), n.text)
    for parent in list(node.iter()):
        for child in list(parent):
            name = child.get('content') if child.tag == 'include' else None
            if not name or not name.startswith('InfinityMedia_'):
                continue
            ref = include(root, name)
            defaults = {p.get('name'): p.get('default', '') for p in ref.findall('param')}
            defaults.update({p.get('name'): p.get('value', '') for p in child.findall('param')})
            definition = expand(root, ref.find('definition'), defaults)
            index = list(parent).index(child)
            parent.remove(child)
            for offset, item in enumerate(definition):
                parent.insert(index + offset, item)
    return node


def rect(node, width, height):
    def number(tag, parent, default):
        text = node.findtext(tag)
        if text is None:
            return default
        return float(text[:-1]) * parent / 100 if text.endswith('%') else float(text)
    x, y = number('left', width, 0), number('top', height, 0)
    w = number('width', width, width - x - number('right', width, 0))
    h = number('height', height, height - y - number('bottom', height, 0))
    return x, y, w, h


class Browser(unittest.TestCase):
    def test_columns_have_explicit_bounded_nonoverlapping_coordinate_spaces(self):
        root = read()
        for name in NAMES:
            body = include(root, name).find('control')
            left = body.find("control[@type='group']")
            selected_include = root.find("include[@name='InfinityMedia_SelectedMedia']")
            selected = (selected_include.find('definition/control') if selected_include is not None
                        else body.findall("control[@type='group']")[1])
            for w, h in [(1080, 2520), (2520, 1080), (1080, 1128), (1128, 1080),
                         (1080, 1920), (1920, 1080), (1080, 1080), (1080, 1440)]:
                bx, by, bw, bh = rect(body, w, h)
                self.assertGreaterEqual(bx, 0);self.assertGreaterEqual(by, 0)
                self.assertLessEqual(bx + bw, w);self.assertLessEqual(by + bh, h)
                self.assertGreater(bh, 500)
                lx, ly, lw, lh = rect(left, bw, bh)
                rx, ry, rw, rh = rect(selected, bw, bh)
                self.assertLess(lx + lw, rx);self.assertLessEqual(rx + rw, bw + .01)
                self.assertGreater(lw, bw * .45);self.assertGreater(rw, bw * .35)
                self.assertLessEqual(ly + lh, bh);self.assertLessEqual(ry + rh, bh)

    def test_media_rows_take_full_column_with_fixed_readable_height(self):
        for name in NAMES:
            panel = include(read(), name).find(".//control[@id='50']")
            layouts = [n for n in panel if n.tag in ('itemlayout', 'focusedlayout')]
            for layout in layouts[:2]:
                self.assertIn('Container.Content(movies)', layout.get('condition', ''))
                self.assertIn('Container.Content(tvshows)', layout.get('condition', ''))
                self.assertIn('Container.Content(episodes)', layout.get('condition', ''))
                self.assertEqual(layout.get('width'), '100%')
                self.assertGreaterEqual(float(layout.get('height')), 100)
                self.assertIsNone(layout.get('aspectratio'))

    def test_rows_keep_geometry_and_only_selected_text_can_scroll(self):
        root = read()
        for name in NAMES:
            panel = include(root, name).find(".//control[@id='50']")
            layouts = [n for n in panel if n.tag in ('itemlayout', 'focusedlayout')][:2]
            self.assertEqual(layouts[0].get('height'), layouts[1].get('height'))
            self.assertEqual(layouts[0].get('width'), layouts[1].get('width'))
            for layout in layouts:
                resolved = expand(root, layout)
                titles = [c for c in resolved.findall('.//control') if c.findtext('label') == '$INFO[ListItem.Label]']
                self.assertEqual(len(titles), 2)
                for title in titles:
                    self.assertEqual(title.get('type'), 'label')
                    self.assertGreaterEqual(float(title.findtext('left')), 90)
                    self.assertGreaterEqual(float(title.findtext('right')), 12)
                moving = next(c for c in titles if c.findtext('scroll') == 'true')
                self.assertIn('Infinity.OptionalMotionAllowed', moving.findtext('visible'))
                self.assertTrue(moving.findtext('visible').startswith('true' if layout.tag == 'focusedlayout' else 'false'))
                meta = next(c for c in resolved.findall('.//control') if c.findtext('label') == '$VAR[InfinityMedia_RowMetadata]')
                self.assertLessEqual(float(titles[0].findtext('top')) + float(titles[0].findtext('height')), float(meta.findtext('top')))
                self.assertLessEqual(float(meta.findtext('top')) + float(meta.findtext('height')), float(layout.get('height')))

    def test_selected_art_is_real_media_only_and_never_stretched(self):
        root = read()
        poster = root.find("variable[@name='InfinityMedia_SelectedPoster']")
        if poster is None:
            # Inspect the actual baseline path, not the absence of new helpers.
            selected = include(root, NAMES[0]).find('control').findall("control[@type='group']")[1]
            image = selected.find(".//control[@type='multiimage']")
            self.assertEqual(image.findtext('aspectratio'), 'keep', 'Selected media is stretched by the existing multiimage')
            self.fail('Baseline selected-poster path still falls back to a generic icon')
        text = E.tostring(poster, encoding='unicode')
        self.assertNotIn('.Icon', text);self.assertNotIn('PosterThumb', text)
        self.assertNotIn('Default', text)
        self.assertTrue(all('Container(50).ListItem.Art(' in (v.text or '') for v in poster.findall('value') if v.text))
        selected = include(root, 'InfinityMedia_SelectedMedia')
        images = [c for c in selected.findall('.//control') if c.findtext('texture') == '$VAR[InfinityMedia_SelectedPoster]']
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].findtext('aspectratio'), 'keep')
        self.assertEqual(images[0].findtext('width'), '100%')
        self.assertLessEqual(float(images[0].findtext('height').rstrip('%')), 60)
        self.assertLessEqual(float(images[0].find('height').get('max')), 540)

    def test_metadata_and_plot_remain_selected_item_data(self):
        root = read()
        text = E.tostring(include(root, 'InfinityMedia_SelectedMediaText'), encoding='unicode')
        self.assertIn('Container(50).ListItem.Label', text)
        self.assertIn('$VAR[VideoPlotVar]', text)
        meta = text
        for field in ('Year', 'Duration', 'Genre', 'Rating', 'MPAA'):
            self.assertIn('Container(50).ListItem.' + field, meta)
        self.assertIn('Skin.HasSetting(Enable.HideRatings)', meta)

    def test_missing_poster_collapses_reserved_artwork_space(self):
        root = read();selected = include(root, 'InfinityMedia_SelectedMedia')
        stack = selected.find('.//control[@id="98060"]')
        image = stack.find('control[@type="image"]')
        self.assertIn('!String.IsEmpty(Container(50).ListItem.Art(poster))', image.findtext('visible'))
        self.assertIsNone(image.find('includehidden'))
        self.assertEqual(stack.findtext('usecontrolcoords'), 'false')
        self.assertIsNone(stack.find('height'))
        self.assertEqual(stack.findtext('bottom'), '128')

    def test_actions_fit_outside_the_scrollable_details_at_short_heights(self):
        source=include(read(),'InfinityMedia_SelectedMedia')
        outer=source.find('.//control[@id="98059"]')
        self.assertEqual(outer.find('height').get('min'),'100%')
        self.assertEqual(outer.find('height').get('max'),'100%')
        details=outer.find('control[@id="98060"]')
        actions=outer.find('control[@id="98068"]')
        self.assertIsNotNone(actions)
        self.assertIsNone(details.find('.//control[@id="98070"]'))
        for available in (636,684,1476,2076):
            cap=available-float(details.findtext('bottom'))
            self.assertGreater(cap,0)
            self.assertLessEqual(cap+float(outer.findtext('itemgap'))+float(actions.findtext('height')),available)

    def test_existing_palette_and_fonts_own_new_surfaces(self):
        root = read()
        for name in ('InfinityMedia_BrowserRow','InfinityMedia_SelectedMediaText','InfinityMedia_SelectedMedia'):
            for c in include(root, name).findall('.//control'):
                if c.find('font') is not None:
                    self.assertTrue(c.findtext('font').startswith('Infinity'))
                    self.assertTrue(c.findtext('textcolor', '').startswith('$VAR[Infinity'))
                for texture in c.findall('texture'):
                    if texture.text == 'infinity_ui/contract_white.png':
                        self.assertTrue((texture.get('colordiffuse') or c.findtext('colordiffuse', '')).startswith('$VAR[Infinity'))

    def test_real_actions_are_conditional_and_use_original_native_dispatch(self):
        source = include(read(), 'InfinityMedia_SelectedMedia')
        expected = {'98070':['SetFocus(50)','Action(Select)'],
                    '98071':['PlayMedia($ESCINFO[Container(50).ListItem.Trailer])'],
                    '98072':['SetFocus(50)','Action(Info)']}
        for cid, actions in expected.items():
            c = source.find(".//control[@id='%s']" % cid)
            self.assertIsNotNone(c);self.assertEqual([n.text for n in c.findall('onclick')], actions)
            self.assertEqual(c.findtext('enable'), '!Container.IsUpdating')
            self.assertIsNotNone(c.find('visible'))
            for onclick in c.findall('onclick'):
                self.assertIn('!Container.IsUpdating', onclick.get('condition'))
                self.assertIn(c.findtext('visible'), onclick.get('condition'))
            self.assertNotIn('RunPlugin', ''.join(actions))
        self.assertIn('IsPlayable', source.find(".//control[@id='98070']/visible").text)
        self.assertIn('.Trailer', source.find(".//control[@id='98071']/visible").text)

    def test_original_container_input_and_context_ownership_are_preserved(self):
        root = read()
        for name in NAMES:
            old = include(OLD, name).find(".//control[@id='50']")
            new = include(root, name).find(".//control[@id='50']")
            for tag in ('visible','onleft','onright','onup','ondown','onclick','onback','viewtype','pagecontrol'):
                self.assertEqual([E.tostring(c) for c in old.findall(tag)], [E.tostring(c) for c in new.findall(tag)], tag)
            self.assertEqual(len(new.findall('onlongclick')), len(old.findall('onlongclick')))
            # Loading stays on the genuinely pending focused row, not every row.
        frame = include(root, 'InfinityMedia_BrowserRow').find(".//include[@content='InfinityActionLoadingFrame']")
        self.assertEqual(frame.get('condition'), '$PARAM[Focused]')

    def test_existing_non_media_rows_and_specialist_details_are_retained(self):
        def canonical(n):
            return (n.tag,n.attrib,(n.text or '').strip(),tuple(canonical(c) for c in n))
        for name in NAMES:
            old=include(OLD,name);new=include(read(),name)
            before=old.find('.//control[@id="50"]');after=new.find('.//control[@id="50"]')
            old_rows=[c for c in before if c.tag in ('itemlayout','focusedlayout')
                      and c.get('condition') not in ['Container.Content(%s)'%m for m in prepare.MEDIA]]
            new_rows=[c for c in after if c.tag in ('itemlayout','focusedlayout')][2:]
            self.assertEqual([canonical(c) for c in old_rows],[canonical(c) for c in new_rows])
            for a,b in zip(old.find('control').findall('control[@type="group"]')[1:],
                           new.find('control').findall('control[@type="group"]')[1:]):
                b=copy.deepcopy(b)
                b.find('visible').text=a.findtext('visible')
                self.assertEqual(canonical(a),canonical(b))

    def test_shared_poster_variables_preserve_every_non_media_fallback(self):
        source=Path('/tmp/infinity-signed456-payload-audit/assets/addons/skin.infinity.diggz/unified/Variables.xml')
        before=E.parse(source).getroot()
        after=E.parse(PATH.with_name('Variables.xml')).getroot()
        for old in before:
            new=after.find("%s[@name='%s']"%(old.tag,old.get('name')))
            new=copy.deepcopy(new)
            if old.get('name') in ('PosterVar','PosterThumb'):
                added=len(new)-len(old)
                self.assertGreater(added,0)
                prefix=list(new)[:added]
                for value in prefix:
                    self.assertIn('window.isactive(videos)',value.get('condition').lower())
                    self.assertIn('Container.Content(movies)',value.get('condition'))
                    self.assertNotIn('.Icon',value.text or '')
                    new.remove(value)
            def canonical(n):
                return (n.tag,n.attrib,(n.text or '').strip(),tuple(canonical(c) for c in n))
            self.assertEqual(canonical(old),canonical(new))

    def test_video_window_retains_all_original_registration_loading_and_actions(self):
        old=E.parse('/tmp/infinity-signed456-payload-audit/assets/addons/skin.infinity.diggz/unified/MyVideoNav.xml').getroot()
        new=E.parse(PATH.with_name('MyVideoNav.xml')).getroot()
        guide=new.find('controls/include[@content="InfinityMedia_TouchGuide"]')
        self.assertIsNotNone(guide);new.find('controls').remove(guide)
        parents={c:p for p in new.iter() for c in p}
        floor=next(n for n in new.iter('include') if n.text=='FloorReturnButtons')
        wrapper=parents[floor];parent=parents[wrapper]
        self.assertEqual(wrapper.get('type'),'group')
        self.assertIn('!String.IsEqual(Skin.String(Infinity.HomeView),cinema)',wrapper.findtext('visible'))
        index=list(parent).index(wrapper);wrapper.remove(floor);parent.remove(wrapper);parent.insert(index,floor)
        removed=0
        for p in new.iter():
            for v in list(p.findall('visible')):
                if v.text.startswith('![Control.IsVisible(50) + !String.IsEqual(Skin.String(Infinity.HomeView),cinema)'):
                    self.assertIn('Container.Content(movies)',v.text);p.remove(v);removed+=1
        self.assertEqual(removed,2)
        def canonical(n):
            return (n.tag,n.attrib,(n.text or '').strip(),tuple(canonical(c) for c in n))
        self.assertEqual(canonical(old),canonical(new))

    def test_white_frame_is_excluded_only_for_typed_media(self):
        for name in NAMES:
            old = include(OLD,name).find('control/control[@type="group"]/control[@type="image"]')
            new = include(read(),name).find('control/control[@type="group"]/control[@type="image"]')
            self.assertEqual(old.findtext('texture'), '$VAR[InfinityPanelTexture]' if name == NAMES[0] else 'contentpanel.png')
            self.assertIsNone(old.find('colordiffuse'))
            self.assertIn('![Container.Content(movies)', new.findtext('visible'))
            self.assertEqual(old.findtext('texture'), new.findtext('texture'))

    def test_case_fallback_cannot_cover_the_new_media_details(self):
        original=E.parse('/tmp/infinity-signed456-payload-audit/assets/addons/skin.infinity.diggz/unified/Variables.xml').getroot()
        case=original.find('variable[@name="GlobalCaseVar"]')
        self.assertEqual(case.findall('value')[-1].text,'trailers.png')
        self.assertIn('ListItem.VideoResolution',case.findall('value')[-2].get('condition'))
        selected=E.tostring(include(read(),'InfinityMedia_SelectedMedia'),encoding='unicode')
        self.assertNotIn('GlobalCaseVar',selected);self.assertNotIn('CaseTypePathVar',selected)
        for name in NAMES:
            body=include(read(),name).find('control')
            legacy=body.findall('control[@type="group"]')[1]
            self.assertIn('![Container.Content(movies)',legacy.findtext('visible'))

    def test_reference_frame_and_passive_genres_preserve_native_actions(self):
        root=read();selected=include(root,'InfinityMedia_SelectedMedia')
        poster=next(c for c in selected.findall('.//control') if c.findtext('texture')=='$VAR[InfinityMedia_SelectedPoster]')
        self.assertEqual(poster.findtext('aspectratio'),'keep')
        self.assertEqual(poster.find('bordertexture').get('colordiffuse'),'$VAR[InfinityPaletteAccent]')
        for c in selected.findall('.//control[@type="button"]'):
            self.assertEqual(c.findtext('align'),'center')
        text=include(root,'InfinityMedia_SelectedMediaText')
        chips=[c for c in text.findall('.//control') if c.get('id') in ('98090','98091','98092','98093')]
        self.assertEqual(len(chips),4)
        for c in chips:
            self.assertEqual(c.get('type'),'group');self.assertFalse(c.findall('.//onclick'))
        fallback=next(c for c in text.findall('.//control') if c.findtext('label')=='$INFO[Container(50).ListItem.Genre]')
        self.assertIn('GenreSource',fallback.findtext('visible'));self.assertIn('GenreCount',fallback.findtext('visible'))

    def test_other_include_families_unchanged_except_duplicate_media_topbar(self):
        root = read()
        for old in OLD:
            if old.get('name') in NAMES:
                continue
            new = root.find("%s[@name='%s']" % (old.tag, old.get('name')))
            if old.get('name') == 'InfinityMedia_Topbar':
                new = copy.deepcopy(new)
                v = new.findall('control/visible')[-1]
                self.assertIn('![Control.IsVisible(50)', v.text)
                self.assertIn('Container.Content(movies)', v.text)
                new.find('control').remove(v)
            # Ignore indentation only, not values/attrs/conditions/callbacks.
            def canonical(n):
                return (n.tag, n.attrib, (n.text or '').strip(), tuple(canonical(c) for c in n))
            self.assertEqual(canonical(old), canonical(new), old.get('name'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
