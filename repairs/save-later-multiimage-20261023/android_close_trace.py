"""Disposable fixture-only close-call observation; never packaged in an APK.

Records types and code locations, never paths from handles, payloads or accounts.
Profiling can perturb timing; a diagnostic pass cannot resolve an earlier fail.
No method is replaced and no file operation or checkpoint receipt is intercepted.
"""
import sys
import time

_events = []
_overflow = 0
_limit = 256


def observe(frame, event, function):
    global _overflow
    if event not in ('c_call', 'c_return', 'c_exception'):
        return
    if getattr(function, '__name__', '') != 'close':
        return
    if len(_events) >= _limit:
        _overflow += 1
        return
    owner = getattr(function, '__self__', None)
    kind = type(owner)
    callers = []
    current = frame
    for _ in range(6):
        if current is None:
            break
        code = current.f_code
        callers.append(dict(file=code.co_filename, function=code.co_name, line=current.f_lineno))
        current = current.f_back
    _events.append(dict(event=event, monotonic_ns=time.monotonic_ns(),
                        object_id=id(owner), object_type=kind.__module__+'.'+kind.__qualname__,
                        callers=callers))


def start():
    if sys.getprofile() is not None:
        raise RuntimeError('Existing fixture profiler must not be overwritten')
    sys.setprofile(observe)


def finish():
    # Observe only this disposable service's main-thread startup. Preserve the
    # original service, provider, native ledger and Close/readback assertions.
    if sys.getprofile() is not observe:
        raise RuntimeError('Fixture close profiler changed unexpectedly')
    sys.setprofile(None)
    import json
    import xbmc
    xbmc.log('INFINITY_CLOSE_DIAGNOSTIC '+json.dumps(dict(
        schema=1, diagnostic_only=True, thread_scope='future-fixture-main-startup',
        events=_events, overflow=_overflow, no_operation_results_changed=True,
        timing_may_be_perturbed=True)), xbmc.LOGINFO)
