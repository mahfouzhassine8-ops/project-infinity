"""Selected signed-package install-over checks only. No app launch/shutdown.

Checks actual PackageManager update/recovery acceptance and stable UID/dataDir/
first-install time. Does not claim physical Fold data or functional acceptance.
"""
from pathlib import Path
from zipfile import ZipFile
import json,os,re,subprocess,sys,traceback
import common_release as c

PACKAGE='com.projectinfinity.kodi'
STAGED=c.ROOT/'movies-cast-install-inputs.json'
OUT=c.ROOT/'movies-cast-install-results'
def prepare():
    c.require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')==c.REPO,'CI_ONLY_INSTALL_CHECK')
    r=c.load(c.HERE/'SIGNED-QA-PAIR.json');c.require(set(r['inputs'])=={'baseline','candidate','recovery'} and r['shutdown'] is False and r['application_startup'] is False,'EXACT_SELECTED_INSTALL_PAIR')
    inventory,cb,_,_,_=c.tools();paths={}
    for kind,row in r['inputs'].items():
        root=c.obtain(row,kind+'-signed-install');version={'baseline':2103486,**c.VERSIONS}[kind]
        apk=c.unique(root,'Infinity-'+str(version)+'-Combined-Original-Signer.apk')
        c.require(c.sha(apk)==row['APK_sha256'],'EXACT_SIGNED_INSTALLER_BYTES');c.signature(apk)
        with ZipFile(apk) as z:
            tree=inventory.manifest_tree(z.read('AndroidManifest.xml'))
            c.require(tree['attributes']['package']['value']==PACKAGE and cb.normalize_manifest(z.read('AndroidManifest.xml'))[1]==version,'EXACT_INSTALL_PACKAGE_AND_VERSION')
        paths[kind]=dict(path=str(apk),sha256=c.sha(apk),versionCode=version)
    c.save(STAGED,dict(schema=1,inputs=paths,certificate_sha256=c.CERT,source=os.environ['GITHUB_SHA']))
def adb(*args):
    permitted=(args[0]=='install' and len(args) in (2,3) and (len(args)==2 or args[1]=='-r')) or (
        args[0]=='shell' and (args[1:]==('getprop','ro.product.cpu.abilist') or args[1:]==('dumpsys','package',PACKAGE)))
    c.require(permitted,'ONLY_NORMAL_INSTALL_AND_READ_ONLY_PACKAGE_QUERIES')
    result=subprocess.run(['adb',*args],capture_output=True,text=True,timeout=240)
    c.require(result.returncode==0,'ACTUAL_PACKAGE_MANAGER_COMMAND_FAILED:'+result.stdout[-1200:]+result.stderr[-1200:])
    return result.stdout
def package():
    text=adb('shell','dumpsys','package',PACKAGE)
    patterns={'uid':r'\b(?:userId|appId)=(\d+)','dataDir':r'\bdataDir=(\S+)',
              'versionCode':r'\bversionCode=(\d+)','firstInstallTime':r'\bfirstInstallTime=([^\r\n]+)'}
    result={}
    for name,pattern in patterns.items():
        m=re.search(pattern,text);c.require(m is not None,'ACTUAL_PACKAGE_FIELD:'+name);result[name]=m.group(1).strip()
    result['versionCode']=int(result['versionCode']);return result
def run():
    OUT.mkdir(exist_ok=False);staged=c.load(STAGED);report=dict(schema=1,status='RUNNING_PACKAGE_INSTALL_ONLY',
        source=os.environ['GITHUB_SHA'],certificate_sha256=c.CERT,application_startup='NOT_SELECTED',
        playback='OWNER_QA_AFTER_SIGNING',shutdown='OWNER_QA_AFTER_SIGNING',Fold_acceptance='NOT_RUN',steps=[])
    try:
        report['emulator_abis']=adb('shell','getprop','ro.product.cpu.abilist').strip()
        prior=adb('shell','dumpsys','package',PACKAGE)
        c.require('versionCode=' not in prior,'FRESH_CI_EMULATOR_NO_EXISTING_OWNER_INSTALLATION')
        baseline=None
        for kind in ('baseline','candidate','recovery'):
            row=staged['inputs'][kind];c.require(c.sha(row['path'])==row['sha256'],'INSTALL_INPUT_CHANGED')
            output=adb('install',row['path']) if kind=='baseline' else adb('install','-r',row['path'])
            c.require('Success' in output,'ANDROID_INSTALL_DID_NOT_SUCCEED');actual=package()
            c.require(actual['versionCode']==row['versionCode'],'INSTALLED_VERSION_MISMATCH')
            if baseline is None:baseline=actual
            else:c.require(all(actual[n]==baseline[n] for n in ('uid','dataDir','firstInstallTime')),'UPDATE_OR_RECOVERY_CHANGED_DATA_OWNER')
            report['steps'].append(dict(kind=kind,status='PASS',APK_sha256=row['sha256'],package=actual))
            c.save(OUT/'INSTALL-OVER-AND-RECOVERY.json',report)
        report.update(status='PASS_ACTUAL_ANDROID_IN_PLACE_INSTALL_AND_FORWARD_RECOVERY',
            data_preservation='PackageManager retained UID, dataDir and firstInstallTime. No owner profile/database opened or modified.',
            data_reset=False,uninstall=False,forced_downgrade=False,application_launch=False)
    except Exception as error:
        report.update(status='FAIL_OR_BLOCKED_INSTALL_ENVIRONMENT',reason=str(error))
        raise
    finally:c.save(OUT/'INSTALL-OVER-AND-RECOVERY.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    c.require(len(sys.argv)==2,'EXACT_INSTALL_CHECK_MODE')
    {'prepare':prepare,'run':run}[sys.argv[1]]()
