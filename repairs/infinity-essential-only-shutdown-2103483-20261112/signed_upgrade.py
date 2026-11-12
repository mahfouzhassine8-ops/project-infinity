#!/usr/bin/env python3
"""Original-signed84 -> repair86 -> forward87, install-only synthetic retention.

No application start, shutdown, native injection, uninstall, reset or user device.
"""
import argparse,hashlib,importlib.util,json,os,re,sys,traceback
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SELECTION=HERE/'SIGNED-UPGRADE-SELECTION.json';FEATURE='essential-only-signed-upgrade-recovery';BRANCH='work/infinity-essential-only-shutdown-2103483-20261112'
OLD=ROOT/'repairs/infinity-core-outcomes-qa-2103483-20261112/signed_install.py'
spec=importlib.util.spec_from_file_location('retained_install_only',OLD);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
require=old.require;sha=old.sha;save=old.save

def selected():
 r=json.loads(SELECTION.read_text());require(r.get('enabled') is True,'DISABLED_UNTIL_ACTUAL_SIGNED_PAIR')
 require(r['feature']==FEATURE and r['branch']==BRANCH and r['install_only'] is True and r['synthetic_data_only'] is True and all(r[n] is False for n in ('application_tests','shutdown_tests','native_injection','owner_device')),'EXACT_INSTALL_ONLY_SCOPE')
 require(r['packages']['baseline']['versionCode']==2103484 and r['packages']['repair']['versionCode']==2103486 and r['packages']['recovery']['versionCode']==2103487,'UNUSED_FORWARD_PAIR_AND_INSTALLED_DIAGNOSTIC')
 previous=json.loads((OLD.parent/'SIGNED-INSTALL-SELECTION.json').read_text())
 require(r['packages']['baseline']['artifact']==previous['candidate'] and r['packages']['baseline']['APK_sha256']==previous['candidate_APK_sha256'],'EXACT_ORIGINAL_SIGNED84')
 require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and os.environ.get('SELECTED_FEATURE')==FEATURE and os.environ.get('AUTHORIZED_SCOPE')=='Original signed84 to repair86 and forward87 install-over; synthetic data retention only; no launch or Close','EXACT_MANUAL_INSTALL_ONLY_ROUTE')
 require(old.subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==os.environ['SELECTED_SOURCE'],'EXACT_TEST_SOURCE')
 for n,h in r['source_bindings'].items():require(sha(ROOT/n)==h,'UNCHANGED_TEST_SOURCE:'+n)
 return r

def fetch(out):
 r=selected();base,tools=old.helpers();require(not out.exists(),'FRESH_INTAKE')
 for role,pin in r['packages'].items():
  require(pin['artifact']['workflow_id']==397702717,'ONLY_ORIGINAL_SIGNER')
  tools['artifact'](pin['artifact'],out/role)
 save(out/'FETCH.json',dict(selection_sha256=sha(SELECTION),source=os.environ['SELECTED_SOURCE']))

def stage(inputs,sdk):
 r=selected();base,tools=old.helpers();f=json.loads((inputs/'FETCH.json').read_text());require(f==dict(selection_sha256=sha(SELECTION),source=os.environ['SELECTED_SOURCE']),'FROZEN_INTAKE')
 paths={};payloads={};sdk_fields={}
 for role,pin in r['packages'].items():
  root=inputs/role;require(sha(root/'artifact.zip')==pin['artifact']['sha256'],'WHOLE_AUTHENTICATED_ARTIFACT')
  apk=tools['one'](root/'files','Infinity-'+str(pin['versionCode'])+'-Combined-Original-Signer.apk');require(sha(apk)==pin['APK_sha256'],'EXACT_APK:'+role)
  text=base.command([sdk/'build-tools/35.0.0/apksigner','verify','--verbose','--print-certs',apk],timeout=60)
  require(re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)',text)==[old.CERT],'SOLE_PERMANENT_CERTIFICATE')
  for v in ('v1','v2','v3'):require(any(x.startswith('Verified using '+v+' scheme') and x.endswith(': true') for x in text.splitlines()),'SIGNATURE:'+v)
  (inputs/(role+'-SIGNATURE.txt')).write_text(text)
  badging=base.command([sdk/'build-tools/35.0.0/aapt','dump','badging',apk],timeout=60);(inputs/(role+'-BADGING.txt')).write_text(badging)
  require(re.search(r"^package: name='"+re.escape(old.PACKAGE)+r"' versionCode='"+str(pin['versionCode'])+"'",badging,re.M),'ACTUAL_PACKAGE_VERSION')
  sdk_fields[role]=old.sdk_contract(badging)
  with ZipFile(apk) as z:
   payloads[role]=old.payload(z);require(payloads[role][old.LIB]==pin['native_sha256'],'EXACT_NATIVE')
   require(z.read('assets/experience-component-updates.properties')==('infinity.last_updated_in='+str(pin['versionCode'])+'\ncobra.last_updated_in=2103445\n').encode(),'ONLY_INFINITY_LABEL_ADVANCES')
  paths[role]=str(apk.resolve())
 for role in ('repair','recovery'):
  require(sdk_fields[role]==sdk_fields['baseline'] and set(payloads[role])==set(payloads['baseline']),'SAME_SDK_AND_COMPLETE_PAYLOAD')
  require({n for n,v in payloads[role].items() if v!=payloads['baseline'][n]}==old.CHANGES,'ONLY_NATIVE_AND_REQUIRED_VERSION_MEMBERS')
 save(inputs/'INTAKE.json',dict(status='PASS_ORIGINAL_SIGNED_INPUTS_ONLY',paths=paths,selection_sha256=sha(SELECTION),certificate_sha256=old.CERT))
 return r,base,tools,paths

