"""Opt-in, read-only API37 observation of an already-running Infinity process.

This tool never installs, starts, stops, resets or navigates the application.
It observes an independently selected action performed by a feature runner or
the user. HWUI frame statistics describe the Android Search/dialog surfaces;
they are explicitly not native Kodi/GL frame-rate evidence.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import math
from pathlib import Path
import re
import shlex
import subprocess
import time

PACKAGE='com.projectinfinity.kodi'
SCOPES=('search-enter','search-button','search-all','home-loading','scroll','rotation','option-b','idle')


def _quantile(values, fraction):
    ordered=sorted(values)
    return ordered[max(0,math.ceil(len(ordered)*fraction)-1)] if ordered else None


def hwui_rows(text):
    """Parse named framestats fields; retain valid completed frames only."""
    rows={};window='unnamed'
    for section in text.split('---PROFILEDATA---'):
        lines=section.strip().splitlines()
        names=[line.strip() for line in lines if line.strip().startswith('Window:')]
        if names:window=names[-1]
        start=next((i for i,line in enumerate(lines) if line.startswith('Flags,') and 'FrameCompleted' in line),None)
        if start is None:continue
        for record in csv.DictReader(io.StringIO('\n'.join(lines[start:]))):
            try:
                flags=int(record['Flags']);began=int(record['IntendedVsync']);done=int(record['FrameCompleted'])
            except (KeyError,TypeError,ValueError):continue
            if flags!=0 or began<=0 or done<began or done>=2**63-1:continue
            rows[(window,began)]=done
    return rows


def hwui_delta(before, after):
    original=hwui_rows(before);current=hwui_rows(after)
    fresh={key:value for key,value in current.items() if key not in original}
    milliseconds=[(done-start[1])/1e6 for start,done in fresh.items()]
    return dict(status='OBSERVED' if fresh else 'NOT_OBSERVED',source='Android HWUI framestats',
        native_kodi_gl_fps_measured=False,frame_count=len(fresh),
        median_frame_duration_ms=_quantile(milliseconds,.5),p95_frame_duration_ms=_quantile(milliseconds,.95),
        max_frame_duration_ms=max(milliseconds) if milliseconds else None,
        ring_buffer_may_omit_earlier_frames=True,
        complete_selected_action_timing=False)


def process_stat(text):
    """Linux stat fields after a process name that itself may contain spaces."""
    end=text.rfind(')')
    if end<0:raise ValueError('Process stat unavailable')
    fields=text[end+1:].split()
    if len(fields)<22:raise ValueError('Process stat incomplete')
    return dict(cpu_ticks=int(fields[11])+int(fields[12]),start_ticks=int(fields[19]),rss_pages=int(fields[21]))


def process_delta(before, after, elapsed_seconds, clock_ticks, page_size):
    if before['start_ticks']!=after['start_ticks']:return dict(status='PROCESS_REPLACED')
    ticks=after['cpu_ticks']-before['cpu_ticks']
    if elapsed_seconds<=0 or ticks<0:return dict(status='INVALID_INTERVAL')
    return dict(status='OBSERVED',elapsed_seconds=elapsed_seconds,
        cpu_percent_of_one_core=(100*ticks/clock_ticks/elapsed_seconds) if clock_ticks and clock_ticks>0 else None,
        rss_before_bytes=before['rss_pages']*page_size if page_size and page_size>0 else None,
        rss_after_bytes=after['rss_pages']*page_size if page_size and page_size>0 else None,
        clock_ticks=clock_ticks,page_size=page_size,
        cpu_interval='host monotonic interval between read-only process-stat snapshots')


class Device:
    def __init__(self, serial):
        if not serial or any(c.isspace() for c in serial):raise ValueError('Explicit ADB serial required')
        self.serial=serial

    def adb(self,*parts):
        result=subprocess.run(['adb','-s',self.serial,*map(str,parts)],capture_output=True,text=True,timeout=20)
        if result.returncode:raise RuntimeError(result.stderr.strip() or 'ADB read failed')
        return result.stdout

    def shell(self,*parts):return self.adb('shell',shlex.join(map(str,parts)))

    def admit(self, allow_fold=False):
        if self.adb('get-state').strip()!='device':raise RuntimeError('Selected device is not available')
        sdk=self.shell('getprop','ro.build.version.sdk').strip()
        if sdk!='37':raise RuntimeError('Only Android17/API37 is selected')
        model=self.shell('getprop','ro.product.model').strip()
        emulator=self.shell('getprop','ro.kernel.qemu').strip()=='1'
        if not emulator and not (allow_fold and model=='SM-F976U1'):
            raise RuntimeError('Physical observation requires explicit Fold acceptance selection')
        names=self.shell('ps','-A','-o','PID,NAME')
        processes=[]
        for line in names.splitlines():
            parts=line.split()
            if len(parts)==2 and parts[0].isdigit() and parts[1] in (PACKAGE,PACKAGE+':kodi'):
                processes.append(dict(pid=int(parts[0]),name=parts[1]))
        if not processes:raise RuntimeError('Infinity is not already running; observation will not launch it')
        return dict(sdk=37,model=model,emulator=emulator,processes=processes)


def _optional(action):
    try:return dict(status='READ',value=action())
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as error:
        return dict(status='UNAVAILABLE',reason=str(error)[:500])


def _positive(value):
    try:number=int(value.strip());return number if number>0 else None
    except (AttributeError,ValueError):return None


def resource_snapshot(device, admission):
    result={}
    for process in admission['processes']:
        pid=process['pid'];row=dict(name=process['name'],pid=pid)
        row['stat']=_optional(lambda:process_stat(device.shell('cat','/proc/'+str(pid)+'/stat')))
        row['stat_monotonic']=time.monotonic()
        row['meminfo']=_optional(lambda:device.shell('dumpsys','meminfo',str(pid)))
        result[str(pid)]=row
    # Do not retain unrelated applications from the device-wide CPU dump.
    result['own_cpuinfo']=_optional(lambda:'\n'.join(line for line in device.shell('dumpsys','cpuinfo').splitlines() if PACKAGE in line))
    return result


def frame_snapshot(device, layers):
    return dict(hwui=_optional(lambda:device.shell('dumpsys','gfxinfo',PACKAGE,'framestats')),
        native_surface_latency={name:_optional(lambda name=name:device.shell('dumpsys','SurfaceFlinger','--latency',name)) for name in layers})


def capture(device, scope, phase, seconds, out, allow_fold=False):
    if scope not in SCOPES or phase not in ('reference','candidate') or not 1<=seconds<=30:
        raise ValueError('Select one supported case, reference/candidate phase, and 1–30 seconds')
    admission=device.admit(allow_fold)
    if out.exists():raise ValueError('Refusing to overwrite an earlier observation')
    listed=_optional(lambda:device.shell('dumpsys','SurfaceFlinger','--list'))
    layers=[line for line in listed.get('value','').splitlines() if PACKAGE in line and 'SurfaceView' in line]
    clock_ticks=_positive(_optional(lambda:device.shell('getconf','CLK_TCK')).get('value'))
    page_size=_positive(_optional(lambda:device.shell('getconf','PAGESIZE')).get('value'))
    before_resources=resource_snapshot(device,admission)
    before_frames=frame_snapshot(device,layers)
    began=time.monotonic();print('Observation window ready; perform the selected action.',flush=True)
    time.sleep(seconds)
    ended=time.monotonic();after_frames=frame_snapshot(device,layers)
    after_resources=resource_snapshot(device,admission)
    report=dict(schema=1,scope=scope,phase=phase,admission=admission,
        observation_window_seconds=ended-began,before_resources=before_resources,after_resources=after_resources,
        before_frames=before_frames,after_frames=after_frames,
        application_started=False,application_stopped=False,application_settings_changed=False,
        display_refresh_changed=False,playback_fps_changed=False,shutdown='NOT RUN',
        load_latency='NOT_MEASURED: no input/readiness markers injected',
        touch_latency='NOT_MEASURED: no input/presentation correlation injected',
        native_frame_pacing='RAW_LAYER_SAMPLES_ONLY: no FPS claim from HWUI',
        processes={})
    before=before_frames['hwui'];after=after_frames['hwui']
    report['hwui']=hwui_delta(before['value'],after['value']) if before['status']==after['status']=='READ' else dict(status='UNAVAILABLE')
    for process in admission['processes']:
        key=str(process['pid']);a=before_resources[key];b=after_resources[key]
        report['processes'][key]=process_delta(a['stat']['value'],b['stat']['value'],b['stat_monotonic']-a['stat_monotonic'],clock_ticks,page_size) if a['stat']['status']==b['stat']['status']=='READ' else dict(status='UNAVAILABLE')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',required=True);parser.add_argument('--scope',choices=SCOPES,required=True)
    parser.add_argument('--phase',choices=('reference','candidate'),required=True)
    parser.add_argument('--seconds',type=int,default=10);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--physical-fold-observation',action='store_true')
    args=parser.parse_args()
    answer=capture(Device(args.serial),args.scope,args.phase,args.seconds,args.out,args.physical_fold_observation)
    print(json.dumps({key:answer[key] for key in ('scope','phase','hwui','processes','load_latency','touch_latency')},indent=2))
