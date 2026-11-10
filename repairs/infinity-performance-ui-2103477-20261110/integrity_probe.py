"""Disposable Android actual-authenticated-source worker checks; never shipped."""
import os
import threading
import time
from pathlib import Path


def require(value,label):
    if not value:raise RuntimeError(label)

def resources(root):
    descriptors=[]
    for name in os.listdir('/proc/self/fd'):
        try:
            target=os.readlink('/proc/self/fd/'+name)
            if target==str(root) or target.startswith(str(root)+'/'):descriptors.append(target)
        except OSError:pass
    return dict(at=time.monotonic(),process_cpu=time.process_time(),all_fds=len(os.listdir('/proc/self/fd')),
                skin_descriptors=descriptors,python_threads=[t.name for t in threading.enumerate()])

def worker_contracts(service,common,monitor):
    service._integrity_monitor=monitor
    service._integrity_foreground=service.ForegroundGate(service.xbmc)
    root=Path(service.xbmcvfs.translatePath('special://skin')).resolve()
    result={'before':resources(root),'dispatches':[]}
    start=time.monotonic();pending=service._background_integrity();job=service._integrity_job
    result['dispatch_ms']=1000*(time.monotonic()-start)
    require(pending['status']=='checking' and job is not None,'REAL_NONBLOCKING_JOB_ADMITTED')
    require(job['thread'].daemon is False,'NONDAEMON_OWNED_WORKER')
    for _ in range(8):
        now=time.monotonic();reply=service._background_integrity()
        result['dispatches'].append(dict(milliseconds=1000*(time.monotonic()-now),status=reply['status'],alive=job['thread'].is_alive()))
        require(service._integrity_job is job or service._integrity_job is None,'NO_DUPLICATE_WORKER')
        if not job['thread'].is_alive():break
        monitor.waitForAbort(.025)
    until=time.monotonic()+35
    while job['thread'].is_alive() and time.monotonic()<until and not monitor.abortRequested():monitor.waitForAbort(.025)
    require(not job['thread'].is_alive(),'WORKER_COMPLETES_WITHIN_COOPERATIVE_BUDGET_AND_MARGIN')
    accepted=service._background_integrity()
    result['worker_wall_ms']=1000*(time.monotonic()-start);result['worker_result']=accepted
    require(accepted['status']=='ok' and accepted['checked']==948,'COMPLETE948_CURRENT_RESULT')
    result['after_worker']=resources(root)
    now=time.monotonic();manual=common.skin_baseline_integrity();result['manual_ms']=1000*(time.monotonic()-now)
    require(accepted==manual,'ACTUAL_ANDROID_MANUAL_WORKER_RESULT_PARITY')
    result['manual_result']=manual
    # Reset this private diagnostic instance only. The actual resident globals are another interpreter.
    previous_cache=service._integrity_cache
    service._integrity_checked_at=0;service._integrity_retry_after=0
    service._background_integrity();canceled=service._integrity_job
    require(canceled is not None,'OWNED_SECOND_JOB')
    result['alive_before_cancel']=canceled['thread'].is_alive()
    service._cancel_integrity();until=time.monotonic()+5
    while canceled['thread'].is_alive() and time.monotonic()<until:monitor.waitForAbort(.01)
    require(not canceled['thread'].is_alive(),'COOPERATIVE_EVENT_CANCEL_RETIREMENT')
    service._background_integrity()
    require(service._integrity_cache is previous_cache and service._integrity_job is None,'CANCELED_GENERATION_NOT_ACCEPTED')
    result['cancellation_during_read_observed']=result['alive_before_cancel'] and canceled.get('result',{}).get('status')=='canceled'
    result['cancellation_attribution']='Completion can win the event race; parent rejection is mandatory regardless of private result status'
    result['cancellation_result']=canceled['result'];result['after_cancel']=resources(root)
    require(not any(t.name=='InfinitySkinIntegrity' for t in threading.enumerate()),'OWNED_WORKER_THREAD_RETIRED')
    result['FD_attribution']='Process-wide descriptors include the separately running resident and GUI; raw samples retained, not exclusive leak proof'
    result['scope']='Real authenticated functions and SDK/gate in private QA interpreter; resident verified separately'
    return result
