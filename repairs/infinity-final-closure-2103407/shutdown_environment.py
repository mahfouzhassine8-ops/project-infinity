"""Read-only disposable fixture evidence; never executes or approves a child."""
import hashlib
import json
import os
from pathlib import Path
import stat

FILES=('addon.xml','resources/lib/runner.py','resources/lib/version_check/service.py','resources/lib/version_check/distro/distro.py')


def collect(path_value,code_root):
    if len(path_value)>8192 or len(path_value.split(':'))>64:raise ValueError('Unexpected environment path size')
    rows=[]
    for directory in path_value.split(':'):
        row={'directory':directory,'candidate':directory+'/lsb_release'}
        for name,path in (('directory',directory),('candidate',row['candidate'])):
            observation={}
            try:
                value=os.lstat(path);observation.update(exists=True,mode=oct(value.st_mode),uid=value.st_uid,
                    directory=stat.S_ISDIR(value.st_mode),symlink=stat.S_ISLNK(value.st_mode))
            except OSError as error:observation.update(exists=False,errno=error.errno)
            observation['execute_access']=os.access(path,os.X_OK)
            try:observation['readonly_mount']=bool(os.statvfs(path).f_flag & os.ST_RDONLY)
            except OSError as error:observation['statvfs_errno']=error.errno
            row[name+'_observation']=observation
        rows.append(row)
    sources={}
    for name in FILES:
        path=Path(code_root)/name
        try:
            size=path.stat().st_size
            if size>1024*1024:raise ValueError('Oversized VersionCheck source')
            sources[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':size}
        except OSError as error:sources[name]={'errno':error.errno}
    return dict(schema=1,PATH=path_value,search=rows,versioncheck_source=sources,
        child_execution_attempted=False,child_readonly_or_durable_proof=False,
        service_changed=False,save_authorization_granted=False)


def snapshot(output):
    import xbmcaddon,xbmcvfs
    addon=xbmcaddon.Addon('service.xbmc.versioncheck')
    value=collect(os.environ.get('PATH',''),xbmcvfs.translatePath(addon.getAddonInfo('path')))
    value['versioncheck_version']=addon.getAddonInfo('version')
    value['versioncheck_settings']={key:addon.getSetting(key) for key in ('versioncheck_enable','upgrade_apt')}
    Path(output).write_text(json.dumps(value,indent=2)+'\n')
