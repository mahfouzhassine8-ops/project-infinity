"""Independently inspect downloaded Android receipts and persisted fixture data.

This supplements the live-device assertions in android_probe.py; it cannot grant
physical Fold acceptance or infer real installed-provider functionality.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import xml.etree.ElementTree as ET

FUTURE='service.future.persistence.7fa29'
BASELINE='17041a44f121693ab0852c6a826b7f728a4d834a64225efec363861616b698e6'
MODES=('baseline','safe','pending','opaque','lost-file')

def main():
    if sys.flags.optimize:raise RuntimeError('Audit checks require unoptimized host Python')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence-prefix',type=Path,required=True)
    p.add_argument('--candidate-sha256',required=True)
    p.add_argument('--safe-evidence',type=Path,help='Separate diagnostic-repeat root; never overwrite the failed first-run evidence')
    p.add_argument('--provenance',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();provenance=json.loads(a.provenance.read_text())
    reports={};roots={}
    fixture_hash=hashlib.sha256(Path(__file__).with_name('android_future_service.py').read_bytes()).hexdigest()
    for mode in MODES:
        roots[mode]=Path(str(a.evidence_prefix)+mode)/'android-results'
        if mode=='safe' and a.safe_evidence:roots[mode]=a.safe_evidence/'android-results'
        reports[mode]=json.loads((roots[mode]/'ANDROID17-RESULT.json').read_text())
        r=reports[mode]
        assert r['passed'] and r['mode']==mode,(mode,r.get('failure'))
        assert r['apk_sha256']==(BASELINE if mode=='baseline' else a.candidate_sha256)
        assert r['platform']['sdk']=='37' and r['platform']['release'].split('.')[0]=='17'
        assert r['platform']['qemu']=='1' and 'arm64-v8a' in r['platform']['abis']
        assert not r['physical_fold_verified'] and not r['real_provider_code_tested'] and not r['final_lock']
        assert r['fixture_manifest'][FUTURE+'/service.py']==fixture_hash
    original=reports['baseline']['cycles'][0]['service_ready']['errors']
    assert [x['value_type'] for x in original]==['NoneType','int','memoryview']
    assert all(x['exception']=='TypeError' for x in original)
    summary={}
    for mode,r in reports.items():
        rows=[]
        for c in r['cycles']:
            ready=c['service_ready'];receipt=c['receipt'];owner=c['owner'];pid=owner['pid']
            assert ready['checks_always_executed'] and ready['python_optimization']==1
            assert [x['value_type'] for x in ready['vfs_writes']]==['str','bytes','bytearray']
            assert [x['readback'] for x in ready['vfs_writes']]==['text','textbytes','textbytesarray']
            assert all(x['returned'] is True and x['native_size']==x['native_position']==x['stat_size']==len(x['readback']) for x in ready['vfs_writes'])
            assert c['essential_vfs_before_close']=='textbytesarray'
            assert ready['errors']==original and ready['failed_commit_rolled_back'] and ready['context_commit_rolled_back'] and ready['pathlike_io']
            assert receipt['pid']==pid and receipt['owner']==owner['owner']
            native=receipt['native_receipt'] if mode=='safe' else receipt['last_native_status']
            assert native['owner']==owner['owner'] and native['inventory_complete']
            assert not native['blocker_overflow'] and not native['script_persistence']['blocking_overflow']
            row=dict(cycle=c['cycle'],pid=pid,owner=owner['owner'],phase=receipt['phase'],
                authorization_consumed=receipt['authorization_consumed'],
                checkpoint_generation=native['generation'],
                essential_write_blockers=native['essential_write_blockers'],
                pending_writers=native['script_persistence']['pending_writers'])
            if mode=='safe':
                assert receipt['phase']=='COMPLETE' and receipt['checkpoint_saved']
                assert receipt['authorization_consumed'] and receipt['process_death_confirmed']
                assert all(x['pid']!=pid for x in c['processes_after'])
                assert native['essential_writes_durable'] and native['essential_writes_sealed']
                assert not native['essential_write_blockers'] and not native['script_persistence']['blocking_count']
                assert all(not name.startswith(FUTURE+':') for name in native['script_persistence']['pending_writers'])
                required=[x for x in native['owners'] if x['owner'] in native['essential_owners']]
                assert len(required)==len({x['owner'] for x in required})==16
                assert all(x['required_writes_finished'] and not x['dirty_remaining'] and
                           x['result'] in ('COMMITTED','ALREADY_DURABLE') and
                           x['checkpoint_generation']==native['generation'] for x in required)
                data=roots[mode]/('cycle-'+str(c['cycle']))/'future-data'
                assert c['essential_vfs_after_close']=='textbytesarray'
                assert (data.parent/'essential-vfs-after-close.txt').read_text()=='textbytesarray'
                for when in ('before','after'):
                    favourites=ET.fromstring((data.parent/('favourites-'+when+'-close.xml')).read_text())
                    assert any(x.get('name')=='Universal persistence preserved' and x.text=='ActivateWindow(Home)' for x in favourites)
                for name,value in [('plain-','ordinary state'),('replaced-','replaced state'),
                                   ('buffered-','buffered state'),('worker-','child buffered state')]:
                    assert (data/(name+str(pid))).read_text()==value
                for filename,table,column,value in [('history.db','history','position',37),
                        ('watched.db','watched','watched',1),('commit-controls.db','commits','value',1)]:
                    with sqlite3.connect((data/filename).resolve().as_uri()+'?mode=ro',uri=True) as db:
                        assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
                        assert db.execute('SELECT '+column+' FROM '+table).fetchall()==[(value,)]*(c['cycle']+1)
                assert 'future-provider-state' in (data/'settings.xml').read_text()
                databases=list((data.parent/'Database').glob('*.db'));assert databases
                for database in databases:
                    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
                        assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
                row.update(mandatory_owners=required,downloaded_data_readback_passed=True,
                    kodi_databases_checked=len(databases),future_writer_retired=True,
                    optional_unfinished_jobs=native.get('optional_unfinished_jobs',[]),
                    optional_unfinished_writers=native.get('optional_unfinished_writers'))
            else:
                assert receipt['phase']=='CHECKPOINT_FAILED' and not receipt['authorization_consumed']
                assert not receipt['checkpoint_saved'] and not receipt['process_death_confirmed']
                assert any(x['pid']==pid for x in c['processes_after'])
                blockers=native['essential_write_blockers'];assert blockers
                if mode=='pending':
                    assert any('pending_protected_sqlite_write_transaction' in x and FUTURE in x for x in blockers)
                    assert all(FUTURE in x and 'sqlite' in x for x in blockers)
                elif mode=='opaque':assert all('service.xbmc.versioncheck' in x for x in blockers)
                elif mode=='lost-file':
                    assert any('unflushed_protected_buffer' in x and 'buffered-'+str(pid) in x for x in blockers)
                    assert all(FUTURE in x and ('buffered-'+str(pid) in x or 'unverified_dirty_buffer_namespace' in x) for x in blockers)
                else:assert any(FUTURE in x and 'vfs_write_exception' in x for x in blockers)
                row['unverified_state_remained_blocked']=True
            rows.append(row)
        summary[mode]=rows
    safe=reports['safe'];assert len(safe['cycles'])==3
    final=safe['final_reopen_verified'];assert final['ready']['history_count']==final['ready']['watched_count']==4
    assert final['ready']['checks_always_executed'] and final['ready']['python_optimization']==1
    assert [x['readback'] for x in final['ready']['vfs_writes']]==['text','textbytes','textbytesarray']
    assert final['ready']['failed_commit_rolled_back'] and final['ready']['context_commit_rolled_back'] and final['ready']['pathlike_io']
    assert len({c['owner']['owner'] for c in safe['cycles']}|{final['owner']['owner']})==4
    result=dict(passed=True,scope='Downloaded Android17 receipts and independent read-only fixture/database audit',
        provenance=provenance,candidate_sha256=a.candidate_sha256,original_vfs_errors_preserved=original,
        controls=summary,final_reopen=final,physical_fold_verified=False,real_provider_code_tested=False,final_lock=False)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,controls={m:len(v) for m,v in summary.items()},physical_fold_verified=False)))

if __name__=='__main__':main()
