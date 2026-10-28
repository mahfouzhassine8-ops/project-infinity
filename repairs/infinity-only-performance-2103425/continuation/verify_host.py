"""Selected actual-source/XML integration; never claims a Kodi render test."""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import sys
import time
import tracemalloc
import types
import unittest
from urllib.parse import parse_qs, urlsplit
from lxml import etree as ET

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from verify import load_hub, fixture, definitions, listing_checks, search_checks, inventory_checks, Home
from rail_isolation import RAILS, OFFSET, OWNER

INPUT = STAGED = None


def xml(path): return ET.fromstring(path.read_bytes())
def canonical(node): return ET.tostring(node, method='c14n')


def normalize_clone(node):
    node = deepcopy(node)
    for element in node.iter():
        for key, value in list(element.attrib.items()):
            element.set(key, re.sub(r'(?<!\d)(2[89]\d{3})(?!\d)', lambda m: str(int(m[0]) - OFFSET), value))
        if element.text:
            element.text = re.sub(r'(?<!\d)(2[89]\d{3})(?!\d)', lambda m: str(int(m[0]) - OFFSET), element.text)
    node.remove(node.find('visible'))
    return node


class ActualGeneratedRails(unittest.TestCase):
    def setUp(self):
        self.skin = STAGED / 'members/assets/addons/skin.infinity.diggz'
        self.oldskin = INPUT / 'skin.infinity.diggz'

    def test_all_actual_layouts_have_unique_owned_controls_and_unchanged_card_geometry(self):
        files = list(self.skin.rglob('Home.xml'))
        self.assertEqual(len(files), 14)
        for path in files:
            old, new = xml(self.oldskin / path.relative_to(self.skin)), xml(path)
            original = {int(c.get('id')): c for c in old.iter('control') if c.get('id', '').isdigit()}
            controls = [c for c in new.iter('control') if c.get('id', '').isdigit()]
            ids = [int(c.get('id')) for c in controls]
            self.assertEqual(len(ids), len(set(ids)), str(path))
            controls = {int(c.get('id')): c for c in controls}
            for ident in RAILS:
                for target, source in ((ident, 'trakt'), (ident + OFFSET, 'infinity')):
                    self.assertIn(OWNER.format(source), controls[target].findtext('visible'))
                    self.assertNotIn(OWNER.format('infinity' if source == 'trakt' else 'trakt'), controls[target].findtext('visible'))
                    # Item/focus layouts, art bindings, actions and geometry exact.
                    for tag in ('itemlayout', 'focusedlayout', 'left', 'top', 'width', 'height',
                                'orientation', 'scrolltime', 'preloaditems'):
                        a, b = original[ident].find(tag), controls[target].find(tag)
                        self.assertEqual(None if a is None else canonical(a), None if b is None else canonical(b))
                    self.assertEqual(controls[target].findtext('content'), '$VAR[InfinityP0HomeFeed%d]' % target)

    def test_generated_includes_resolve_all_primary_secondary_routes_without_current_source(self):
        files = list(self.skin.rglob('Includes_InfinityHomeUnified.xml'))
        self.assertEqual(len(files), 10)
        for path in files:
            variables = {v.get('name'): v for v in xml(path).findall('variable')}
            for ident, (media, row) in RAILS.items():
                for target, source in ((ident, 'trakt'), (ident + OFFSET, 'infinity')):
                    values = variables['InfinityP0HomeFeed%d' % target].findall('value')
                    url = values[0].text
                    self.assertNotIn('hubsource', ''.join(values[0].itertext()))
                    self.assertNotIn('$VAR[', url)
                    query = parse_qs(urlsplit(url).query)
                    if source == 'infinity':
                        self.assertEqual(urlsplit(url).netloc, 'script.infinity.commandcenter')
                        self.assertEqual(query['media'], [media])
                        self.assertEqual(query['bucket'], [('next' if row == 'primary' else 'progress') if media == 'tv'
                                                           else ('watchlist' if row == 'primary' else 'collection')])
                        self.assertEqual(query['home'], ['1'])
                    else:
                        self.assertEqual(urlsplit(url).netloc, 'plugin.video.umbrella')
                        self.assertEqual(query['action'], [('calendar' if row == 'primary' else 'shows_progress') if media == 'tv' else 'movies'])
                        self.assertEqual(query['url'], [('progress' if row == 'primary' else 'progresstv') if media == 'tv'
                                                       else ('traktwatchlist' if row == 'primary' else 'traktcollection')])
            # View All variables stay independent of the 20-card Home projection.
            for name in ('InfinityMoviesPrimaryPath','InfinityMoviesSecondaryPath','InfinityTVPrimaryPath','InfinityTVSecondaryPath'):
                self.assertEqual(canonical(variables[name]), canonical(next(v for v in xml(self.oldskin / path.relative_to(self.skin)).findall('variable') if v.get('name') == name)))

    def test_navigation_actions_and_dependent_art_have_source_ownership(self):
        for path in self.skin.rglob('Home.xml'):
            root = xml(path)
            for element in root.iter():
                if not isinstance(element.tag, str): continue
                text = element.text or ''
                match = re.search(r'Container\((\d+)\)\.ListItem', text)
                if match and (int(match[1]) in RAILS or int(match[1])-OFFSET in RAILS):
                    source = 'trakt' if int(match[1]) in RAILS else 'infinity'
                    owners = [p.findtext('visible','') for p in element.iterancestors('control')]
                    self.assertTrue(any(OWNER.format(source) in v for v in owners), (path, text))
                match = re.fullmatch(r'(\d+)', text) if element.tag.startswith('on') else None
                if not match: match = re.search(r'SendClick\((\d+)\)', text)
                if match and (int(match[1]) in RAILS or int(match[1])-OFFSET in RAILS):
                    source = 'trakt' if int(match[1]) in RAILS else 'infinity'
                    owners = [element.get('condition','')] + [p.findtext('visible','') for p in element.iterancestors('control')]
                    self.assertTrue(any(OWNER.format(source) in v for v in owners), (path, text))

    def test_delayed_result_destinations_and_cached_selections_stay_in_separate_control_instances(self):
        # Host contract over actual generated control/provider bindings. This
        # proves disjoint destinations, not Android paint timing or job execution.
        root = xml(self.skin / 'unified/Includes_InfinityHomeUnified.xml')
        urls = {int(v.get('name').removeprefix('InfinityP0HomeFeed')): v.findtext('value')
                for v in root.findall('variable') if v.get('name','').startswith('InfinityP0HomeFeed') and
                v.get('name').removeprefix('InfinityP0HomeFeed').isdigit()}
        queues, caches, selections = [], {}, {}
        for sequence, (source, media) in enumerate([('trakt','movie'),('infinity','movie'),('trakt','tv'),('infinity','tv')]*3):
            ident = (8804 if media == 'movie' else 8803) + (OFFSET if source == 'infinity' else 0)
            queues.append((ident, source, urls[ident], sequence))
            selections.setdefault(ident, sequence % 3)
        random.Random(37).shuffle(queues)
        for ident, source, url, sequence in queues:
            self.assertEqual('infinity' if ident > OFFSET else 'trakt', source)
            self.assertEqual(urls[ident], url)
            caches[ident] = (source, 'Identical legitimate title')
        self.assertEqual(len(caches), 4)
        self.assertEqual(set(caches), set(selections))
        self.assertEqual(len({urlsplit(urls[i]).netloc for i in (8804,28804)}), 2)

    def test_generator_exact_matching_and_actual_generated_secondary_route(self):
        path = STAGED / 'candidate-addons/script.infinity.commandcenter/skin_upgrade.py'
        ns = dict(ET=__import__('xml.etree.ElementTree', fromlist=['ElementTree']))
        definitions(path, ('_content_path_var',), ns)
        cases = [(('calendar','progress'),'InfinityTVPrimaryPath'),
                 (('shows_progress','progresstv'),'InfinityTVSecondaryPath'),
                 (('movies','traktwatchlist'),'InfinityMoviesPrimaryPath'),
                 (('movies','traktcollection'),'InfinityMoviesSecondaryPath'),
                 (('movies','progresstv'),None),(('calendar','progressfake'),None)]
        for (action, route), expected in cases:
            line = '<content>plugin://plugin.video.umbrella/?action=%s&amp;url=%s</content>' % (action,route)
            self.assertEqual(ns['_content_path_var'](line), expected)
        self.assertIsNone(ns['_content_path_var']('<content>plugin://plugin.video.umbrella/?action=calendar&amp;url=progress&amp;url=progresstv</content>'))

    def test_tv_projection_equivalence_private_copies_and_bounds(self):
        old = load_hub(INPUT / 'script.infinity.commandcenter')
        new = load_hub(STAGED / 'candidate-addons/script.infinity.commandcenter')
        data = fixture(old, 180)
        # A verified completed episode has a real successor, with independent
        # library proof; malformed successors and older episodes stay excluded.
        key = next(k for k,v in data['items'].items() if v['media']=='tv')
        last = data['watched'][key]
        data['items'].pop(key)
        last.update(show_ids_verified=True, show_tmdb=last['tmdb'], watched_at=1000,
                    verified_next=dict(verified=True, after=[last['season'],last['episode']],
                        show_tmdb=last['tmdb'],season=2,episode=1,
                        library=dict(episodeid=42,file='/media/real-next.mkv')))
        original = deepcopy(data)
        for name in ('progress_shows','next_episodes'):
            before, after = getattr(old,name),getattr(new,name)
            self.assertEqual(before(deepcopy(data)), after(deepcopy(data)))
            for limit in (0,1,20,100,None):
                result = after(deepcopy(data), limit=limit)
                self.assertEqual(result, before(deepcopy(data))[:limit])
                if result:
                    if 'metadata' in result[0]: result[0]['metadata']['cast'][0]['name']='private'
                    elif 'library_next' in result[0]:result[0]['library_next']['episodeid']=99
            for limit in (-1,101,True,'20'):
                with self.assertRaises(ValueError): after(deepcopy(data),limit=limit)
        self.assertEqual(data,original)

    def test_counts_are_exact_without_copying_title_metadata_or_changing_writer_functions(self):
        old = load_hub(INPUT / 'script.infinity.commandcenter')
        new = load_hub(STAGED / 'candidate-addons/script.infinity.commandcenter')
        data = fixture(old, 300)
        expected = old.counts(deepcopy(data))
        new._entry_copy = lambda *a, **kw: self.fail('Count must not copy title metadata')
        self.assertEqual(new.counts(deepcopy(data)), expected)
        for name in ('save', 'publish_home', 'flush_kodi_sync', 'queue_kodi_sync'):
            a=(INPUT/'script.infinity.commandcenter/resume_hub.py').read_text()
            b=(STAGED/'candidate-addons/script.infinity.commandcenter/resume_hub.py').read_text()
            def source(text):
                return ast.get_source_segment(text,next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name))
            self.assertEqual(source(a),source(b))

    def test_existing_2103426_search_inventory_and_batch_behavior(self):
        root=STAGED/'candidate-addons/script.infinity.commandcenter'
        listing_checks(root, INPUT/'script.infinity.commandcenter', 'candidate')
        search_checks(root,'candidate'); inventory_checks(root,'candidate')

    def test_actual_listing_builds_only_home20_but_viewall100_and_only_continue_releases_first_viewport(self):
        root=STAGED/'candidate-addons/script.infinity.commandcenter'
        hub=load_hub(root);data=fixture(hub,240);data['watchlist']=deepcopy(data['items'])
        hub.load_view=lambda *a,**kw:deepcopy(data)
        for params,bucket,count in (({'home':'1'},'watchlist',20),({},'watchlist',100),({'home':'1'},'continue',20)):
            home=Home();built=[]
            native=types.SimpleNamespace(setPluginCategory=lambda *a:None,setContent=lambda *a:None,
                addDirectoryItems=lambda h,rows,total: self.assertEqual(len(rows),count),
                endOfDirectory=lambda *a,**kw: self.assertTrue(kw['succeeded']))
            def card(entry,*a):built.append(entry);return entry['source'],entry
            ns=dict(hub=hub,time=time,re=re,HANDLE=7,PARAMS=params,PROFILE=Path('/host'),xbmcplugin=native,
                xbmcgui=types.SimpleNamespace(Window=lambda _:home),setting_bool=lambda *a:True,
                _category=lambda *a:'Movies',prepare_render=lambda d,v,r:r,_list_item=card)
            definitions(root/'plugin.py',('listing','_values_for'),ns);ns['listing']('movie',bucket)
            self.assertEqual(len(built),count)
            self.assertEqual(home.getProperty('Infinity.Home.FirstViewportReady'),'true' if bucket=='continue' else '')


