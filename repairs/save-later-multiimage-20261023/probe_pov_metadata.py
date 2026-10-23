"""Read-only execution of the published POV metadata HTTP functions.

Uses only the distribution's public default metadata token in memory. Never
loads user accounts, installs/imports a provider, or touches its caches/DBs.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class HttpPeer:
    """Only transport adaptation; the two provider functions run unchanged."""
    def request(self,method,url,headers,timeout):
        request=Request(url,headers=headers,method=method.upper())
        try:response=urlopen(request,timeout=timeout)
        except HTTPError as error:response=error
        with response:
            self.last_status=response.status
            raw=response.read(4*1024*1024)
            return type('Reply',(),dict(headers=response.headers,ok=200<=response.status<300,
                reason=response.reason,url=url,text=raw.decode('utf-8'),
                json=lambda self:json.loads(raw)))()


def probe(root):
    source=root/'resources/lib/indexers/tmdb_api.py';raw=source.read_bytes()
    tree=ast.parse(raw);names={'get_tmdb','tvshow_details'}
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    if {n.name for n in functions}!=names:raise RuntimeError('Provider functions absent')
    token=ET.parse(root/'resources/settings.xml').getroot().find('.//setting[@id="tmdb_read_token"]').get('default')
    # The provider catches and logs HTTP failures. Capture only a boolean;
    # avoid exporting request URLs, authorization headers, or response secrets.
    errors=[]
    http=HttpPeer()
    scope=dict(READ_TOKEN=token,session=http,base_url='https://api.themoviedb.org',
               timeout=5,logger=lambda *a:errors.append(True))
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),scope)
    output=[]
    for tmdb in ('330430','296756'):
        errors.clear();data=scope['tvshow_details'](tmdb,'en')
        valid=isinstance(data,dict) and str(data.get('id'))==tmdb
        output.append(dict(tmdb=tmdb,http_status=getattr(http,'last_status',None),response_received=isinstance(data,dict),request_failure_logged=bool(errors),
            identity_verified=valid,title=data.get('name') if valid else None,
            external_ids={k:data.get('external_ids',{}).get(k) for k in ('tvdb_id','imdb_id')} if valid else {},
            seasons=len(data.get('seasons') or []) if valid else None,
            episodes=data.get('number_of_episodes') if valid else None))
    return dict(scope=__doc__,transport='stdlib HTTP peer; not Kodi/provider session runtime',source_sha256=hashlib.sha256(raw).hexdigest(),epoch_ms=round(time.time()*1000),results=output,
                exact_physical_exception_reproduced=False,provider_profile_or_database_modified=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=probe(a.source)
    a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
