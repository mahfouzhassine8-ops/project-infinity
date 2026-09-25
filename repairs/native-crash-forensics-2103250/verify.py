#!/usr/bin/env python3
"""Verify the 2103250 crash-forensics APK against exact locked 2103229."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, zipfile
from pathlib import Path

VERSION=2103250
NAME='1.0.9-Native-Crash-Forensics-RC1'
PARENT_SHA='3a80480e300bafc6071aed7f494cc6b3a96a79f7e1e4dcb9ae87fe36c9a707f5'
NATIVE_SHA='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'
SIGNER='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
RECORDER='lib/arm64-v8a/libinfinitycrash.so'
LIBKODI='lib/arm64-v8a/libkodi.so'
DEX=re.compile(r'classes\d*\.dex$')
SIG=re.compile(r'META-INF/[^/]+\.(?:RSA|DSA|EC|SF|MF)$',re.I)


def hb(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha(p:Path)->str:return hb(p.read_bytes())
def req(v,msg):
    if not v: raise RuntimeError(msg)

def handler_body(c:str)->str:
    m=re.search(r'static void crash_handler\([^)]*\)\s*\{',c)
    req(m,'crash_handler missing')
    i=m.end()-1; depth=0
    while i<len(c):
        if c[i]=='{': depth+=1
        elif c[i]=='}':
            depth-=1
            if depth==0:return c[m.start():i+1]
        i+=1
    raise RuntimeError('unclosed crash_handler')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--recorder',type=Path,required=True)
    p.add_argument('--recorder-source',type=Path,required=True)
    p.add_argument('--signing',type=Path,required=True)
    p.add_argument('--badging',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)

    req(sha(a.parent)==PARENT_SHA,'wrong locked 2103229 parent APK')
    req(a.candidate.is_file(),'candidate APK missing')
    report=json.loads(a.audit.read_text())
    req(report.get('version_code')==VERSION,'packager versionCode mismatch')
    req(report.get('version_name')==NAME,'packager versionName mismatch')
    req(report.get('signer_certificate_sha256')==SIGNER,'permanent signer changed')
    req(report.get('apk_sha256')==sha(a.candidate),'APK receipt hash mismatch')
    req(report.get('native_engine_sha256')==NATIVE_SHA,'packager native engine drift')
    req(report.get('diagnostic_native_library_added')==RECORDER,'diagnostic native library receipt missing')

    with zipfile.ZipFile(a.parent) as old, zipfile.ZipFile(a.candidate) as new:
        req(old.testzip() is None and new.testzip() is None,'APK CRC failure')
        on=set(old.namelist()); nn=set(new.namelist())
        req(RECORDER not in on and RECORDER in nn,'recorder inventory contract failed')
        req(nn-on=={RECORDER},'candidate added unexpected APK members: '+repr(sorted(nn-on)))
        req(on-nn==set(),'candidate removed APK members: '+repr(sorted(on-nn)))
        req(hb(old.read(LIBKODI))==NATIVE_SHA,'locked parent libkodi identity drift')
        req(new.read(LIBKODI)==old.read(LIBKODI),'libkodi.so changed')
        req(hb(new.read(RECORDER))==sha(a.recorder),'recorder APK bytes differ from compiled recorder')

        allowed=lambda n: n=='AndroidManifest.xml' or DEX.fullmatch(n) or SIG.fullmatch(n)
        changed=[]
        for n in sorted(on):
            if old.read(n)!=new.read(n): changed.append(n)
        unexpected=[n for n in changed if not allowed(n)]
        req(not unexpected,'unprotected parent APK payload changed: '+repr(unexpected[:20]))

        protected_native=[n for n in on if n.startswith('lib/') and not n.endswith('/')]
        for n in protected_native:
            req(old.read(n)==new.read(n),'existing native library changed: '+n)
        for prefix in ('assets/','res/'):
            for n in on:
                if n.startswith(prefix) and not n.endswith('/'):
                    req(old.read(n)==new.read(n),'asset/resource changed: '+n)
        req(old.read('resources.arsc')==new.read('resources.arsc'),'resources.arsc changed')
        joined=b''.join(new.read(n) for n in nn if DEX.fullmatch(n))
        for token in (b'nativeCrashRecorder.loaded',b'nativeCrashRecorder.unavailable',
                      b'trace_request_attempted',b'process_state_summary',
                      b'native_crash_record',b'native_pc_resolution',b'main.onResume'):
            req(token in joined,'compiled diagnostics token missing: '+repr(token))

    badging=a.badging.read_text(errors='replace')
    req(f"versionCode='{VERSION}'" in badging and f"versionName='{NAME}'" in badging,
        'badging identity mismatch')
    signing=a.signing.read_text(errors='replace').lower()
    req(SIGNER in signing,'signing verification does not contain permanent certificate')

    main=(a.source/'tools/android/packaging/xbmc/src/Main.java.in').read_text()
    exit_src=(a.source/'tools/android/packaging/xbmc/src/InfinityExitDiagnostics.java.in').read_text()
    for token in ('System.loadLibrary("infinitycrash")','InfinityExitDiagnostics.snapshotNativeMaps',
                  'main.onCreate.beforeNative','main.onResume','main.onPause','main.onStop'):
        req(token in main,'Main diagnostic hook missing: '+token)
    for token in ('collector_version", "2"','getProcessStateSummary','trace_request_attempted',
                  'native_crash_record','native_pc_resolution','native-maps-pending-'):
        req(token in exit_src,'collector v2 contract missing: '+token)

    c=a.recorder_source.read_text()
    body=handler_body(c)
    for forbidden in ('malloc(','calloc(','realloc(','free(','snprintf(','printf(','fprintf(',
                      '_Unwind_Backtrace','backtrace(','JNIEnv','dladdr('):
        req(forbidden not in body,'unsafe crash-handler call/token: '+forbidden)
    for required in ('write(g_crash_fd','restore_and_reraise','__NR_gettid','fault_address=',
                     'pc=','sp=','fp=','lr=','native_engine_sha256='):
        req(required in body,'crash-handler evidence token missing: '+required)
    req('SA_SIGINFO | SA_ONSTACK' in c,'altstack signal handler contract missing')
    req('sigaction(g_signals[i], &action, &g_previous[i])' in c,'previous signal handler not preserved')
    req('__NR_tgkill' in c,'fatal signal not re-raised to Android')

    note=subprocess.run(['readelf','-n',str(a.recorder)],capture_output=True,text=True,check=True).stdout
    syms=subprocess.run(['readelf','-Ws',str(a.recorder)],capture_output=True,text=True,check=True).stdout
    req('Build ID:' in note,'crash recorder ELF build-id missing')
    req('infinity_crash_recorder_install' in syms,'recorder constructor symbol missing')

    result={
      'schema':1,'build':VERSION,'version_name':NAME,'parent':2103229,
      'parent_apk_sha256':PARENT_SHA,'candidate_apk_sha256':sha(a.candidate),
      'native_engine_sha256':NATIVE_SHA,'native_engine_rebuilt':False,
      'signer_sha256':SIGNER,'diagnostic_native_library':RECORDER,
      'diagnostic_native_library_sha256':sha(a.recorder),
      'existing_native_libraries_preserved':len(protected_native),
      'changed_parent_entries':changed,
      'assets_resources_preserved':True,'playback_native_engine_preserved':True,
      'physical_device_verified':False,
      'status':'TEST CANDIDATE — crash evidence instrumentation only; does not claim SIGSEGV fixed'
    }
    (a.out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.out/'recorder-readelf-notes.txt').write_text(note)
    (a.out/'recorder-readelf-symbols.txt').write_text(syms)
    print('PASS: exact 2103229 runtime preserved; bounded crash-forensics instrumentation added')

if __name__=='__main__':main()