def measurements():
    old=load_hub(INPUT/'script.infinity.commandcenter')
    new=load_hub(STAGED/'candidate-addons/script.infinity.commandcenter')
    data=fixture(old,1000)
    result={}
    for name in ('progress_shows','next_episodes'):
        rows={}
        for phase,hub in (('signed2103426',old),('candidate2103427',new)):
            function=getattr(hub,name)
            copies=[];original=hub._entry_copy
            def count(*a,**kw):copies.append(1);return original(*a,**kw)
            hub._entry_copy=count
            call=lambda: function(data,**({'limit':20} if phase=='candidate2103427' else {}))[:20]
            expected=call();copy_count=len(copies);hub._entry_copy=original
            samples=[]
            for _ in range(9):
                start=time.perf_counter();self_result=call();samples.append((time.perf_counter()-start)*1000)
                assert self_result==expected
            tracemalloc.start();call();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            rows[phase]=dict(median_ms=statistics.median(samples),p95_ms=sorted(samples)[-1],samples_ms=samples,peak_traced_bytes=peak,private_entry_copies=copy_count,displayed=len(expected))
        result[name]=rows
    counts={}
    for phase,hub in (('signed2103426',old),('candidate2103427',new)):
        original=hub._entry_copy; copied=[]
        def count(*a,**kw):copied.append(1);return original(*a,**kw)
        hub._entry_copy=count; value=hub.counts(data);hub._entry_copy=original
        samples=[]
        for _ in range(9):
            start=time.perf_counter();assert hub.counts(data)==value;samples.append((time.perf_counter()-start)*1000)
        counts[phase]=dict(private_entry_copies=len(copied),median_ms=statistics.median(samples),samples_ms=samples)
    result['Home_count_projection']=counts
    result.update(conditions='Same CPython host, 1000 synthetic records with nested metadata, 9 samples; no Android/native-provider/Fold performance claim',home_request_card_builder_budget={'before':100,'after':20,'actual_panel_limit':20},shutdown='NOT_RUN',Android='NOT_RUN')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--staged',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();INPUT,STAGED=args.input,args.staged
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ActualGeneratedRails)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    report=measurements();report['selected_host_cases']=result.testsRun
    args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
