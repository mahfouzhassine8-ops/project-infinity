"""Read-only endpoint evidence; outages are recorded separately from fixture test results."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import urllib.request
from zoneinfo import ZoneInfo

SPECS = [('nfl','football','nfl'),('nba','basketball','nba'),('mlb','baseball','mlb'),
 ('nhl','hockey','nhl'),('ncaaf','football','college-football'),('ncaam','basketball','mens-college-basketball'),
 ('wnba','basketball','wnba'),('epl','soccer','eng.1'),('ucl','soccer','uefa.champions'),
 ('mls','soccer','usa.1'),('laliga','soccer','esp.1'),('bundesliga','soccer','ger.1'),
 ('seriea','soccer','ita.1'),('ligue1','soccer','fra.1'),('uel','soccer','uefa.europa')]


def read(task):
    (key,sport,league),day=task
    row={'league':key,'day':day,'started_at':datetime.now(timezone.utc).isoformat()}
    started=time.monotonic()
    for host in ('site.api.espn.com','site.web.api.espn.com'):
        url=f'https://{host}/apis/site/v2/sports/{sport}/{league}/scoreboard?limit=500&dates={day}'
        if key=='ncaaf': url+='&groups=80'
        if key=='ncaam': url+='&groups=50'
        try:
            req=urllib.request.Request(url,headers={'Accept':'application/json','Cache-Control':'no-cache','Pragma':'no-cache','User-Agent':'Cobra-Sports-Audit/2103323'})
            with urllib.request.urlopen(req,timeout=10) as response:
                payload=json.load(response);row['headers']={k:response.headers.get(k) for k in ('Date','Age','Cache-Control','Last-Modified')}
            assert isinstance(payload.get('events'),list),'Missing events array'
            row.update(ok=True,url=url,event_count=len(payload['events']),events=[])
            for event in payload['events']:
                status=event.get('status',{});kind=status.get('type',{})
                comps=event.get('competitions') or [{}]
                row['events'].append({'id':event.get('id'),'date':event.get('date'),'name':event.get('shortName'),
                    'state':kind.get('state'),'period':status.get('period'),'detail':kind.get('shortDetail'),
                    'scores':[{k:c.get(k) for k in ('homeAway','score')} for c in comps[0].get('competitors',[])]})
            break
        except Exception as error: row.setdefault('errors',[]).append(f'{host}: {type(error).__name__}: {error}')
    row.setdefault('ok',False);row['elapsed_seconds']=round(time.monotonic()-started,3)
    row['received_at']=datetime.now(timezone.utc).isoformat();return row


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    now=datetime.now(ZoneInfo('America/Detroit'))
    days=[(now-timedelta(days=1)).strftime('%Y%m%d'),now.strftime('%Y%m%d')]
    with ThreadPoolExecutor(max_workers=8) as pool: rows=list(pool.map(read,[(s,d) for s in SPECS for d in days]))
    report={'observation_only':True,'timezone':'America/Detroit','leagues_checked':len(SPECS),
        'successful_requests':sum(r['ok'] for r in rows),'total_requests':len(rows),'snapshots':rows,
        'limits':'External endpoint reachability and response evidence; one snapshot cannot prove continuous upstream freshness or physical device ticker delivery.'}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(f"ESPN endpoint audit: {report['successful_requests']}/{len(rows)} requests succeeded across {len(SPECS)} leagues")
