"""Build reviewed navigation API shapes from immutable public distributions.

These are inputs for the generic resolver, not executable provider patches.
The generated contracts carry code-shape pins; per-open raw pins are mandatory.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import zipfile

HERE = Path(__file__).resolve().parent
PROOFS = (
    dict(family='mode-list-v1', addon='plugin.video.pov', version='6.10.21',
         archive='pov-6.10.21.zip', sha256='e75d5e0946631a735efa6e3cab62d5121f5cb52e6ab829de1a1a4673ff3c4c98',
         url='https://raw.githubusercontent.com/kodifitzwell/repo/master/plugin.video.pov/plugin.video.pov-6.10.21.zip',
         git_blob='2bd9233a980758dd8471bb9eb0e10267fa1629de',
         entrypoint='resources/lib/router.py',
         sources=['resources/lib/router.py', 'resources/lib/modules/entry.py',
                  'resources/lib/modules/kodi_utils.py', 'resources/lib/menus/tvshows.py',
                  'resources/lib/menus/movies.py', 'resources/lib/menus/seasons.py',
                  'resources/lib/indexers/metadata.py'],
         search={'movie':dict(params={'mode':'build_movie_list','action':'tmdb_movies_search'},query_key='query'),
                 'tv':dict(params={'mode':'build_tvshow_list','action':'tmdb_tv_search'},query_key='query')}),
    dict(family='action-list-v1', addon='plugin.video.umbrella', version='6.7.729',
         archive='umbrella-6.7.729.zip', sha256='df02c5de5b614d70c32c27917d7e27110947b03efb15980f461522a5abceff3a',
         url='https://raw.githubusercontent.com/umbrellaplug/umbrellaplug.github.io/c8e728d65cf2eb9b35501d90f218a49db44f46ca/omega/zips/plugin.video.umbrella/plugin.video.umbrella-6.7.729.zip',
         entrypoint='umbrella.py',
         sources=['umbrella.py','resources/lib/modules/router.py',
                  'resources/lib/menus/tvshows.py','resources/lib/menus/movies.py',
                  'resources/lib/menus/seasons.py','resources/lib/menus/episodes.py',
                  'resources/lib/modules/control.py'],
         search={'movie':dict(params={'action':'movieSearchterm'},query_key='name'),
                 'tv':dict(params={'action':'tvSearchterm'},query_key='name')}),
    dict(family='json-args-list-v1', addon='plugin.video.seren', version='4.3.214',
         archive='seren-4.3.214.zip', sha256='83e4f40478b091ec21beb012ec0fdd060e0e0ce539c09e9a177b018beb35d3bf',
         url='https://raw.githubusercontent.com/deklica/repo.dexe/824cbcaddf0ca88230300805f5b78744b0297eea/zips/plugin.video.seren/plugin.video.seren-4.3.214.zip',
         entrypoint='seren.py',
         sources=['seren.py','resources/lib/modules/router.py','resources/lib/modules/globals.py',
                  'resources/lib/common/tools.py','resources/lib/gui/movieMenus.py',
                  'resources/lib/gui/tvshowMenus.py','resources/lib/modules/list_builder.py'],
         search={'movie':dict(params={'action':'moviesSearch'},query_key='action_args',query_codec='seren_json'),
                 'tv':dict(params={'action':'showsSearch'},query_key='action_args',query_codec='seren_json')}),
)


def build(folder):
    # Import only Infinity's pure fingerprint helper; never import a provider.
    peers = ('xbmc','xbmcaddon','xbmcgui','xbmcplugin','xbmcvfs','infinity_search','resume_hub')
    original = {n:sys.modules.get(n) for n in peers}
    try:
        for n in peers:sys.modules[n]=types.ModuleType(n)
        spec=importlib.util.spec_from_file_location('navigation_shape',HERE/'saved_navigation.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    finally:
        for n,p in original.items():
            if p is None:sys.modules.pop(n,None)
            else:sys.modules[n]=p
    contracts=[]
    for proof in PROOFS:
        raw=(folder/proof['archive']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=proof['sha256']:
            raise RuntimeError('Unverified public distribution: '+proof['archive'])
        with zipfile.ZipFile(folder/proof['archive']) as archive:
            names=archive.namelist()
            if len(names)!=len(set(names)) or archive.testzip():raise RuntimeError('Invalid provider archive')
            pins={name:module.fingerprint(archive.read(proof['addon']+'/'+name),proof['addon'])
                  for name in proof['sources']}
        contracts.append(dict(family=proof['family'],entrypoint=proof['entrypoint'],
                              sources=pins,search=proof['search']))
    return dict(schema=1,contracts=contracts,provenance=[{k:v for k,v in p.items()
                if k not in ('sources','search','entrypoint','family')} for p in PROOFS])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--providers',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.write_text(json.dumps(build(a.providers),indent=2,sort_keys=True)+'\n')
