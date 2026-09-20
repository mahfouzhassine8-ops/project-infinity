#!/usr/bin/env python3
"""Run actual generated provider/RPC Java under Robolectric; no JNI or device claim."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil, subprocess, urllib.parse, urllib.request

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--dependencies',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True);src=a.out/'src';classes=a.out/'classes';src.mkdir(exist_ok=True);classes.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('provider_repair',ROOT/'apply.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
base=a.source/'tools/android/packaging/xbmc/src'
files=['content/XBMCFileContentProvider.java.in','content/XBMCContentProvider.java.in','XBMCJsonRPC.java.in','XBMCFile.java.in','XBMCProperties.java.in','XBMCTextureCache.java.in','XBMCRecommendationBuilder.java.in','channels/model/Subscription.java.in','channels/model/XBMCDatabase.java.in','channels/util/SharedPreferencesHelper.java.in']
files += [str(f.relative_to(base)) for f in (base/'model').glob('*.java.in')]
identities={}
for name in files:
    text=(base/name).read_text()
    if not a.baseline:
        if name=='content/XBMCFileContentProvider.java.in':text=m.transform_provider(text)
        elif name=='XBMCJsonRPC.java.in':text=m.transform_jsonrpc(text)
    identities[name]=hashlib.sha256(text.encode()).hexdigest()
    text=text.replace('@APP_PACKAGE@','com.projectinfinity.kodi').replace('@APP_NAME@','Cobra')
    out=src/'com/projectinfinity/kodi'/name[:-3];out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
for name,text in {
    'com/projectinfinity/kodi/R.java':'package com.projectinfinity.kodi; public class R {public static class drawable {public static final int notif_icon=17301514,ic_recommendation_80dp=17301514;} public static class color {public static final int recommendation_color=17170444;}}',
    'com/projectinfinity/kodi/Splash.java':'package com.projectinfinity.kodi; public class Splash extends android.app.Activity {}',
    'androidx/annotation/DrawableRes.java':'package androidx.annotation; public @interface DrawableRes {}',
    'androidx/annotation/Nullable.java':'package androidx.annotation; public @interface Nullable {}',
}.items():
    target=src/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
test=ROOT/('tests/Cobra2103200BaselineProviderProof.java' if a.baseline else 'tests/Cobra2103200ProviderBoundaryTest.java');shutil.copy2(test,src/'com/projectinfinity/kodi'/test.name)
gson=a.out/'gson-2.10.1.jar'
if not gson.exists():gson.write_bytes(urllib.request.urlopen('https://repo.maven.apache.org/maven2/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar',timeout=60).read())
cp=':'.join(map(str,sorted((a.dependencies/'deps').glob('*.jar'))+[gson,classes]))
compile=subprocess.run(['java','-XX:-UsePerfData','com.sun.tools.javac.Main','-cp',cp,'-d',str(classes)]+[str(f) for f in src.rglob('*.java')],capture_output=True,text=True)
(a.out/'compile.log').write_text(compile.stdout+compile.stderr)
if compile.returncode:print(compile.stdout+compile.stderr);raise SystemExit(compile.returncode)
proxy=urllib.parse.urlparse(urllib.request.getproxies().get('https',''));cmd=['java','-XX:-UsePerfData','--add-opens=java.base/java.io=ALL-UNNAMED']
if proxy.hostname:cmd += [f'-Dhttps.proxyHost={proxy.hostname}',f'-Dhttps.proxyPort={proxy.port}',f'-Dhttp.proxyHost={proxy.hostname}',f'-Dhttp.proxyPort={proxy.port}']
cmd += ['-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',f'-Dmaven.repo.local={a.dependencies}/m2','-cp',cp,'org.junit.runner.JUnitCore','com.projectinfinity.kodi.'+test.stem]
result=subprocess.run(cmd,capture_output=True,text=True);log=result.stdout+result.stderr;(a.out/'tests.log').write_text(log)
(a.out/'result.json').write_text(json.dumps({'exit_code':result.returncode,'baseline':a.baseline,'source_hashes':identities,'test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),'physical_device_verified':False,'fixture':'Actual generated provider, JSONRPC and Android APIs; caller UID simulated using Robolectric; R/Splash annotations supplied as fixture stubs; no JNI streaming'},indent=2)+'\n')
print(log);raise SystemExit(result.returncode)
