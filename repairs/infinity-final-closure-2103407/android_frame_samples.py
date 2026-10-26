"""Read-only native SurfaceFlinger sample analysis, never HWUI-as-native-FPS."""
import math


def quantile(values,fraction):
    values=sorted(values)
    return values[max(0,math.ceil(len(values)*fraction)-1)] if values else None


def presents(text):
    # AOSP FrameTracker::dumpStats: desired, actual, ready. INT64_MAX is
    # unsignalled, not a completed presentation. Keep actual unique edges.
    result=set()
    for line in text.splitlines():
        fields=line.split()
        if len(fields)!=3:continue
        try:desired,actual,ready=map(int,fields)
        except ValueError:continue
        if all(0<x<2**63-1 for x in (desired,actual,ready)):result.add(actual)
    return result


def summarize(before,after):
    fresh=sorted(presents(after)-presents(before))
    intervals=[(b-a)/1e6 for a,b in zip(fresh,fresh[1:]) if b>a]
    return dict(status='OBSERVED' if intervals else 'NOT_OBSERVED',source='matching app SurfaceView / SurfaceFlinger actual presentations',
        fresh_presentation_count=len(fresh),interval_count=len(intervals),
        median_present_interval_ms=quantile(intervals,.5),p95_present_interval_ms=quantile(intervals,.95),
        max_present_interval_ms=max(intervals) if intervals else None,
        partial_ring_buffer=True,input_cadence_influences_intervals=True,
        full_action_jank_or_touch_latency_measured=False,physical_Fold=False)


def cpu_interval(before,after,ticks_per_second):
    def stat(raw):
        end=raw.rfind(')')
        if end<0:raise ValueError('Missing stat name')
        fields=raw[end+1:].split()
        return int(fields[11])+int(fields[12]),int(fields[19])
    try:
        a,start=stat(before['proc_stat']);b,end=stat(after['proc_stat'])
        elapsed=after['monotonic']-before['monotonic']
        if start!=end or elapsed<=0 or b<a or not isinstance(ticks_per_second,int) or ticks_per_second<=0:
            raise ValueError('Invalid sample identity/interval/clock')
        return dict(status='OBSERVED',seconds=elapsed,cpu_percent_of_one_core=100*(b-a)/ticks_per_second/elapsed,
                    clock_ticks=ticks_per_second)
    except (KeyError,IndexError,ValueError,TypeError):return dict(status='UNAVAILABLE')