def run(inputs,sdk,out):
 require(not out.exists(),'FRESH_RESULTS');r,base,tools,paths=stage(inputs,sdk);out.mkdir(parents=True)
 report=dict(status='RUNNING',scope=FEATURE,source=os.environ['SELECTED_SOURCE'],application_launched=False,shutdown='NOT_RUN',native_runtime='NOT_RUN',native_injection=False,real_userdata='NOT_RUN',Fold='NOT_RUN',steps=[]);device=None
 try:
  # Integrity hashing of a 330 MB APK/large native image is a file read,
  # not a UI or shutdown deadline. The functional run's final 12-second
  # hash command timed out after successful relaunch. Retain all exact
  # hashes; give only these read commands a bounded 120-second budget.
  class IntegrityDevice(base.Device):
   def shell(self,*args,timeout=12,check=True):
    if args and args[0]=='sha256sum':timeout=max(timeout,120)
    return super().shell(*args,timeout=timeout,check=check)
  device=IntegrityDevice(out,sdk);report['environment']=base.environment(device,out);require(not device.shell('pm','list','packages',old.PACKAGE).strip(),'NEW_DISPOSABLE_VM')
  base.root_reconnect(device,out)
  require(device.adb('install','--no-streaming',paths['baseline'],timeout=300).strip().endswith('Success'),'SIGNED84_INSTALL')
  pin=r['packages']['baseline'];before=old.installed(device,tools,pin['versionCode'],pin['APK_sha256'],pin['native_sha256']);sentinels,original=old.seed(device,before,out);report['baseline']=before;report['synthetic_before']=original
  for role in ('repair','recovery'):
   old.no_application(device);result=device.adb('install','-r','--no-streaming',paths[role],timeout=300);require(result.strip().endswith('Success'),'ORDINARY_INSTALL_OVER:'+role)
   pin=r['packages'][role];after=old.installed(device,tools,pin['versionCode'],pin['APK_sha256'],pin['native_sha256']);require(after['UID']==before['UID'] and after['data_directory']==before['data_directory'],'UID_AND_DATA_DIRECTORY_PRESERVED')
   measured=old.snapshot(device,sentinels);require(measured==original,'SYNTHETIC_BYTES_AND_OWNERSHIP_PRESERVED:'+role);old.no_application(device)
   report['steps'].append(dict(role=role,installed=after,sentinels=measured,passed=True));save(out/'SIGNED-UPGRADE-RECOVERY.json',report)
  report['status']='PASS_ORIGINAL_SIGNED84_REPAIR86_FORWARD87_INSTALL_OVER_SYNTHETIC_RETENTION_NO_APP_LAUNCH'
 except BaseException as error:report.update(status='FAIL',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
 finally:
  save(out/'SIGNED-UPGRADE-RECOVERY.json',report)
  if device:
   try:(out/'package-after.txt').write_text(device.shell('dumpsys','package',old.PACKAGE,check=False))
   except Exception:pass
 print(json.dumps(dict(status=report['status'],error=report.get('error'))));require(report['status'].startswith('PASS_'),'INSTALL_OVER_OR_RETENTION_FAILED')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=('gate','fetch','stage','run'));p.add_argument('--inputs',type=Path);p.add_argument('--sdk',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
 {'gate':selected,'fetch':lambda:fetch(a.out),'stage':lambda:stage(a.inputs,a.sdk),'run':lambda:run(a.inputs,a.sdk,a.out)}[a.mode]()
