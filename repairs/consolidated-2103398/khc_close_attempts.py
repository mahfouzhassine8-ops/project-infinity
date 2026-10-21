"""Read actual per-attempt native receipts; never grant shutdown authority."""
import json
from pathlib import Path
import re


def collect(root):
    root=Path(root)
    result={'schema':1,'attempts':[],'history_complete':True,'termination_authority':False}
    if root.is_symlink() or not root.is_dir():
        result['history_complete']=False
        return result
    files=sorted(root.glob('attempt-*.json'))
    if len(files)>512:result['history_complete']=False
    for path in files[-512:]:
        if path.is_symlink() or not re.fullmatch(r'attempt-[A-Za-z0-9-]+-(?:CHECKPOINT_FAILED|SAFE_TO_TERMINATE)\.json',path.name):continue
        try:
            with path.open('rb') as f:raw=f.read(262145)
            if len(raw)>262144:raise ValueError()
            row=json.loads(raw)
            session=row.get('session');pid=row.get('pid');phase=row.get('phase')
            if not isinstance(session,str) or type(pid) is not int or phase not in ('CHECKPOINT_FAILED','SAFE_TO_TERMINATE'):raise ValueError()
            owners=[{'owner':o.get('owner'),'result':o.get('result'),'required_writes_finished':o.get('required_writes_finished') is True,'dirty_remaining':o.get('dirty_remaining') is True} for o in row.get('owners',[]) if o.get('essential') is True]
            scripts=row.get('script_persistence') or {}
            result['attempts'].append({'session':session,'pid':pid,'phase':phase,
                'checkpoint':'FAILED' if phase=='CHECKPOINT_FAILED' else 'NATIVE_SAFE_RECEIPT',
                'essential_writes_durable':row.get('essential_writes_durable') is True,
                'essential_owners':owners,'unverified_protected_writer_count':scripts.get('blocking_count'),
                'optional_unfinished_writers':row.get('optional_unfinished_writers'),
                'exit_authorization_consumed':'NEEDS_SEPARATE_ANDROID_RECEIPT',
                'engine_termination':'NEEDS_SEPARATE_PROCESS_DEATH_RECEIPT',
                'whole_package_termination':'NEEDS_SEPARATE_PACKAGE_PROCESS_RECEIPT',
                'fatal_crash':'NOT_INFERRED_FROM_CHECKPOINT','recovered_ui_freeze':'SEPARATE_INCIDENT'})
        except (OSError,ValueError,TypeError,AttributeError):result['history_complete']=False
    return result
