from pathlib import Path
import re,json,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args();root=a.root
f=root/'shell-kodi/tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in';s=f.read_text()
def once(old,new):
 global s
 assert s.count(old)==1,(old[:100],s.count(old))
 s=s.replace(old,new)
once('  private void cobraSportsResolveAsync(CobraSportsGame game,CobraSportsResolverCallback consumer){final ArrayList<CobraSportsChannelInfo> snapshot=cobraSportsChannelSnapshot();',
 '  private long mCobraSportsActionSerial;\n  private void cobraSportsResolveAsync(CobraSportsGame game,CobraSportsResolverCallback consumer){final long request=++mCobraSportsActionSerial,ticket=mCobraNavigation.current();final String owner=cobraDrawerOwner(),profile=mFeatures.activeProfileId();final ArrayList<CobraSportsChannelInfo> snapshot=cobraSportsChannelSnapshot();')
once('publishCobraUi(()->{String top=matches.isEmpty()?"none":matches.get(0).channel.name+',
 'publishCobraUi(()->{if(request!=mCobraSportsActionSerial||!mCobraNavigation.accepts(ticket)||!owner.equals(cobraDrawerOwner())||!profile.equals(mFeatures.activeProfileId()))return;String top=matches.isEmpty()?"none":matches.get(0).channel.name+')
once('final ArrayList<CobraSportsChannelInfo> snapshot=cobraSportsChannelSnapshot();toast("Building Smart Sports Multi-View…");',
 'final long request=++mCobraSportsActionSerial,ticket=mCobraNavigation.current();final String owner=cobraDrawerOwner(),profile=mFeatures.activeProfileId();final ArrayList<CobraSportsChannelInfo> snapshot=cobraSportsChannelSnapshot();toast("Building Smart Sports Multi-View…");')
once('publishCobraUi(()->cobraSportsLaunchSmartMulti(selected,snapshot));',
 'publishCobraUi(()->{if(request!=mCobraSportsActionSerial||!mCobraNavigation.accepts(ticket)||!owner.equals(cobraDrawerOwner())||!profile.equals(mFeatures.activeProfileId()))return;cobraSportsLaunchSmartMulti(selected,snapshot);});')
once('Live mini-player edge colours • suspended in fullscreen, PiP and background','Live video colors illuminate Cobra glass, Watch controls and menus. Video stays unchanged.')
f.write_text(s)
f=root/'shell-kodi/tools/android/packaging/xbmc/build.gradle.in';s=f.read_text().replace('versionCode 2103280','versionCode 2103281').replace('1.0.9-Audit-Followup-RC1','1.0.9-Remaining-Audit-RC1');f.write_text(s)
base='ad18f93633ecc3ec74d121acf50bda873cd33cd0';apk='e12654c0d81b6b04c4507f2c8bfde9e92761ab5a93ac16b86a3f89f9b7656870'
f=root/'scripts/infinity_background_resume.py';s=f.read_text()
for key,value in [('VERSION_CODE','2103281'),('RELEASE',repr('1.0.9-Remaining-Audit-RC1')),('BASE_COMMIT',repr(base)),('BASE_APK_SHA256',repr(apk))]:
 s,n=re.subn(r'^'+key+r' = .*$',key+' = '+value,s,flags=re.M);assert n==1
f.write_text(s)
f=root/'scripts/package_background_resume.py';s=f.read_text().replace('Infinity-2103280-Audit-Followup-RC1','Infinity-2103281-Remaining-Audit-RC1').replace("'base_run':36810766190","'base_run':36818383789");f.write_text(s)
f=root/'engine/background-resume-source.json';r=json.loads(f.read_text());r.update(base_source_commit=base,base_apk_sha256=apk,version_code=2103281,release='1.0.9-Remaining-Audit-RC1',candidate_locked=False,physical_device_verified=False)
for path in ['tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in','tools/android/packaging/xbmc/build.gradle.in']:r['files'].setdefault(path,{})['after']=hashlib.sha256((root/'shell-kodi'/path).read_bytes()).hexdigest()
f.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
