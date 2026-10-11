# -*- coding: utf-8 -*-
import os, re, json, time, zipfile, shutil, urllib.request, urllib.parse, gzip, io, hashlib, sqlite3, sys
import xbmc, xbmcgui, xbmcvfs, xbmcaddon
import xml.etree.ElementTree as ET
import uuid
import tempfile
from khc_safety import repository_info, replace_repository, snapshot_file

ADDON_ID='script.kodihealthcenter'
PROFILE=xbmcvfs.translatePath('special://profile/addon_data/%s/' % ADDON_ID)
HOME=xbmcvfs.translatePath('special://home/')
ADDONS=xbmcvfs.translatePath('special://home/addons/')
LOG=xbmcvfs.translatePath('special://logpath/kodi.log')
OLDLOG=xbmcvfs.translatePath('special://logpath/kodi.old.log')
TEMP=xbmcvfs.translatePath('special://temp/')
PACKAGES=xbmcvfs.translatePath('special://home/addons/packages/')
BACKUPS=os.path.join(PROFILE,'repair_backups')
CONFIG_BACKUPS=os.path.join(PROFILE,'config_backups')
UNDO_FILE=os.path.join(PROFILE,'last_action.json')
SCAN_STATE_FILE=os.path.join(PROFILE,'last_scan_issues.json')
SCAN_RESULT_FILE=os.path.join(PROFILE,'last_scan_results.json')
os.makedirs(PROFILE, exist_ok=True)

NOISY=('Repository add-on ','Window Translator: Can\'t find window','Direct texture file loading failed','GetDirectory - Error getting')
CRASH_PATTERNS=('segmentation fault','fatal error','abort','crashed','unhandled exception','python callback/script returned','exception thrown')


# Custom tweak remnants that Health Center can safely identify after uninstall.
# Matching is deliberately conservative so normal build/skin/add-on data is not removed.
TWEAK_KEYWORDS=('fold','performance','easy.switch','easyswitch','resume.manager','resumemanager','playback.resumer','background.playback','kodihelper','kodi.helper')



def _known_tweak_leftovers():
    root=xbmcvfs.translatePath('special://profile/addon_data/')
    found=[]
    try:
        for d in os.listdir(root):
            low=d.lower()
            if d==ADDON_ID or installed(d):
                continue
            if any(k in low for k in TWEAK_KEYWORDS):
                p=os.path.join(root,d)
                if os.path.isdir(p): found.append((d,p,folder_size(p)))
    except: pass
    return found


def fmt_bytes(n):
    try: n=float(n)
    except: return '0 B'
    for u in ('B','KB','MB','GB','TB'):
        if n < 1024 or u=='TB': return ('%.1f %s' % (n,u)) if u!='B' else ('%d B' % n)
        n/=1024.0

def read_text(path, limit=4*1024*1024):
    try:
        with open(path,'r',encoding='utf-8',errors='replace') as f: return f.read(limit)
    except: return ''

def folder_size(path):
    total=0
    if not os.path.isdir(path): return 0
    for base,dirs,fs in os.walk(path):
        for fn in fs:
            try: total+=os.path.getsize(os.path.join(base,fn))
            except: pass
    return total

def jsonrpc(method, params=None):
    req={'jsonrpc':'2.0','id':1,'method':method}
    if params is not None: req['params']=params
    try: return json.loads(xbmc.executeJSONRPC(json.dumps(req)))
    except: return {}

def installed(addonid):
    r=jsonrpc('Addons.GetAddonDetails',{'addonid':addonid,'properties':['enabled','name','version','path']})
    return r.get('result',{}).get('addon')

def _save_undo(action, addonid=None, previous=None):
    try:
        with open(UNDO_FILE,'w',encoding='utf-8') as f: json.dump({'action':action,'addonid':addonid,'previous':previous,'time':time.time()},f)
    except: pass

def set_enabled(addonid, enabled, record=True):
    wanted = bool(enabled)
    previous = addon_enabled(addonid) if record else None
    r = jsonrpc('Addons.SetAddonEnabled', {'addonid': addonid, 'enabled': wanted})
    if not isinstance(r, dict) or r.get('result') != 'OK' or 'error' in r:
        return False
    ok = addon_enabled(addonid) is wanted
    if ok and record and previous is not None and previous != wanted:
        _save_undo('enabled_state', addonid, previous)
    return ok

def addon_enabled(addonid):
    a = installed(addonid)
    if not isinstance(a, dict) or not isinstance(a.get('enabled'), bool):
        return None
    return a['enabled']

def repository_addons():
    repos=[]
    if not os.path.isdir(ADDONS): return repos
    for d in sorted(os.listdir(ADDONS)):
        if not d.startswith('repository.'): continue
        a=installed(d)
        if a:
            repos.append({'id':d,'name':a.get('name') or d,'version':a.get('version') or '?','enabled':bool(a.get('enabled',False))})
    return repos

def repository_backups():
    out=[]
    if not os.path.isdir(BACKUPS): return out
    for fn in sorted(os.listdir(BACKUPS), reverse=True):
        if not (fn.startswith('repository.') and fn.endswith('.zip')): continue
        # backup names are <addonid>-YYYYmmdd-HHMMSS.zip
        aid=re.sub(r'-\d{8}-\d{6}\.zip$','',fn)
        out.append({'id':aid,'file':fn,'path':os.path.join(BACKUPS,fn)})
    return out

def restore_backup(item):
    aid, zpath = item.get('id'), item.get('path')
    info = _repository_zip_info(zpath) if zpath and os.path.isfile(zpath) else None
    if not info or info['id'] != aid:
        xbmcgui.Dialog().ok('Restore failed', 'Backup identity or archive validation failed. Nothing was changed.')
        return
    if installed(aid) or os.path.lexists(os.path.join(ADDONS, aid)):
        xbmcgui.Dialog().ok('Already installed', aid + ' already exists; it was not overwritten.')
        return
    return _install_repository_zip(zpath)

def repository_details(repo):
    aid=repo['id']; issue_titles=[]
    for x in detect_issues():
        if x.get('addonid')==aid: issue_titles.append(x.get('title',''))
    xml=read_text(os.path.join(ADDONS,aid,'addon.xml'),512*1024)
    insecure=bool(re.search(r'<(info|checksum|datadir)[^>]*>\s*http://',xml,re.I))
    msg='ID: %s\nVersion: %s\nStatus: %s' % (aid,repo.get('version','?'),'Enabled' if repo.get('enabled') else 'Disabled')
    if insecure: msg+='\nTransport warning: HTTP source detected'
    if issue_titles: msg+='\n\nCurrent Health Center flags:\n- '+'\n- '.join(issue_titles[:8])
    else: msg+='\n\nNo current Health Center issue is tied to this repository.'
    xbmcgui.Dialog().ok(repo.get('name') or aid,msg)

def bulk_repository_state(enabled):
    repos=repository_addons()
    if not repos:
        xbmcgui.Dialog().ok('Repository Manager','No installed repositories were found.')
        return
    target='enable' if enabled else 'disable'
    if not enabled:
        msg=('Disable ALL %d installed repositories?\n\n'
             'They will remain installed and can be re-enabled at any time.\n\n'
             'This may temporarily stop add-on updates and dependency installs until repositories are enabled again.') % len(repos)
        if not xbmcgui.Dialog().yesno('Disable all repositories?',msg):
            return
    else:
        if not xbmcgui.Dialog().yesno('Enable all repositories?',
            'Enable ALL %d installed repositories?\n\nKodi will be allowed to use them for updates and dependencies again.' % len(repos)):
            return
    changed=0; already=0; failed=[]
    for r in repos:
        if bool(r.get('enabled'))==bool(enabled):
            already+=1
            continue
        if set_enabled(r['id'],enabled,record=False): changed+=1
        else: failed.append(r['id'])
    lines=['%s complete.' % ('Enable all' if enabled else 'Disable all'),
           '', 'Changed: %d' % changed, 'Already %s: %d' % ('enabled' if enabled else 'disabled',already)]
    if failed:
        lines+=['Failed: %d' % len(failed),'','Could not change:','- '+'\n- '.join(failed[:12])]
    xbmcgui.Dialog().ok('Repository Manager','\n'.join(lines))


def repository_manager():
    while True:
        repos=repository_addons(); backups=repository_backups()
        labels=['Enable ALL repositories','Disable ALL repositories']; actions=[('enable_all',None),('disable_all',None)]
        for r in repos:
            state='ENABLED' if r['enabled'] else 'DISABLED'
            labels.append('[%s] %s' % (state,r['name']))
            actions.append(('repo',r))
        if backups:
            labels.append('Restore a removed repository from Health Center backup')
            actions.append(('restore',None))
        labels.append('Done'); actions.append(('done',None))
        i=xbmcgui.Dialog().select('Repository Manager',labels)
        if i<0 or actions[i][0]=='done': return
        kind,obj=actions[i]
        if kind=='enable_all':
            bulk_repository_state(True); continue
        if kind=='disable_all':
            bulk_repository_state(False); continue
        if kind=='restore':
            bs=repository_backups()
            if not bs: xbmcgui.Dialog().ok('Restore','No repository backups were found.'); continue
            j=xbmcgui.Dialog().select('Restore repository backup',[b['id']+' — '+b['file'] for b in bs]+['Cancel'])
            if j<0 or j>=len(bs): continue
            restore_backup(bs[j]); continue
        r=obj; aid=r['id']
        opts=['View details']
        opts.append('Disable repository' if r['enabled'] else 'Enable repository')
        opts+=['Remove repository (backup first)','Cancel']
        j=xbmcgui.Dialog().select(r['name'],opts)
        if j<0 or opts[j]=='Cancel': continue
        choice=opts[j]
        if choice=='View details': repository_details(r)
        elif choice.startswith('Disable'):
            if xbmcgui.Dialog().yesno('Disable repository?', aid+' will remain installed and can be re-enabled at any time.\n\nContinue?'):
                ok=set_enabled(aid,False)
                xbmcgui.Dialog().notification('Kodi Health Center','Repository disabled' if ok else 'Could not disable',xbmcgui.NOTIFICATION_INFO if ok else xbmcgui.NOTIFICATION_ERROR,3500)
        elif choice.startswith('Enable'):
            ok=set_enabled(aid,True)
            xbmcgui.Dialog().notification('Kodi Health Center','Repository enabled' if ok else 'Could not enable',xbmcgui.NOTIFICATION_INFO if ok else xbmcgui.NOTIFICATION_ERROR,3500)
        elif choice.startswith('Remove'):
            remove_addon(aid)

def log_lines(include_old=True):
    text=read_text(LOG)
    if include_old:
        text += "\n" + read_text(OLDLOG)
    return text.splitlines()

def old_log_lines():
    return read_text(OLDLOG).splitlines()

def detect_issues(lines=None):
    # Actionable issues should be based on the CURRENT log plus live Kodi state.
    # kodi.old.log is history and must never make a removed add-on look active.
    if lines is None:
        lines=log_lines(include_old=False)
    issues=[]; seen=set()
    def add(key, title, detail, addonid=None, repair=None, severity='warning'):
        if key in seen:return
        seen.add(key); issues.append({'key':key,'title':title,'detail':detail,'addonid':addonid,'repair':repair,'severity':severity})
    for line in lines:
        m=re.search(r"Unknown addon id '([^']+)'", line)
        if m:
            aid=m.group(1)
            # xbmcaddon.Addon(id) is also commonly used as an OPTIONAL capability
            # probe. Do not tell the user to install an arbitrary add-on merely
            # because a runtime lookup failed. Promote it to an actionable missing
            # dependency only when an installed addon.xml declares that ID as a
            # non-optional dependency. The raw log line remains exported either way.
            if not installed(aid):
                users=dependency_users(aid, required_only=True)
                if users:
                    add(
                        'missing:'+aid,
                        'Missing required dependency: '+aid,
                        'Required by installed add-on(s): '+', '.join(users[:8])+'.',
                        aid,None,'error')
        m=re.search(r'Repository add-on ([\w.\-]+) does not have any directory matching ([\d.]+)',line)
        if m:
            aid,ver=m.groups(); add('repo:'+aid,'Incompatible repository: '+aid,'Repository has no directory matching Kodi '+ver+'.',aid,'addon','error')
        if 'plugin.video.themoviedb.helper' in line and 'GetDirectory - Error getting' in line:
            tmdb_base=xbmcvfs.translatePath('special://profile/addon_data/plugin.video.themoviedb.helper/')
            needed=('log_tagger','log_library','timer_report')
            if any(not os.path.isdir(os.path.join(tmdb_base,n)) for n in needed):
                add('tmdbdirs','TMDb Helper missing working folders','Health Center can recreate log_tagger, log_library and timer_report.','plugin.video.themoviedb.helper','tmdbdirs')
    # insecure repository URLs by addon.xml, no network requests
    if os.path.isdir(ADDONS):
        for d in os.listdir(ADDONS):
            if not d.startswith('repository.'): continue
            xml=read_text(os.path.join(ADDONS,d,'addon.xml'), 512*1024)
            if re.search(r'<(info|checksum|datadir)[^>]*>\s*http://',xml,re.I):
                add('http:'+d,'Insecure HTTP repository: '+d,'This repository contains an unencrypted HTTP source.',d,'addon')
    return issues

def dependency_users(aid, required_only=False):
    """Return installed add-ons that actually declare *aid* in <requires>.

    required_only=True excludes optional capability imports. This avoids treating
    xbmcaddon.Addon(id) probes and optional integrations as broken dependencies.
    """
    users=[]
    if not os.path.isdir(ADDONS): return users
    for d in os.listdir(ADDONS):
        xml_path=os.path.join(ADDONS,d,'addon.xml')
        if not os.path.isfile(xml_path):
            continue
        try:
            r=ET.parse(xml_path).getroot()
            req=r.find('requires')
            if req is None:
                continue
            for imp in req.findall('import'):
                if imp.attrib.get('addon') != aid:
                    continue
                optional=str(imp.attrib.get('optional','false')).strip().lower() in ('true','1','yes')
                if required_only and optional:
                    continue
                users.append(d)
                break
        except Exception:
            # Fail closed for repair decisions: malformed metadata must not invent
            # a dependency relationship.
            continue
    return sorted(set(users))

def choose_action(issue):
    # v1.8.4 safety: the action is derived from the selected issue object itself.
    # Missing dependencies are diagnostic-only; we never remove/disable something else for them.
    aid=issue.get('addonid'); repair=issue.get('repair')
    title=issue.get('title','Issue')
    if issue.get('key','').startswith('missing:'):
        users=dependency_users(aid)
        msg='Missing: %s\n\n' % aid
        if users:
            msg+='Installed add-ons declaring this dependency:\n- '+'\n- '.join(users[:12])
        else:
            msg+='No installed addon.xml currently declares this dependency. The reference may be stale or generated at runtime.'
        msg+='\n\nYou can open Add-on Dependencies to look for a repair using Kodi\'s configured repositories.'
        if xbmcgui.Dialog().yesno('Dependency diagnosis',msg+'\n\nOpen dependency repair options now?'):
            dependency_repair_menu({'id':aid,'version':'','optional':False})
        return
    if repair=='tmdbdirs':
        if xbmcgui.Dialog().yesno('Repair TMDb Helper folders?', 'Selected issue:\n'+title+'\n\nCreate/verify the three working folders?'):
            repair_tmdb()
        return
    if aid and installed(aid):
        is_repo=aid.startswith('repository.')
        enabled=addon_enabled(aid)
        opts=[]
        if is_repo:
            opts.append('Disable repository' if enabled else 'Enable repository')
            opts.append('View repository details')
            opts.append('Remove repository (backup first)')
        else:
            opts.append('Disable add-on' if enabled else 'Enable add-on')
            opts.append('Remove add-on (backup first)')
        opts.append('Cancel')
        idx=xbmcgui.Dialog().select(title+' — choose action',opts)
        if idx<0 or opts[idx]=='Cancel': return
        action=opts[idx]
        if action=='View repository details':
            a=installed(aid) or {}
            repository_details({'id':aid,'name':a.get('name') or aid,'version':a.get('version') or '?','enabled':bool(a.get('enabled',False))})
            return
        if action.startswith('Enable'):
            ok=set_enabled(aid,True); xbmcgui.Dialog().notification('Kodi Health Center','Enabled' if ok else 'Could not enable',xbmcgui.NOTIFICATION_INFO if ok else xbmcgui.NOTIFICATION_ERROR,3500); return
        if action.startswith('Disable'):
            if not xbmcgui.Dialog().yesno('Confirm Disable', 'Selected issue:\n'+title+'\n\nTarget:\n'+aid+'\n\nThis keeps it installed so you can re-enable it later.\n\nContinue?'): return
            ok=set_enabled(aid,False); xbmcgui.Dialog().notification('Kodi Health Center','Disabled' if ok else 'Could not disable',xbmcgui.NOTIFICATION_INFO if ok else xbmcgui.NOTIFICATION_ERROR,3500); return
        if action.startswith('Remove'):
            if not xbmcgui.Dialog().yesno('Confirm Remove', 'Selected issue:\n'+title+'\n\nTarget:\n'+aid+'\n\nA backup will be created first. Continue?'): return
            remove_addon(aid, confirmed=True)
        return
    xbmcgui.Dialog().ok('No automatic repair',title+'\n\nHealth Center will not make a change for this issue automatically.')

def repair_tmdb():
    base=xbmcvfs.translatePath('special://profile/addon_data/plugin.video.themoviedb.helper/')
    made=[]
    for name in ('log_tagger','log_library','timer_report'):
        p=os.path.join(base,name)
        try: os.makedirs(p,exist_ok=True); made.append(name)
        except: pass
    xbmcgui.Dialog().ok('Repair complete','Created/verified:\n'+', '.join(made))

def remove_addon(aid, confirmed=False):
    if aid==ADDON_ID:
        xbmcgui.Dialog().ok('Blocked','Health Center will not remove itself.'); return
    a=installed(aid)
    if not a: xbmcgui.Dialog().ok('Not installed',aid+' is not currently installed.'); return
    if (not confirmed) and (not xbmcgui.Dialog().yesno('Remove '+aid+'?','A backup ZIP will be created first. This removes the installed add-on folder. Add-on settings are left intact.')):
        return
    path=a.get('path') or os.path.join(ADDONS,aid)
    path=xbmcvfs.translatePath(path)
    try:
        os.makedirs(BACKUPS,exist_ok=True)
        stamp=time.strftime('%Y%m%d-%H%M%S'); zpath=os.path.join(BACKUPS,aid+'-'+stamp+'.zip')
        with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
            for base,dirs,fs in os.walk(path):
                for fn in fs:
                    fp=os.path.join(base,fn); z.write(fp,os.path.relpath(fp,os.path.dirname(path)))
        set_enabled(aid,False); shutil.rmtree(path)
        xbmc.executebuiltin('UpdateLocalAddons')
        xbmcgui.Dialog().ok('Removed',aid+' was removed.\nBackup:\n'+zpath)
    except Exception as e: xbmcgui.Dialog().ok('Remove failed',str(e))


def _load_last_scan_keys():
    try:
        with open(SCAN_STATE_FILE,'r',encoding='utf-8') as f:
            data=json.load(f)
        if isinstance(data,list):
            return set(str(x) for x in data)
    except:
        pass
    return set()

def _save_scan_keys(keys):
    try:
        with open(SCAN_STATE_FILE,'w',encoding='utf-8') as f:
            json.dump(sorted(set(keys)),f)
    except:
        pass

def _dependency_name_from_key(key):
    if key.startswith('missing:'):
        return key.split(':',1)[1]
    return key

def _runtime_findings(lines):
    """Return (active, recovered) deduplicated runtime signals."""
    text_lines=[str(line) for line in lines]
    low_lines=[line.lower() for line in text_lines]
    rules = [
        ('skin-window-collision','error','Infinity skin custom-window registration collision',
         lambda low: 'id already in use for custom window' in low,
         'Kodi reported duplicate/invalid custom-window registration. Responsive skin and fallback profiles may both expose the same custom window ID.'),
        ('addons-db-too-old','warning','Legacy Add-ons database could not be upgraded',
         lambda low: "can't update database addons" in low and "too old" in low,
         'Kodi reported an Addons database generation that is too old to upgrade in place.'),
        ('keymap-invalid-action','warning','Keymap contains an invalid action',
         lambda low: 'keymapping error:' in low,
         'Kodi rejected at least one configured keymap action.'),
        ('tmdb-helper-nameerror','error','TMDb Helper runtime NameError',
         lambda low: "name 'enumerate' is not defined" in low,
         "TMDb Helper logged a Python NameError involving enumerate. This is an add-on runtime error, not a Kodi process crash by itself."),
    ]
    active=[]
    recovered=[]
    for key,severity,title,predicate,detail in rules:
        match_idx=[i for i,low in enumerate(low_lines) if predicate(low)]
        if not match_idx:
            continue
        matches=[text_lines[i] for i in match_idx]
        base={'key':key,'severity':severity,'title':title,'detail':detail,
              'count':len(matches),'samples':matches[:5]}

        # Custom-window collisions are load-time events. If a newer Infinity
        # skin load occurs after the last collision and no later collision is
        # logged, the old entries describe the superseded skin load rather
        # than the currently active skin. Preserve them as recovered evidence.
        if key=='skin-window-collision':
            last_collision=max(match_idx)
            later_skin_loads=[
                i for i in range(last_collision+1,len(low_lines))
                if ('load skin from:' in low_lines[i]
                    and 'skin.infinity.diggz' in low_lines[i])
            ]
            if later_skin_loads:
                recovery_i=later_skin_loads[-1]
                base.update({
                    'detail':'Earlier custom-window collisions predate a later Infinity skin load. No collision recurred after that newer load.',
                    'recovered':True,
                    'recovery_sample':text_lines[recovery_i],
                })
                recovered.append(base)
                continue

        active.append(base)

    auth_rules=[
        ('auth-bad-token','warning','Add-on authentication token error','bad_token',
         ('real debrid token refreshed','token refreshed successfully'),
         'A provider reported bad_token, then a later token-refresh success marker appeared in the same current log.'),
        ('auth-invalid-grant','warning','Add-on authentication grant error','invalid_grant',
         ('background trakt refresh succeeded','trakt token refreshed successfully'),
         'A provider reported invalid_grant, then a later Trakt refresh success marker appeared in the same current log.'),
    ]
    from khc_lifecycle import scope
    for key,severity,title,error_token,success_tokens,recovered_detail in auth_rules:
        owners={scope(text_lines[i]) for i,low in enumerate(low_lines) if error_token in low}
        for owner in sorted(owners,key=lambda x:x or ''):
            idx=[i for i,low in enumerate(low_lines) if error_token in low and scope(text_lines[i])==owner]
            last_error=max(idx)
            later_success=next((i for i in range(last_error+1,len(low_lines)) if owner and scope(text_lines[i])==owner and any(tok in low_lines[i] for tok in success_tokens)),None)
            base={'key':key+':'+(owner or 'unscoped'),'severity':severity,'title':title,'count':len(idx),'samples':[text_lines[i] for i in idx[:5]],'owner':owner}
            if later_success is not None:
                base.update({'detail':recovered_detail,'recovered':True,'recovery_sample':text_lines[later_success],'resolved_samples':[text_lines[i] for i in idx]})
                recovered.append(base)
            else:
                base.update({'detail':'No later matching verification for this add-on authorization operation.','recovered':False})
                active.append(base)
    return active,recovered




# ---- Authorization Health 2.5.15 --------------------------------------------
AUTH_OWNER_ID='script.module.acctmgr'
AUTH_SURFACE_ID='script.infinity.authsurface'
AUTH_MASTER_FIELDS={
    'Trakt':('trakt.token','trakt.refresh','trakt.expires','trakt.username'),
    'Real-Debrid':('realdebrid.token','realdebrid.refresh','realdebrid.username'),
    'Premiumize':('premiumize.token','premiumize.username'),
    'All-Debrid':('alldebrid.token','alldebrid.username'),
    'TorBox':('torbox.token','torbox.acct_id','torbox.auth_status'),
    'OffCloud':('offcloud.token',),
    'Easynews':('easynews.username','easynews.password'),
    'MDBList':('mdblist.apikey','mdblist.username'),
}
TRAKT_TARGETS=[
    ('TMDb Helper','plugin.video.themoviedb.helper'),
    ('Umbrella','plugin.video.umbrella'),
    ('POV','plugin.video.pov'),
    ('Fen Light','plugin.video.fenlight'),
    ('Seren','plugin.video.seren'),
    ('The Crew','plugin.video.thecrew'),
    ('SALTS','plugin.video.salts'),
    ('Trakt Addon','script.trakt'),
    ('The Gears', 'plugin.video.gears'),
    ('Red Light', 'plugin.video.redlight'),
    ('Genocide', 'plugin.video.genocide'),
    ('Shadow', 'plugin.video.shadow'),
    ('Ghost', 'plugin.video.ghost'),
    ('The Chains', 'plugin.video.thechains'),
    ('Homelander', 'plugin.video.homelander'),
    ('Nightwing', 'plugin.video.nightwing'),
    ('Jokers Absolution', 'plugin.video.absolution'),
    ('Scrubs V2', 'plugin.video.scrubsv2'),
    ('Gratis Red', 'plugin.video.gratisred'),
]

def _addon_obj(addonid):
    try:
        return xbmcaddon.Addon(addonid) if installed(addonid) else None
    except Exception:
        return None

def _setting_ids_for(addonid):
    out=[]
    a=installed(addonid)
    path=(a or {}).get('path') if isinstance(a,dict) else None
    if not path:
        try: path=xbmcaddon.Addon(addonid).getAddonInfo('path')
        except Exception: path=None
    if not path: return out
    local=xbmcvfs.translatePath(path)
    for rel in ('resources/settings.xml','settings.xml'):
        p=os.path.join(local,rel)
        if not os.path.isfile(p): continue
        try:
            r=ET.parse(p).getroot()
            for node in r.iter('setting'):
                sid=node.attrib.get('id','')
                low=sid.lower()
                if sid and 'trakt' in low and any(x in low for x in ('token','refresh','auth','authorization')):
                    if not any(x in low for x in ('client','secret','api')) and sid not in out:
                        out.append(sid)
        except Exception:
            pass
    return out

def _trakt_setting_candidates(addonid):
    explicit={
        'plugin.video.themoviedb.helper':['trakt_token'],
        'plugin.video.umbrella':['trakt.user.token','trakt.refreshtoken'],
        'plugin.video.pov':['trakt.token','trakt.refresh'],
        'plugin.video.fenlight':['trakt.token','trakt.refresh'],
        'plugin.video.seren':['trakt.auth','trakt.refresh'],
        'plugin.video.thecrew':['trakt.token','trakt.refresh'],
        'plugin.video.salts':['trakt_access_token','trakt_refresh_token'],
        'script.trakt':['authorization','trakt_token','trakt_refresh_token'],
        'plugin.video.gears':['trakt.token', 'trakt.refresh'],
        'plugin.video.redlight':['trakt.token', 'trakt.refresh'],
        'plugin.video.genocide':['trakt.token', 'trakt.refresh'],
        'plugin.video.shadow':['trakt_access_token', 'trakt_refresh_token'],
        'plugin.video.ghost':['trakt_access_token', 'trakt_refresh_token'],
        'plugin.video.thechains':['trakt_access_token', 'trakt_refresh_token'],
        'plugin.video.homelander':['trakt.token', 'trakt.refresh'],
        'plugin.video.nightwing':['trakt.token', 'trakt.refresh'],
        'plugin.video.absolution':['trakt.token', 'trakt.refresh'],
        'plugin.video.scrubsv2':['trakt.token', 'trakt.refresh'],
        'plugin.video.gratisred':['trakt.token', 'trakt.refresh'],
    }
    ids=list(explicit.get(addonid,[]))
    for sid in _setting_ids_for(addonid):
        if sid not in ids: ids.append(sid)
    return ids

def _read_trakt_target(addonid, owner_access='', owner_refresh=''):
    a=_addon_obj(addonid)
    if not a:
        return {'installed':False,'status':'NOT INSTALLED','access_present':False,'refresh_present':False,
                'access_matches_owner':None,'refresh_matches_owner':None,'credential_values_exported':False}
    access=[]; refresh=[]; detected=[]
    for sid in _trakt_setting_candidates(addonid):
        try: value=a.getSetting(sid) or ''
        except Exception: value=''
        if not value: continue
        detected.append(sid)
        low=sid.lower()
        parsed=None
        if value.lstrip().startswith('{'):
            try: parsed=json.loads(value)
            except Exception: parsed=None
        if isinstance(parsed,dict):
            av=parsed.get('access_token') or parsed.get('token') or ''
            rv=parsed.get('refresh_token') or parsed.get('refresh') or ''
            if av: access.append(str(av))
            if rv: refresh.append(str(rv))
        elif 'refresh' in low:
            refresh.append(str(value))
        elif any(x in low for x in ('token','auth','authorization')):
            access.append(str(value))
    access_present=bool(access); refresh_present=bool(refresh)
    access_match=(owner_access in access) if owner_access and access else (False if owner_access and access_present else None)
    refresh_match=(owner_refresh in refresh) if owner_refresh and refresh else (False if owner_refresh and refresh_present else None)
    if access_match is True and refresh_match is True: status='SYNCED'
    elif access_match is True and not refresh_present: status='ACCESS SYNCED / REFRESH UNVERIFIED'
    elif access_match is True and refresh_match is False: status='ACCESS SYNCED / REFRESH MISMATCH'
    elif access_present and access_match is False: status='DIFFERENT AUTHORIZATION'
    elif access_present: status='AUTHORIZATION PRESENT'
    elif addonid in ('plugin.video.fenlight','plugin.video.gears','plugin.video.redlight'):
        status='DATABASE STORAGE / UNVERIFIED'
    else: status='MISSING'
    return {'installed':True,'status':status,'access_present':access_present,'refresh_present':refresh_present,
            'access_matches_owner':access_match,'refresh_matches_owner':refresh_match,
            'credential_fields_detected':len(detected),'credential_values_exported':False,
            'verification_scope':'local_configuration_only','server_authentication_verified':False}

def _am_trakt_sync_list():
    # Do not mistake another service's addon_list JSON for the Trakt selection.
    from pathlib import Path
    from khc_native import read_metadata
    path = Path(xbmcvfs.translatePath('special://profile/addon_data/%s/' % AUTH_OWNER_ID)) / 'trakt_sync_list.json'
    data = read_metadata(path)
    rows = data.get('addon_list', [])
    if not isinstance(rows, list):
        return []
    return list(dict.fromkeys(x for x in rows[:128] if isinstance(x, str) and 0 < len(x) <= 128))

def _latest_marker_state(lines, failures, successes):
    from khc_lifecycle import marker_state
    return marker_state(lines,failures,successes)


def _authorization_health(lines=None):
    lines=log_lines(include_old=False) if lines is None else lines
    owner=_addon_obj(AUTH_OWNER_ID)
    owner_info=installed(AUTH_OWNER_ID) or {}
    selected=_am_trakt_sync_list()
    selected_set=set(selected)
    services=[]; attention=0
    owner_values={}
    for service,fields in AUTH_MASTER_FIELDS.items():
        present={}
        for key in fields:
            try: value=owner.getSetting(key) if owner else ''
            except Exception: value=''
            present[key]=bool(value)
            if service=='Trakt' and key in ('trakt.token','trakt.refresh'): owner_values[key]=value or ''
        if not owner:
            status='OWNER UNAVAILABLE'
        elif service=='Trakt':
            if present.get('trakt.token') and present.get('trakt.refresh'): status='CONFIGURED'
            elif present.get('trakt.token') or present.get('trakt.refresh'): status='PARTIAL / REAUTHORIZE'
            else: status='NOT CONFIGURED'
        elif any(present.values()): status='CONFIGURED'
        else: status='NOT CONFIGURED'
        services.append({'service':service,'status':status,'fields_present':present,'credential_values_exported':False})
        if status in ('PARTIAL / REAUTHORIZE','OWNER UNAVAILABLE'): attention+=1
    trakt_log=_latest_marker_state(lines,('invalid_grant','session not found','re-authorize your trakt'),
                                   ('background trakt refresh succeeded','trakt token refreshed successfully','trakt successfully authorized'))
    rd_log=_latest_marker_state(lines,('bad_token','real-debrid unauthorized'),
                                ('real debrid token refreshed','real-debrid token refreshed','real-debrid auth'))
    if trakt_log=='REFRESH / AUTH FAILURE': attention+=1
    if rd_log=='REFRESH / AUTH FAILURE': attention+=1
    targets=[]
    access=owner_values.get('trakt.token',''); refresh=owner_values.get('trakt.refresh','')
    for display,addonid in TRAKT_TARGETS:
        t=_read_trakt_target(addonid,access,refresh)
        t.update({'name':display,'addon_id':addonid,'selected_in_am_lite_sync':display in selected_set})
        if t['installed'] and t['selected_in_am_lite_sync'] and t['status'] not in ('SYNCED','AUTHORIZATION PRESENT'):
            attention+=1
        targets.append(t)
    return {
        'schema':2,'verification_scope':'local_settings_and_log_markers_only','server_authentication_verified':False,
        'captured_epoch':time.time(),'health_center_version':xbmcaddon.Addon(ADDON_ID).getAddonInfo('version'),
        'owner':{'addon_id':AUTH_OWNER_ID,'installed':bool(owner),'enabled':bool(owner_info.get('enabled',False)) if isinstance(owner_info,dict) else False,
                 'version':owner_info.get('version','') if isinstance(owner_info,dict) else ''},
        'authorization_surface':{'addon_id':AUTH_SURFACE_ID,'installed':bool(installed(AUTH_SURFACE_ID))},
        'services':services,'trakt':{'log_state':trakt_log,'sync_targets_selected':selected,'targets':targets},
        'real_debrid':{'log_state':rd_log},'needs_attention_count':attention,
        'privacy':'Credential values are compared only in memory. No access token, refresh token, API key, password, username or credential fingerprint is exported or logged.'
    }

def _authorization_health_text(h):
    out=['KODI HEALTH CENTER — AUTHORIZATION HEALTH','=========================================',
         'Owner: %s %s' % (h.get('owner',{}).get('addon_id','?'),h.get('owner',{}).get('version','')),
         'Needs attention: %s' % h.get('needs_attention_count',0),
         'CONFIGURED/SYNCED describes local settings, not a live Trakt server test.',
         'Unselected or independently authorized add-ons are not forced to share credentials.',
         '', 'SERVICES','--------']
    for s in h.get('services',[]): out.append('%s — %s' % (s.get('service','?'),s.get('status','?')))
    out += ['', 'TRAKT REFRESH STATE','-------------------',str(h.get('trakt',{}).get('log_state','?')),
            '', 'TRAKT TARGET CONSISTENCY','------------------------']
    targets=[x for x in h.get('trakt',{}).get('targets',[]) if x.get('installed')]
    if not targets: out.append('(no known installed Trakt targets detected)')
    for t in targets:
        selected='selected' if t.get('selected_in_am_lite_sync') else 'not selected'
        out.append('%s — %s — %s' % (t.get('name','?'),t.get('status','?'),selected))
    out += ['', 'REAL-DEBRID REFRESH STATE','-------------------------',str(h.get('real_debrid',{}).get('log_state','?')),
            '',str(h.get('privacy',''))]
    return '\n'.join(out)+'\n'

def authorization_health():
    h=_authorization_health()
    text=_authorization_health_text(h)
    xbmcgui.Dialog().textviewer('Kodi Health Center — Authorization Health',text,usemono=False)
    if installed(AUTH_SURFACE_ID) and xbmcgui.Dialog().yesno('Authorization Health','Open Infinity Authorization & Accounts now?'):
        xbmc.executebuiltin('RunAddon(%s)' % AUTH_SURFACE_ID)


def _scan_collect(source='scan-kodi'):
    """Collect the exact read-only evidence set used by Scan Kodi.

    This helper deliberately does not mutate scan history, delete data, enable/disable
    add-ons, or perform repairs. The same collector is reused by Send Logs for Help so
    a support ZIP contains the same categories the user sees in Scan Kodi.
    """
    lines=log_lines(include_old=False)
    oldlines=old_log_lines()
    errors=[l for l in lines if re.search(r'\b(error|critical|fatal)\b',l,re.I)]
    actual=[l for l in errors if any(p in l.lower() for p in CRASH_PATTERNS)]
    noisy=[l for l in errors if any(p.lower() in l.lower() for p in NOISY)]
    olderrors=[l for l in oldlines if re.search(r'\b(error|critical|fatal)\b',l,re.I)]
    oldactual=[l for l in olderrors if any(p in l.lower() for p in CRASH_PATTERNS)]
    issues=detect_issues(lines)
    runtime_findings,recovered_runtime_findings=_runtime_findings(lines)
    authorization=_authorization_health(lines)
    from khc_lifecycle import read_checkpoint
    checkpoint=read_checkpoint(HOME)
    recovered_samples={sample for finding in recovered_runtime_findings for sample in finding.get('resolved_samples',finding.get('samples',[]))}
    resolved_errors=[line for line in errors if line in recovered_samples]
    errors=[line for line in errors if line not in recovered_samples]
    actual=[line for line in actual if line not in recovered_samples]
    noisy=[line for line in noisy if line not in recovered_samples]

    data_root=xbmcvfs.translatePath('special://profile/addon_data/')
    leftovers=[]
    try:
        if os.path.isdir(data_root):
            for d in sorted(os.listdir(data_root)):
                if d.startswith(('plugin.','script.','service.','repository.','skin.')) and not installed(d):
                    path=os.path.join(data_root,d)
                    leftovers.append({'addon_id':d,'size_bytes':folder_size(path),'size':fmt_bytes(folder_size(path))})
    except:
        leftovers=[]

    tweaks=[]
    for item in _known_tweak_leftovers():
        try:
            name,path,size=item
            tweaks.append({'name':name,'size_bytes':int(size),'size':fmt_bytes(size)})
        except:
            continue

    free=total=0
    try:
        u=shutil.disk_usage(HOME); free,total=u.free,u.total
    except:
        pass

    return {
        'schema':3,
        'source':source,
        'captured_epoch':time.time(),
        'health_center_version':xbmcaddon.Addon(ADDON_ID).getAddonInfo('version'),
        'status':'NEEDS ATTENTION' if (actual or issues or runtime_findings or checkpoint.get('active') or authorization.get('needs_attention_count',0)) else 'GOOD',
        'status_reason':{'likely_crashes_script_failures':len(actual),'actionable_issues':len(issues),'runtime_findings':len(runtime_findings),'recovered_runtime_findings':len(recovered_runtime_findings),'authorization_findings':authorization.get('needs_attention_count',0)},
        'counts':{
            'current_errors':len(errors),
            'resolved_errors':len(resolved_errors),
            'checkpoint_active':int(checkpoint.get('active',False)),
            'likely_crashes_script_failures':len(actual),
            'known_noise':len(noisy),
            'actionable_issues':len(issues),
            'historical_errors':len(olderrors),
            'historical_likely_crashes_script_failures':len(oldactual),
            'leftover_addon_data':len(leftovers),
            'known_tweak_remnants':len(tweaks),
            'runtime_findings':len(runtime_findings),
            'runtime_finding_occurrences':sum(int(x.get('count',0)) for x in runtime_findings),
            'recovered_runtime_findings':len(recovered_runtime_findings),
            'recovered_runtime_finding_occurrences':sum(int(x.get('count',0)) for x in recovered_runtime_findings),
            'authorization_findings':authorization.get('needs_attention_count',0),
        },
        'current_errors':errors,
        'resolved_errors':resolved_errors,
        'shutdown_checkpoint':checkpoint,
        'likely_crashes_script_failures':actual,
        'known_noise':noisy,
        'actionable_issues':[
            {k:x.get(k) for k in ('key','severity','title','detail','addonid','repair')}
            for x in issues
        ],
        'runtime_findings':runtime_findings,
        'recovered_runtime_findings':recovered_runtime_findings,
        'authorization_health':authorization,
        'historical_errors':olderrors,
        'historical_likely_crashes_script_failures':oldactual,
        'leftover_addon_data':leftovers,
        'known_tweak_remnants':tweaks,
        'storage':{'free_bytes':int(free),'total_bytes':int(total),'free':fmt_bytes(free),'total':fmt_bytes(total)},
        'safety_note':'Read-only scan. Leftover add-on data is reported only and is not removed by Scan Kodi.',
    }


def _save_scan_result(snapshot):
    try:
        tmp=SCAN_RESULT_FILE+'.tmp'
        with open(tmp,'w',encoding='utf-8') as f:
            json.dump(snapshot,f,indent=2,sort_keys=True)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,SCAN_RESULT_FILE)
    except:
        pass


def _load_scan_result():
    try:
        with open(SCAN_RESULT_FILE,'r',encoding='utf-8') as f:
            data=json.load(f)
        return data if isinstance(data,dict) else None
    except:
        return None


def _scan_details_text(scan):
    counts=scan.get('counts',{}) if isinstance(scan,dict) else {}
    out=[
        'KODI HEALTH CENTER — SCAN KODI DETAILS',
        '=======================================',
        'Health Center: '+str(scan.get('health_center_version','?')),
        'Source: '+str(scan.get('source','?')),
        'Status: '+str(scan.get('status','?')),
        '',
        'COUNTS',
        '------',
        'Current errors: %s' % counts.get('current_errors',0),
        'Likely crashes/script failures: %s' % counts.get('likely_crashes_script_failures',0),
        'Known noisy/repository entries: %s' % counts.get('known_noise',0),
        'Actionable issues: %s' % counts.get('actionable_issues',0),
        'Runtime findings: %s (%s occurrences)' % (counts.get('runtime_findings',0),counts.get('runtime_finding_occurrences',0)),
        'Authorization findings: %s' % counts.get('authorization_findings',0),
        'Historical errors: %s' % counts.get('historical_errors',0),
        'Historical crash/script entries: %s' % counts.get('historical_likely_crashes_script_failures',0),
        'Leftover add-on data folders: %s' % counts.get('leftover_addon_data',0),
        'Known tweak remnants: %s' % counts.get('known_tweak_remnants',0),
        '',
        'ACTIONABLE ISSUES — FULL DETAIL',
        '-------------------------------',
    ]
    issues=scan.get('actionable_issues',[]) or []
    if not issues:
        out.append('(none)')
    for i,x in enumerate(issues,1):
        out.append('%d. [%s] %s' % (i,str(x.get('severity','?')).upper(),x.get('title','Issue')))
        out.append('   key: '+str(x.get('key','')))
        if x.get('addonid'): out.append('   addon: '+str(x.get('addonid')))
        if x.get('repair'): out.append('   repair class: '+str(x.get('repair')))
        out.append('   detail: '+str(x.get('detail','')))


    out.extend(['','RUNTIME FINDINGS — DEDUPLICATED','-------------------------------'])
    runtime=scan.get('runtime_findings',[]) or []
    if not runtime: out.append('(none)')
    for i,x in enumerate(runtime,1):
        out.append('%d. [%s] %s — %s occurrence(s)' % (i,str(x.get('severity','?')).upper(),x.get('title','Finding'),x.get('count',0)))
        out.append('   key: '+str(x.get('key','')))
        out.append('   detail: '+str(x.get('detail','')))
        for sample in (x.get('samples',[]) or [])[:3]: out.append('   sample: '+str(sample))

    out.extend(['','RECOVERED RUNTIME FINDINGS — INFORMATION ONLY','---------------------------------------------'])
    recovered=scan.get('recovered_runtime_findings',[]) or []
    if not recovered: out.append('(none)')
    for i,x in enumerate(recovered,1):
        out.append('%d. [RECOVERED] %s — %s occurrence(s)' % (i,x.get('title','Recovered finding'),x.get('count',0)))
        out.append('   detail: '+str(x.get('detail','')))
        if x.get('recovery_sample'): out.append('   recovery: '+str(x.get('recovery_sample')))

    out.extend(['','AUTHORIZATION HEALTH','--------------------'])
    auth=scan.get('authorization_health',{}) or {}
    for line in _authorization_health_text(auth).splitlines()[2:]: out.append(line)

    def section(title,key):
        out.extend(['',title,'-'*len(title)])
        values=scan.get(key,[]) or []
        if not values:
            out.append('(none)')
        else:
            for value in values:
                out.append(str(value))

    section('LIKELY CRASHES / SCRIPT FAILURES','likely_crashes_script_failures')
    section('CURRENT ERROR LOG ENTRIES','current_errors')
    section('KNOWN NOISY / REPOSITORY ENTRIES','known_noise')
    section('HISTORICAL-ONLY ERRORS','historical_errors')
    section('RESOLVED / VERIFIED LOG OPERATIONS','resolved_errors')
    out.extend(['','SHUTDOWN CHECKPOINT',str(scan.get('shutdown_checkpoint',{}))])
    section('HISTORICAL CRASH / SCRIPT ENTRIES','historical_likely_crashes_script_failures')

    out.extend(['','LEFTOVER ADD-ON DATA — REPORT ONLY','----------------------------------'])
    vals=scan.get('leftover_addon_data',[]) or []
    if not vals: out.append('(none)')
    for x in vals: out.append('%s — %s' % (x.get('addon_id','?'),x.get('size','?')))

    out.extend(['','KNOWN TWEAK REMNANTS','--------------------'])
    vals=scan.get('known_tweak_remnants',[]) or []
    if not vals: out.append('(none)')
    for x in vals: out.append('%s — %s' % (x.get('name','?'),x.get('size','?')))

    st=scan.get('storage',{}) or {}
    out.extend(['','STORAGE','-------','Free: %s / %s' % (st.get('free','?'),st.get('total','?')),'',str(scan.get('safety_note',''))])
    return '\n'.join(out)+'\n'


def check_kodi():
    previous=_load_last_scan_keys()
    scan=_scan_collect('scan-kodi-manual')
    issues=scan.get('actionable_issues',[])
    current=set(x.get('key','') for x in issues if x.get('key'))
    cleared=sorted(k for k in (previous-current) if k.startswith('missing:'))
    scan['cleared_dependencies_this_scan']=[_dependency_name_from_key(k) for k in cleared]
    _save_scan_keys(current)
    _save_scan_result(scan)

    if cleared:
        names=[_dependency_name_from_key(k) for k in cleared]
        short=', '.join(names[:3])
        if len(names)>3:
            short+=' +%d more' % (len(names)-3)
        xbmcgui.Dialog().notification(
            'Kodi Health Center',
            'Cleared dependencies: %s' % short,
            xbmcgui.NOTIFICATION_INFO,5000)

    c=scan.get('counts',{})
    st=scan.get('storage',{})
    msg='Kodi Status: %s\n\nCrashes/script failures: %d\nProblems needing attention: %d\nRuntime findings: %d\nAuthorization findings: %d\nLeftover add-on data: %d\nKnown tweak remnants: %d\nStorage free: %s / %s' % (
        scan.get('status','?'),c.get('likely_crashes_script_failures',0),c.get('actionable_issues',0),c.get('runtime_findings',0),c.get('authorization_findings',0),
        c.get('leftover_addon_data',0),c.get('known_tweak_remnants',0),st.get('free','0 B'),st.get('total','0 B'))
    msg+='\n\nShutdown: '+scan.get('shutdown_checkpoint',{}).get('state','UNVERIFIED')
    if cleared:
        msg+='\n\nCleared this scan: %d dependency issue%s' % (len(cleared),'' if len(cleared)==1 else 's')
    if xbmcgui.Dialog().yesno('Kodi Health Check',msg+'\n\nOpen advanced details?'):
        details='ACTIVE / CURRENT\nRecent log errors: %d\nLikely crash/script failures: %d\nKnown noisy/repository errors: %d\nCurrent actionable issues: %d\nRuntime findings: %d\nRecovered runtime findings: %d\n\nOLD / HISTORY (not active)\nOld log errors: %d\nOld crash/script entries: %d\n\nLEFTOVER ADD-ON DATA (not installed): %d\nKnown tweak remnants: %d' % (
            c.get('current_errors',0),c.get('likely_crashes_script_failures',0),c.get('known_noise',0),c.get('actionable_issues',0),c.get('runtime_findings',0),c.get('recovered_runtime_findings',0),
            c.get('historical_errors',0),c.get('historical_likely_crashes_script_failures',0),c.get('leftover_addon_data',0),c.get('known_tweak_remnants',0))
        tweaks=scan.get('known_tweak_remnants',[]) or []
        if tweaks:
            details+='\n\nTWEAK REMNANTS\n'+'\n'.join('• '+x.get('name','?') for x in tweaks[:12])
        xbmcgui.Dialog().ok('Kodi Health Check — Advanced',details)
        leftovers=scan.get('leftover_addon_data',[]) or []
        if leftovers and xbmcgui.Dialog().yesno('Leftover Add-on Data','%d leftover add-on-data folder%s found.\n\nView the names?\n\nNothing will be deleted.' % (len(leftovers),'' if len(leftovers)==1 else 's')):
            names=[x.get('addon_id','?') for x in leftovers]
            byname={x.get('addon_id','?'):x for x in leftovers}
            while True:
                j=xbmcgui.Dialog().select('Leftover Add-on Data (%d)' % len(names),names+['Back'])
                if j<0 or j>=len(names):
                    break
                addon_id=names[j]
                item=byname.get(addon_id,{})
                xbmcgui.Dialog().ok('Leftover Add-on Data',addon_id+'\n\nSize: '+str(item.get('size','?'))+'\n\nThe matching add-on is not currently installed. Scan Kodi is only reporting this folder; it has NOT been removed.')

def repairs():
    while True:
        issues=detect_issues()
        if not issues:
            xbmcgui.Dialog().ok('Manual Repair','No actionable issues were detected.'); return
        labels=[]
        for x in issues:
            mark='[ERROR]' if x['severity']=='error' else '[WARN]'
            labels.append('%s %s' % (mark,x['title']))
        i=xbmcgui.Dialog().select('Manual Repair — select an issue',labels+['Done'])
        if i<0 or i>=len(issues): break
        # Copy the exact selected issue so later rescans cannot remap the action.
        selected=dict(issues[i])
        if xbmcgui.Dialog().yesno(selected['title'],selected['detail']+'\n\nOpen safe options for THIS issue?'):
            choose_action(selected)

def _remove_contents(target, allow_dirs=True, preserve_names=None, stop_for_playback=False):
    preserve=set(x.lower() for x in (preserve_names or []))
    removed=0; failed=0; freed=0
    if not os.path.isdir(target): return removed,failed,freed
    try:
        names=os.listdir(target)
    except:
        return removed,1,freed
    for n in names:
        if stop_for_playback and xbmc.getCondVisibility('Player.HasMedia'):
            break
        if n.lower() in preserve: continue
        p=os.path.join(target,n)
        try:
            before=folder_size(p) if os.path.isdir(p) else (os.path.getsize(p) if os.path.isfile(p) else 0)
            if os.path.isfile(p) or os.path.islink(p): os.remove(p)
            elif allow_dirs and os.path.isdir(p): shutil.rmtree(p)
            else: continue
            removed+=1; freed+=before
        except:
            failed+=1
    return removed,failed,freed

def _orphan_addon_data():
    """Return addon_data folders whose matching add-on is not installed."""
    root=xbmcvfs.translatePath('special://profile/addon_data/')
    out=[]
    try:
        if os.path.isdir(root):
            for name in os.listdir(root):
                if name.startswith(('plugin.','script.','service.','repository.','skin.')) and not installed(name):
                    out.append((name,os.path.join(root,name)))
    except:
        pass
    return out


def quick_clean():
    # Conservative one-tap cleanup: disposable caches only. Never touches addon_data, databases, add-ons or repositories.
    psize=folder_size(PACKAGES); tsize=folder_size(TEMP)
    oldsize=0
    try: oldsize=os.path.getsize(OLDLOG) if os.path.isfile(OLDLOG) else 0
    except: pass
    total=psize+tsize+oldsize
    if xbmc.getCondVisibility('Player.HasMedia'):
        xbmcgui.Dialog().ok('Quick Clean','Playback is active. Stop playback first so Health Center does not remove temporary files that Kodi may still be using.')
        return
    msg=('Quick Clean will remove only disposable Kodi clutter:\n\n'
         '• Downloaded add-on package cache: %s\n'
         '• Temporary files/cache: %s\n'
         '• Old Kodi log: %s\n\n'
         'Estimated reclaimable space: %s\n\n'
         'It will NOT remove add-ons, repositories, settings, databases, favorites, watch history, or addon_data.' %
         (fmt_bytes(psize),fmt_bytes(tsize),fmt_bytes(oldsize),fmt_bytes(total)))
    if not xbmcgui.Dialog().yesno('Quick Clean',msg+'\n\nClean now?'):
        return
    if xbmc.getCondVisibility('Player.HasMedia'):
        xbmcgui.Dialog().ok('Quick Clean','Playback started; cleanup was canceled without removing files.')
        return
    removed=failed=freed=0
    # Package ZIPs are safe to redownload. Temp is disposable when playback is stopped.
    for target in (PACKAGES,TEMP):
        r,f,b=_remove_contents(target,allow_dirs=True,preserve_names=['kodi.log'], stop_for_playback=True)
        removed+=r; failed+=f; freed+=b
    try:
        if not xbmc.getCondVisibility('Player.HasMedia') and os.path.isfile(OLDLOG):
            b=os.path.getsize(OLDLOG); os.remove(OLDLOG); removed+=1; freed+=b
    except:
        failed+=1
    text='Quick Clean complete.\n\nFreed: %s\nItems removed: %d' % (fmt_bytes(freed),removed)
    if failed: text+='\nCould not remove: %d item(s)' % failed
    text+='\n\nAdd-on data, add-ons, repositories, settings and databases were not removed.'
    xbmcgui.Dialog().ok('Quick Clean',text)


def report_text(scan=None):
    scan=scan or _scan_collect('health-summary')
    c=scan.get('counts',{})
    out=['KODI HEALTH CENTER DIAGNOSTIC REPORT','====================================','Version: '+str(scan.get('health_center_version','?')),'Kodi build: '+xbmc.getInfoLabel('System.BuildVersion'),'','SUMMARY','-------','Current log errors: %d'%c.get('current_errors',0),'Likely crash/script failures: %d'%c.get('likely_crashes_script_failures',0),'Actionable issues: %d'%c.get('actionable_issues',0),'Runtime findings: %d'%c.get('runtime_findings',0),'Recovered runtime findings: %d'%c.get('recovered_runtime_findings',0),'Authorization findings: %d'%c.get('authorization_findings',0),'Historical-only errors: %d'%c.get('historical_errors',0),'']
    out+=['ACTIONABLE ISSUES','-----------------']
    for x in scan.get('actionable_issues',[]): out+=['- '+str(x.get('title','Issue')),'  '+str(x.get('detail',''))]
    out+=['','NOTE','----','Repository/configuration noise is not counted as a crash by itself.','Detailed Scan Kodi evidence is included separately as scan-results.json and scan-details.txt.','Authorization status is included separately as authorization-health.json and authorization-health.txt.','Authorization Health compares selected account fields in memory; values are never included in its report. Other log text is filtered best-effort.']
    return '\n'.join(out)+'\n'


def support_package():
    # All support exports use the same verified, filtered diagnostic bundle and
    # now include a fresh read-only Scan Kodi snapshot plus the last manual scan.
    from khc_kodi import export_report
    try:
        current_scan=_scan_collect('support-export-fresh-scan')
        last_manual=_load_scan_result()
        if isinstance(last_manual,dict):
            current_scan['last_manual_scan']={
                'captured_epoch':last_manual.get('captured_epoch'),
                'status':last_manual.get('status'),
                'counts':last_manual.get('counts',{}),
                'cleared_dependencies_this_scan':last_manual.get('cleared_dependencies_this_scan',[]),
            }
        summary=report_text(current_scan)
        details=_scan_details_text(current_scan)
        auth=current_scan.get('authorization_health') or _authorization_health()
        auth_details=_authorization_health_text(auth)
    except Exception as error:
        current_scan={'schema':1,'source':'support-export','status':'scan_unavailable','error_type':type(error).__name__}
        summary='Health scan summary unavailable: '+type(error).__name__
        details='Scan Kodi details unavailable: '+type(error).__name__+'\n'
        auth={'schema':1,'status':'unavailable','error_type':type(error).__name__,'credential_values_exported':False}
        auth_details='Authorization Health unavailable: '+type(error).__name__+'\n'
    export_report(health_text=summary, scan_results=current_scan, scan_details=details, authorization_health=auth, authorization_details=auth_details)


# Compatibility name used by earlier menu code.

def storage_manager():
    try:u=shutil.disk_usage(HOME)
    except:u=None
    msg='Kodi packages: %s\nKodi temp: %s' % (fmt_bytes(folder_size(PACKAGES)),fmt_bytes(folder_size(TEMP)))
    if u: msg='Device free: %s / %s\n\n'%( fmt_bytes(u.free),fmt_bytes(u.total))+msg
    xbmcgui.Dialog().ok('Storage Info',msg+'\n\nHealth Center cannot increase physical storage; it can only safely reclaim disposable Kodi files.')



def addon_dependencies(addonid):
    """Read declared dependencies from an installed add-on's addon.xml."""
    out=[]
    path=os.path.join(ADDONS,addonid,'addon.xml')
    text=read_text(path,1024*1024)
    if not text: return out
    try:
        import xml.etree.ElementTree as ET
        root=ET.fromstring(text)
        req=root.find('requires')
        if req is None: return out
        for imp in req.findall('import'):
            dep=imp.attrib.get('addon')
            if not dep or dep.startswith('xbmc.'): continue
            out.append({
                'id':dep,
                'version':imp.attrib.get('version',''),
                'optional':imp.attrib.get('optional','false').lower()=='true'
            })
    except Exception:
        pass
    return out

def installed_addon_ids():
    ids=[]
    if not os.path.isdir(ADDONS): return ids
    for d in os.listdir(ADDONS):
        if os.path.isfile(os.path.join(ADDONS,d,'addon.xml')):
            ids.append(d)
    return sorted(ids)

def repo_candidates_for_dependency(dep):
    """Find installed repositories whose local metadata/package cache mentions a dependency."""
    found=[]
    for repo in repository_addons():
        rid=repo.get('id')
        rpath=os.path.join(ADDONS,rid)
        hit=False
        # Search only small repository metadata files already on-device. No arbitrary internet downloads.
        for base,dirs,files in os.walk(rpath):
            dirs[:]=[d for d in dirs if d.lower() not in ('resources','media')]
            for fn in files:
                if not fn.lower().endswith(('.xml','.md5','.txt')): continue
                p=os.path.join(base,fn)
                try:
                    if os.path.getsize(p)>4*1024*1024: continue
                except: continue
                if dep in read_text(p,4*1024*1024):
                    hit=True; break
            if hit: break
        if hit: found.append(repo)
    return found



def _repo_endpoints(repoid):
    """Return every repository info/datadir pair declared by an installed repo.

    Kodi repositories may declare info/datadir directly under the extension or
    inside one or more <dir> blocks. Search both layouts.
    """
    p=os.path.join(ADDONS,repoid,'addon.xml')
    text=read_text(p,2*1024*1024)
    if not text: return []
    out=[]
    try:
        import xml.etree.ElementTree as ET
        root=ET.fromstring(text)
        for ext in root.findall('extension'):
            if ext.attrib.get('point')!='xbmc.addon.repository': continue
            blocks=[ext]+list(ext.findall('dir'))
            for block in blocks:
                info=block.find('info'); datadir=block.find('datadir')
                info_url=(info.text or '').strip() if info is not None else ''
                data_url=(datadir.text or '').strip() if datadir is not None else ''
                zipped=(datadir.attrib.get('zip','false').lower()=='true') if datadir is not None else False
                if info_url and data_url:
                    item={'info':info_url,'datadir':data_url,'zip':zipped}
                    if item not in out: out.append(item)
    except Exception:
        return []
    return out

def _fetch_bytes(url, timeout=7, limit=16*1024*1024):
    from khc_download import fetch_bytes
    return fetch_bytes(url, timeout=timeout, limit=limit)


def _repo_remote_match(repo, dep):
    """Look up one exact add-on/dependency ID in an installed repo's metadata."""
    for ep in _repo_endpoints(repo.get('id')):
        info_url=ep['info']
        try:
            data=_fetch_bytes(info_url)
            if info_url.lower().endswith('.gz') or data[:2]==b'\x1f\x8b': data=gzip.decompress(data)
            import xml.etree.ElementTree as ET
            root=ET.fromstring(data); node=None
            if root.tag=='addon' and root.attrib.get('id')==dep: node=root
            else:
                for a in root.iter('addon'):
                    if a.attrib.get('id')==dep: node=a; break
            if node is None: continue
            ver=node.attrib.get('version','').strip()
            if not ver: continue
            base=ep['datadir'].rstrip('/')+'/'
            zip_url=urllib.parse.urljoin(base, dep+'/'+dep+'-'+ver+'.zip')
            return {'repo':repo,'version':ver,'url':zip_url,'endpoint':ep}
        except Exception:
            continue
    return None

def locate_dependency_sources(dep):
    """Search installed repositories for an exact dependency, including remote repo metadata."""
    repos=repository_addons()
    if not repos: return []
    dialog=xbmcgui.DialogProgress()
    dialog.create('Dependency Locator','Searching installed repositories...')
    found=[]
    try:
        for i,repo in enumerate(repos,1):
            if dialog.iscanceled(): break
            dialog.update(int((i-1)*100/max(1,len(repos))), 'Checking %d/%d: %s' % (i,len(repos),(repo.get('name') or repo.get('id'))[:45]))
            hit=_repo_remote_match(repo,dep)
            if hit: found.append(hit)
        dialog.update(100,'Search complete')
    finally:
        dialog.close()
    return found


def _verify_dependency_zip(path, dep):
    from khc_dependency import dependency_info
    try:
        dependency_info(path, dep)
        return True
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, ET.ParseError):
        return False

def manual_download_dependency(dep, parent=None):
    """Locate an exact package in installed repository metadata, download it, and verify its add-on ID."""
    sources=locate_dependency_sources(dep)
    if not sources:
        xbmcgui.Dialog().ok('Dependency Locator',
            'No installed repository advertised this dependency in its repository metadata.\n\n'
            'Health Center will not guess or download from an unknown website.\n\n'+dep)
        return False
    labels=[]
    for x in sources:
        r=x['repo']
        labels.append('%s — v%s%s' % (r.get('name') or r.get('id'),x.get('version','?'),' [disabled]' if not r.get('enabled') else ''))
    j=xbmcgui.Dialog().select('Choose dependency source',labels+['Cancel'])
    if j<0 or j>=len(sources): return False
    src=sources[j]; url=src['url']; repo=src['repo']
    scheme=urllib.parse.urlparse(url).scheme.lower()
    warning=''
    if scheme=='http': warning='\n\nWarning: this repository uses unencrypted HTTP.'
    if not xbmcgui.Dialog().yesno('Manual dependency download',
        'Download the exact dependency ZIP advertised by this installed repository?\n\n'
        'Dependency: %s\nVersion: %s\nRepository: %s%s' % (dep,src.get('version','?'),repo.get('name') or repo.get('id'),warning)):
        return False
    default_dir=PACKAGES
    try:
        chosen=xbmcgui.Dialog().browseSingle(3,'Choose where to save dependency ZIP','files','',False,False,default_dir)
    except Exception:
        chosen=''
    if not chosen:
        return False  # Cancel is not permission to download to a fallback directory.
    chosen=xbmcvfs.translatePath(chosen)
    progress=xbmcgui.DialogProgress()
    progress.create('Manual dependency download','Downloading '+dep+'...')
    from khc_dependency import download_dependency
    from khc_download import DownloadCancelled
    try:
        out=download_dependency(url,chosen,dep,src.get('version',''),
            cancelled=progress.iscanceled,
            progress=lambda got,total: progress.update(min(90,int(90*got/total)) if total else 0,
                                                       'Downloading '+dep+'...'))
        progress.update(100,'Download verified')
        progress.close()
        xbmcgui.Dialog().ok('Dependency downloaded',
            'Downloaded and verified:\n\n%s\n\n'
            'Now use Kodi: Add-ons > Install from zip file, then choose this ZIP.' % out)
        return True
    except DownloadCancelled:
        return False
    except Exception as error:
        progress.close()
        xbmcgui.Dialog().ok('Dependency download failed',
                            dep+'\n\nDownload or verification did not complete: '+type(error).__name__)
        return False
    finally:
        progress.close()

def request_kodi_install(dep):
    """Ask Kodi itself to install the dependency from configured repositories."""
    try:
        xbmc.executebuiltin('InstallAddon(%s)' % dep)
        xbmcgui.Dialog().notification('Add-on Dependencies','Kodi install requested for '+dep,xbmcgui.NOTIFICATION_INFO,4000)
        time.sleep(2)
        xbmc.executebuiltin('UpdateLocalAddons')
        return True
    except Exception:
        return False

def dependency_detail(dep, parent=None):
    did=dep.get('id') if isinstance(dep,dict) else dep
    reqver=dep.get('version','') if isinstance(dep,dict) else ''
    optional=dep.get('optional',False) if isinstance(dep,dict) else False
    inst=installed(did)
    users=dependency_users(did)
    repos=repo_candidates_for_dependency(did)
    status='INSTALLED' if inst else 'MISSING'
    if inst and inst.get('enabled') is False: status='INSTALLED / DISABLED'
    msg='Dependency: %s\nStatus: %s' % (did,status)
    if reqver: msg+='\nRequired version: '+reqver
    if optional: msg+='\nOptional: Yes'
    if inst: msg+='\nInstalled version: '+str(inst.get('version','?'))
    if parent: msg+='\nSelected add-on: '+parent
    if users: msg+='\n\nUsed by:\n- '+'\n- '.join(users[:15])
    if repos:
        msg+='\n\nInstalled repositories whose local metadata mentions it:\n- '+'\n- '.join(
            (r.get('name') or r.get('id'))+(' [enabled]' if r.get('enabled') else ' [disabled]') for r in repos[:10])
    return msg,repos

def dependency_repair_menu(dep,parent=None):
    did=dep.get('id') if isinstance(dep,dict) else dep
    while True:
        inst=installed(did)
        msg,repos=dependency_detail(dep,parent)
        opts=['View details']
        disabled=[r for r in repos if not r.get('enabled')]
        if not inst:
            if disabled: opts.append('Enable matching repository & request install')
            opts.append('Ask Kodi to install from configured repositories')
            opts.append('Locate source & manually download ZIP')
        opts+=['Rescan','Back']
        i=xbmcgui.Dialog().select(did,opts)
        if i<0 or opts[i]=='Back': return
        choice=opts[i]
        if choice=='View details':
            xbmcgui.Dialog().ok('Dependency details',msg)
        elif choice=='Enable matching repository & request install':
            if not disabled: continue
            labels=[(r.get('name') or r.get('id'))+' — '+r.get('id') for r in disabled]
            j=xbmcgui.Dialog().select('Enable repository',labels+['Cancel'])
            if j<0 or j>=len(disabled): continue
            repo=disabled[j]
            if xbmcgui.Dialog().yesno('Enable & Install?',
                'Enable this already-installed repository and ask Kodi to install the missing dependency?\n\n'+
                (repo.get('name') or repo.get('id'))+'\n'+did):
                if set_enabled(repo.get('id'),True):
                    xbmc.executebuiltin('UpdateAddonRepos')
                    time.sleep(2)
                    request_kodi_install(did)
                    xbmcgui.Dialog().notification(
                        'Add-on Dependencies',
                        'Install request sent to Kodi',
                        xbmcgui.NOTIFICATION_INFO,3000)
                    # Do not immediately rescan or open a blocking dialog here.
                    # Kodi may still be opening its own install/progress UI.
                    return
        elif choice=='Ask Kodi to install from configured repositories':
            if xbmcgui.Dialog().yesno('Request install?',
                'Health Center will ask Kodi to install this add-on using your configured repositories.\n\n'
                'It will NOT download a ZIP from an unknown website.\n\n'+did):
                request_kodi_install(did)
                xbmcgui.Dialog().notification(
                    'Add-on Dependencies',
                    'Install request sent to Kodi',
                    xbmcgui.NOTIFICATION_INFO,3000)
                # Let Kodi finish its own install flow without Health Center
                # covering it with a second modal dialog.
                return
        elif choice=='Locate source & manually download ZIP':
            manual_download_dependency(did,parent)
        elif choice=='Rescan':
            continue




def dependency_manager():
    """Fast dependency repair menu. No repository/network scan runs on entry."""
    dlg=xbmcgui.Dialog()
    while True:
        opts=[
            'Missing Dependencies',
            'Browse Installed Add-ons',
            'Back'
        ]
        i=dlg.select('Dependency Repair',opts)
        if i<0 or i==2:
            return

        if i==0:
            # Local-only missing dependency scan, with progress/cancel.
            progress=xbmcgui.DialogProgress()
            progress.create('Dependency Repair','Checking installed add-ons...')
            missing={}
            aids=installed_addon_ids()
            total=max(1,len(aids))
            for n,parent in enumerate(aids):
                if progress.iscanceled():
                    progress.close()
                    return
                if n % 10 == 0:
                    progress.update(int((n*100)/total),
                                    'Checking %d of %d installed add-ons...' % (n+1,len(aids)))
                    xbmc.sleep(1)
                try:
                    for d in addon_dependencies(parent):
                        if not d.get('optional') and not installed(d['id']):
                            missing[d['id']]=d
                except Exception:
                    continue
            progress.close()

            deps=sorted(missing.values(),key=lambda x:x['id'].lower())
            if not deps:
                dlg.ok('Dependency Repair','No missing required dependencies were detected.')
                continue
            labels=[d['id']+((' >= '+d['version']) if d.get('version') else '') for d in deps]
            j=dlg.select('Missing Dependencies',labels+['Back'])
            if j<0 or j>=len(deps):
                continue
            dependency_repair_menu(deps[j])

        elif i==1:
            # Show add-ons first; only inspect dependencies for the selected add-on.
            aids=installed_addon_ids()
            labels=[]
            usable=[]
            for aid in aids:
                a=installed(aid) or {}
                labels.append(a.get('name') or aid)
                usable.append(aid)
            order=sorted(range(len(labels)),key=lambda x:labels[x].lower())
            labels=[labels[x] for x in order]
            usable=[usable[x] for x in order]
            j=dlg.select('Installed Add-ons',labels+['Back'])
            if j<0 or j>=len(usable):
                continue
            parent=usable[j]
            deps=addon_dependencies(parent)
            if not deps:
                dlg.ok('Dependency Repair','This add-on has no declared dependencies.')
                continue
            while True:
                dlabels=[]
                for d in deps:
                    state='OK' if installed(d['id']) else ('OPTIONAL' if d.get('optional') else 'MISSING')
                    dlabels.append('[%s] %s%s' %
                                   (state,d['id'],(' >= '+d['version']) if d.get('version') else ''))
                k=dlg.select(parent+' — Dependencies',dlabels+['Back'])
                if k<0 or k>=len(deps):
                    break
                dependency_repair_menu(deps[k],parent)




def undo_last_repair():
    try:
        data=json.load(open(UNDO_FILE,'r',encoding='utf-8'))
    except:
        xbmcgui.Dialog().ok('Undo','There is no reversible Health Center action recorded yet.'); return
    if data.get('action')=='enabled_state' and data.get('addonid'):
        aid=data['addonid']; prev=bool(data.get('previous'))
        if not installed(aid): xbmcgui.Dialog().ok('Undo','The add-on is no longer installed, so its enable/disable state cannot be restored.'); return
        if xbmcgui.Dialog().yesno('Undo last change?','Restore %s to %s?' % (aid,'ENABLED' if prev else 'DISABLED')):
            ok=set_enabled(aid,prev,record=False)
            if ok:
                try: os.remove(UNDO_FILE)
                except: pass
            xbmcgui.Dialog().ok('Undo','Previous state restored.' if ok else 'Kodi could not restore the previous state.')
        return
    xbmcgui.Dialog().ok('Undo','The last recorded action is not automatically reversible.')


EASY_REPO_CATALOG_URL='https://fuse99.com/zztext/k19repos.xml'

def _easy_repo_catalog_urls():
    """Read Easy Repo Installer's public catalog and return unique HTTP source URLs."""
    try:
        req=urllib.request.Request(EASY_REPO_CATALOG_URL,headers={'User-Agent':'Kodi Health Center/1.9.37'})
        data=_fetch_bytes(EASY_REPO_CATALOG_URL, timeout=12, limit=2*1024*1024).decode('utf-8','ignore')
    except Exception:
        return []
    urls=[]
    for u in re.findall(r'https?://[^\s<>"\']+',data,re.I):
        u=u.replace('&amp;','&').rstrip(').,;')
        if u not in urls and u != EASY_REPO_CATALOG_URL:
            urls.append(u)
    return urls





def _installed_addon_id_set():
    """Return installed Kodi add-on IDs using existing Health Center helpers."""
    try:
        return set(installed_addon_ids())
    except Exception:
        return set()

def _required_dependency_ids():
    """
    Build the set of dependency IDs required by add-ons that are CURRENTLY installed.
    This is the safety gate: anything still required is never treated as orphaned.
    """
    required=set()
    installed_ids=_installed_addon_id_set()
    for parent in list(installed_ids):
        try:
            for dep in addon_dependencies(parent):
                did=(dep or {}).get('id')
                if did and not (dep or {}).get('optional'):
                    required.add(did)
        except Exception:
            continue
    return required



def _repair_super_favourites_keymaps(keymaps_root=None, apply_reload=True):
    """Repair only the exact legacy Super Favourites keymap action seen on device.

    Kodi's keymap action is RunScript(...), not xbmc.runscript(...). The repair is
    deliberately narrow: it touches only XML files under userdata/keymaps that
    contain both the legacy prefix and Super Favourites capturelauncher.py. Every
    changed file is backed up first and the patched XML must parse before commit.
    """
    keymaps_root = keymaps_root or xbmcvfs.translatePath('special://profile/keymaps/')
    result={'changed_files':[],'backups':[],'errors':[],'reload_requested':False}
    if not os.path.isdir(keymaps_root):
        return result

    rx=re.compile(
        r'xbmc\.runscript\(([^)]*plugin\.program\.super\.favourites[/\\]capturelauncher\.py[^)]*)\)',
        re.I)
    backup_root=os.path.join(BACKUPS,'keymaps')
    os.makedirs(backup_root,exist_ok=True)
    stamp=time.strftime('%Y%m%d-%H%M%S')

    for fn in sorted(os.listdir(keymaps_root)):
        if not fn.lower().endswith('.xml'):
            continue
        src=os.path.join(keymaps_root,fn)
        if not os.path.isfile(src):
            continue
        try:
            original=read_text(src,2*1024*1024)
            if not original or not rx.search(original):
                continue
            patched=rx.sub(r'RunScript(\1)',original)
            ET.fromstring(patched)

            backup=os.path.join(backup_root,'%s.%s.bak' % (fn,stamp))
            shutil.copy2(src,backup)

            tmp=src+'.khc.tmp'
            with open(tmp,'w',encoding='utf-8') as f:
                f.write(patched)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp,src)
            result['changed_files'].append(src)
            result['backups'].append(backup)
        except Exception as e:
            result['errors'].append('%s: %s' % (fn,e))
            try:
                if os.path.exists(src+'.khc.tmp'):
                    os.remove(src+'.khc.tmp')
            except Exception:
                pass

    if result['changed_files'] and apply_reload:
        try:
            r=jsonrpc('Input.ExecuteAction',{'action':'reloadkeymaps'})
            result['reload_requested']=bool(isinstance(r,dict) and r.get('result')=='OK')
        except Exception as e:
            result['errors'].append('reloadkeymaps: %s' % e)
    return result


def fix_my_kodi():
    """Auto Repair rebuilt from scratch: local, bounded and UI-safe."""
    dlg = xbmcgui.Dialog()

    # Scan using the existing fast health detector only; repair logic below is new.
    try:
        current_lines=log_lines(include_old=False)
        issues = detect_issues(current_lines)
        runtime_active,_runtime_recovered = _runtime_findings(current_lines)
    except Exception as e:
        dlg.ok('Auto Repair', 'Could not read the current health scan.\n\n%s' % e)
        return

    health = max(0, 100 - ((len(issues) + len(runtime_active)) * 3))
    if not dlg.yesno(
        'Auto Repair',
        'Health: %d/100\n\nIssues identified: %d\n\n'
        'Run the rebuilt Auto Repair?\n\n'
        'Repository and dependency-source repairs stay manual.' %
        (health, len(issues))
    ):
        return

    progress = xbmcgui.DialogProgress()
    progress.create('Auto Repair', 'Starting safe repair pass...')
    repaired = []
    skipped = []
    errors = []

    # The rebuilt engine only performs short deterministic local operations.
    # It never scans 70+ repositories and never opens network catalogs.
    steps = [
        ('Refresh Kodi add-on state', 'refresh'),
        ('Clear stale package cache markers', 'packages'),
    ]
    if any((x or {}).get('key')=='tmdbdirs' for x in issues):
        steps.append(('Repair TMDb Helper working folders', 'tmdbdirs'))

    # The only keymap mutation allowed in Auto Repair is the exact malformed
    # Super Favourites action observed in the device diagnostic. Other keymap
    # problems stay diagnostic-only.
    sf_keymap_issue=any(
        (x or {}).get('key')=='keymap-invalid-action'
        and any('xbmc.runscript(' in str(s).lower() and 'capturelauncher.py' in str(s).lower()
                for s in ((x or {}).get('samples') or []))
        for x in runtime_active
    )
    if sf_keymap_issue:
        steps.append(('Repair legacy Super Favourites keymap action', 'keymap_sf'))

    steps += [
        ('Refresh repositories already installed', 'repos'),
        ('Recheck health', 'verify'),
    ]

    try:
        for i, (label, action) in enumerate(steps):
            if progress.iscanceled():
                progress.close()
                dlg.notification('Auto Repair', 'Canceled', xbmcgui.NOTIFICATION_INFO, 1800)
                return
            progress.update(int(i * 100 / len(steps)), label)

            try:
                if action == 'refresh':
                    xbmc.executebuiltin('UpdateLocalAddons')
                    repaired.append(label)

                elif action == 'packages':
                    # Do not delete packages blindly. Only remove Kodi's transient
                    # add-on temp folder contents when present.
                    temp_dir = xbmcvfs.translatePath('special://home/addons/temp/')
                    if xbmcvfs.exists(temp_dir):
                        dirs, files = xbmcvfs.listdir(temp_dir)
                        for f in files:
                            try:
                                xbmcvfs.delete(os.path.join(temp_dir, f))
                            except Exception:
                                pass
                        repaired.append(label)
                    else:
                        skipped.append(label)

                elif action == 'tmdbdirs':
                    base=xbmcvfs.translatePath('special://profile/addon_data/plugin.video.themoviedb.helper/')
                    made=[]
                    for name in ('log_tagger','log_library','timer_report'):
                        q=os.path.join(base,name)
                        os.makedirs(q,exist_ok=True)
                        if os.path.isdir(q): made.append(name)
                    if len(made)==3:
                        repaired.append(label)
                    else:
                        errors.append(label+': one or more folders could not be verified')

                elif action == 'keymap_sf':
                    km=_repair_super_favourites_keymaps()
                    if km.get('changed_files'):
                        repaired.append(label)
                    elif km.get('errors'):
                        errors.append(label+': '+str(km['errors'][0])[:160])
                    else:
                        skipped.append(label)

                elif action == 'repos':
                    # Ask Kodi to refresh installed repositories itself. No custom
                    # repository enumeration/crawling is performed.
                    xbmc.executebuiltin('UpdateAddonRepos')
                    repaired.append(label)

                elif action == 'verify':
                    xbmc.sleep(250)
                    try:
                        remaining = detect_issues()
                    except Exception:
                        remaining = issues
                    repaired.append(label)

            except Exception as e:
                errors.append('%s: %s' % (label, e))

            # Yield to Kodi between every operation so the UI remains responsive.
            xbmc.sleep(75)

        progress.update(100, 'Repair pass complete')
        xbmc.sleep(150)
        progress.close()

        try:
            remaining_count = len(remaining)
        except Exception:
            remaining_count = len(issues)

        result = [
            'Rebuilt Auto Repair complete.',
            '',
            'Repair steps completed: %d' % len(repaired),
            'Skipped: %d' % len(skipped),
            'Errors: %d' % len(errors),
            'Remaining health issues: %d' % remaining_count,
            '',
            'Missing dependencies/repository sources:',
            'Use Dependency Repair > Dependency Sources (A-Z).'
        ]
        if errors:
            result += ['', 'First error:', errors[0][:180]]
        dlg.ok('Auto Repair Results', '\n'.join(result))

    except Exception as e:
        try:
            progress.close()
        except Exception:
            pass
        dlg.ok('Auto Repair', 'Repair stopped safely.\n\n%s' % e)



def help_guide():
    topics=[
        ('Safety labels', 'SAFE = only low-risk maintenance that does not remove add-ons, repositories or user settings.\n\nCAUTION = changes Kodi state but is intended to be reversible, such as enabling/disabling a repository.\n\nADVANCED = can remove data or significantly change Kodi. Read the confirmation carefully.'),
        ('Add-on Doctor — SAFE', 'Checks installed addon.xml files, required dependencies and recent local install/update history. Crash Correlation compares timing only and never claims that correlation proves cause. Enabling a disabled dependency or opening repair options always requires your action.'),
        ('Auto Repair — SAFE', 'Runs a bounded local maintenance pass: refreshes Kodi add-on state, clears only the transient add-ons/temp file area, repairs the exact legacy Super Favourites keymap action when detected (backup first), requests a refresh of repositories already installed, then rescans current health. It does not auto-install repositories or dependencies; database/authentication/repository removal stays manual.'),
        ('Quick Clean — SAFE', 'One-tap cleanup for disposable Kodi clutter such as downloaded add-on packages, temporary/cache files and the old Kodi log. It does NOT remove installed add-ons, repositories, settings, databases, favorites or addon_data. It will not run during playback.'),
        ('Scan Kodi — SAFE', 'Reads Kodi logs and reports errors, known repository/noise entries, likely crashes or script failures, and actionable issues. Scanning does not change Kodi.'),
        ('Backup Kodi Configuration — SAFE', 'Creates a ZIP backup of Kodi userdata before larger changes. Disposable thumbnail/cache folders are skipped to keep the backup smaller. Stop playback before creating a backup.'),
        ('Manual Repair — CAUTION', 'Shows actionable problems found by Health Center. Each selected issue is locked to its own action. Safe folder repairs can be performed directly; missing dependencies are diagnosis-only; repository/add-on changes require confirmation.'),
        ('Add-on Dependencies — SAFE', 'Explains missing dependencies, locates them in repositories already installed in Kodi, and can download an exact dependency ZIP from that repository after you confirm. Downloads are verified to contain the requested add-on ID. Health Center never guesses an unknown website.'),
        ('Repository Manager — CAUTION', 'Shows installed repositories as ENABLED or DISABLED. You can enable/disable one repository or all repositories without uninstalling them. Remove is a separate backup-first action. Health Center can also restore repository backups it created.'),
        ('Repository Installer — CAUTION', 'Installs a repository from a repository ZIP URL or a local ZIP you choose. Health Center verifies that the ZIP identifies itself as a repository.* add-on and asks for confirmation before installing it. After installation Kodi repository data is refreshed.'),
        ('Enable / Disable All — CAUTION', 'Enable All turns every installed repository back on. Disable All turns repositories off but keeps them installed. Disabled repositories cannot provide updates/dependencies until re-enabled. Disable All requires confirmation.'),
        ('Clean Kodi (Advanced) — ADVANCED', 'Lets you choose individual cleanup categories instead of using Quick Clean. Use this when you want manual control over what is removed.'),
        ('Storage Info — SAFE', 'Shows device free space and the size of disposable Kodi package/temp areas. It does not increase physical storage; it helps identify Kodi data that may be safely reclaimed.'),
        ('Undo Last Repair — CAUTION', 'Reverses the last supported Health Center state change, such as restoring an add-on/repository to its previous enabled/disabled state. Not every operation can be automatically undone.'),
        ('Authorization Health — SAFE', 'Checks Account Manager Lite master authorization presence, Trakt target consistency, and recent refresh/auth failure or recovery markers. Credential values are compared only in memory and are never displayed, logged or exported. Use More Tools > Authorization Health.'),
        ('Send Logs for Help — SAFE', 'Creates a support ZIP containing Health Center/Kodi diagnostic information so a problem can be reviewed. Review logs before sharing if privacy is a concern; Authorization Health compares selected account fields in memory but does not include values in its report. Log redaction is best-effort.'),
        ('Health score', 'The health score is a simplified indicator based on issues detected by Health Center. Repository/configuration noise is separated from likely crashes. A lower score is a reason to inspect the report, not proof that Kodi is broken.'),
    ]
    while True:
        labels=[t[0] for t in topics]+['Back']
        i=xbmcgui.Dialog().select('Kodi Health Center — Help & Guide',labels)
        if i<0 or i>=len(topics): return
        xbmcgui.Dialog().ok(topics[i][0],topics[i][1])




def _repository_zip_info(zip_path):
    try:
        return repository_info(zip_path)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, ET.ParseError):
        return None


def _wait_for_addon_registration(addonid, timeout=12):
    """Ask Kodi to refresh local add-ons and wait until JSON-RPC can see addonid."""
    deadline=time.time()+timeout
    while time.time() < deadline:
        xbmc.executebuiltin('UpdateLocalAddons')
        xbmc.sleep(500)
        a=installed(addonid)
        if a:
            return a
    return None


def _verify_repository_registered(addonid):
    """Verify Kodi itself sees this add-on as a repository after installation."""
    a=installed(addonid)
    if not a:
        return False, 'Kodi did not register the repository add-on.'
    try:
        xml=read_text(os.path.join(ADDONS,addonid,'addon.xml'),512*1024)
        if 'xbmc.addon.repository' not in xml:
            return False, 'Installed add-on is not declared as a Kodi repository.'
    except Exception:
        return False, 'Could not verify repository metadata.'
    return True, ''


def _install_repository_zip(zip_path):
    """Stage first, preserve previous bytes, then verify the exact registered version."""
    info = _repository_zip_info(zip_path)
    dlg = xbmcgui.Dialog()
    if not info:
        dlg.ok('Repository Install Failed', 'The ZIP is not one safe, valid Kodi repository. Nothing was changed.')
        return False
    aid, name, ver = info['id'], info['name'], info['version']
    if xbmc.getCondVisibility('Player.HasMedia'):
        dlg.ok('Repository Install', 'Stop playback before replacing repository files.')
        return False
    prior_enabled = addon_enabled(aid)
    had_target = os.path.exists(os.path.join(ADDONS, aid))
    action = 'Replace/update' if had_target else 'Install'
    if not dlg.yesno(action + ' repository?', '%s\n%s\nVersion %s\n\n%s this repository? Previous files will be preserved.' % (name, aid, ver, action)):
        return False
    progress = xbmcgui.DialogProgress()
    def check_idle():
        if xbmc.getCondVisibility('Player.HasMedia') or progress.iscanceled():
            raise RuntimeError('Installation stopped because playback started or the operation was canceled')
    def verify(meta):
        progress.update(60, 'Registering repository with Kodi...')
        deadline = time.monotonic() + 12
        registered = None
        while time.monotonic() < deadline:
            check_idle()
            xbmc.executebuiltin('UpdateLocalAddons')
            xbmc.sleep(500)
            registered = installed(aid)
            if registered and str(registered.get('version', '')) == ver:
                break
        if not registered or str(registered.get('version', '')) != ver:
            raise RuntimeError('Kodi did not register the exact repository version')
        check_idle()
        if addon_enabled(aid) is not True and not set_enabled(aid, True, record=False):
            raise RuntimeError('Repository enabled state could not be verified')
        ok, reason = _verify_repository_registered(aid)
        if not ok:
            raise RuntimeError(reason)
        return True
    try:
        progress.create('Kodi Health Center', 'Staging and checking ' + name)
        receipt = replace_repository(zip_path, ADDONS, info, verify, check_idle)
    except Exception as exc:
        xbmc.executebuiltin('UpdateLocalAddons')
        state_note = ''
        if getattr(exc, 'restored', False) and prior_enabled is not None:
            if not set_enabled(aid, prior_enabled, record=False):
                state_note = '\nPrevious files restored; enabled state could not be confirmed.'
        recovery = getattr(exc, 'recovery_path', '')
        dlg.ok('Repository Install Failed', str(exc) + state_note +
               ('\nPreserved recovery files: ' + recovery if recovery else '\nExisting repository files were not replaced.'))
        return False
    finally:
        progress.close()
    # Refresh scheduling failure must not trigger rollback of a verified installation.
    refresh_note = ''
    try:
        xbmc.executebuiltin('UpdateAddonRepos')
    except Exception:
        refresh_note = '\nRepository refresh could not be requested.'
    dlg.ok('Repository Installed & Verified', name + '\n' + aid + '\nVersion ' + ver + refresh_note +
           ('\nPrevious files preserved at: ' + receipt['recovery_path'] if receipt['recovery_path'] else ''))
    return True


def install_repository_from_url():
    dlg=xbmcgui.Dialog()
    url=dlg.input('Repository ZIP URL',type=xbmcgui.INPUT_ALPHANUM).strip()
    if not url: return False
    try:
        parsed=urllib.parse.urlparse(url)
        if parsed.scheme not in ('https','http'):
            raise ValueError('Only HTTP/HTTPS repository ZIP URLs are supported')
        if parsed.scheme=='http' and not dlg.yesno('Unencrypted repository URL',
            'This URL uses HTTP instead of HTTPS.\n\nContinue anyway?'):
            return False
        tmpdir=os.path.join(PROFILE,'repo_downloads'); os.makedirs(tmpdir,exist_ok=True)
        tmp=os.path.join(tmpdir,'repository-download-%d.zip' % int(time.time()))
        progress=xbmcgui.DialogProgress(); progress.create('Dependency Sources (A-Z)','Downloading repository ZIP...')
        from khc_download import download_zip, DownloadCancelled
        try:
            download_zip(url, tmp, cancelled=progress.iscanceled,
                         progress=lambda got, total: progress.update(min(99, int(got*100/total)) if total else 0, 'Downloading repository ZIP...'))
        except DownloadCancelled:
            progress.close()
            return False
        progress.close()
        ok=_install_repository_zip(tmp)
        try: os.remove(tmp)
        except: pass
        return ok
    except Exception as e:
        try: progress.close()
        except: pass
        xbmcgui.Dialog().ok('Repository Download Failed','%s: %s' % (type(e).__name__,e))
        return False


def install_repository_from_local_zip():
    try:
        path=xbmcgui.Dialog().browseSingle(1,'Choose repository ZIP','files','.zip',False,False,'')
    except Exception:
        path=''
    if not path: return False
    path=xbmcvfs.translatePath(path)
    return _install_repository_zip(path)



EASY_REPO_ID='plugin.video.ezrepoinstaller'
ALIUNDE_REPO_ID='repository.aliunde'
ALIUNDE_REPO_ZIP='https://fuse99.com/aliunde/repository.aliunde-1.8.6.zip'

def _download_and_install_known_repository(url, label):
    """Download a known HTTPS repository ZIP, then use Health Center's verified installer."""
    tmpdir=os.path.join(PROFILE,'repo_downloads'); os.makedirs(tmpdir,exist_ok=True)
    tmp=os.path.join(tmpdir,'known-repository-%d.zip' % int(time.time()))
    progress=xbmcgui.DialogProgress()
    try:
        progress.create('Easy Repo Setup','Downloading %s...' % label)
        from khc_download import download_zip, DownloadCancelled
        try:
            download_zip(url, tmp, cancelled=progress.iscanceled,
                         progress=lambda got, total: progress.update(min(95, int(got*95/total)) if total else 0, 'Downloading %s...' % label))
        except DownloadCancelled:
            progress.close()
            return False
        progress.close()
        ok=_install_repository_zip(tmp)
        try: os.remove(tmp)
        except: pass
        return ok
    except Exception as e:
        try: progress.close()
        except: pass
        try:
            if os.path.exists(tmp): os.remove(tmp)
        except: pass
        xbmcgui.Dialog().ok('Easy Repo Setup Failed','Could not download %s.\n\n%s' % (label,e))
        return False




# v1.9.34 approved fallback repository catalog.
# These are explicit HTTPS repository ZIPs. Health Center does not add them blindly:
# it first inspects the repository metadata for the missing add-on ID, asks for approval,
# then installs only repositories that actually match.
APPROVED_REPO_CATALOG = [
    {
        'id':'repository.aliunde',
        'name':'Aliunde Repository',
        'zip':'https://fuse99.com/aliunde/repository.aliunde-1.8.6.zip'
    },
    {
        'id':'repository.kodifitzwell',
        'name':'kodifitzwell Repository',
        'zip':'https://kodifitzwell.github.io/repo/repository.kodifitzwell-0.0.1.zip'
    },
    {
        'id':'repository.jurialmunkey',
        'name':'jurialmunkey Alpha Repository',
        'zip':'https://jurialmunkey.github.io/repository.jurialmunkey/repository.jurialmunkey-3.4.zip'
    },
]

def _repo_zip_metadata_from_url(url, timeout=15):
    """Download a small repository ZIP into memory and return its repository declaration."""
    data = _fetch_bytes(url, timeout=timeout, limit=8*1024*1024)
    # Catalog inspection must apply the same ZIP path/member/uncompressed-size
    # gates as installation, before reading addon.xml into memory.
    from khc_safety import repository_info
    info = repository_info(io.BytesIO(data))
    with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
        xml = z.read(info['prefix'] + 'addon.xml')
    import xml.etree.ElementTree as ET
    root=ET.fromstring(xml)
    aid=root.attrib.get('id','')
    name=root.attrib.get('name') or aid
    endpoints=[]
    for ext in root.findall('extension'):
        if ext.attrib.get('point')!='xbmc.addon.repository':
            continue
        blocks=[ext]+list(ext.findall('dir'))
        for block in blocks:
            info=block.find('info'); datadir=block.find('datadir')
            iu=(info.text or '').strip() if info is not None else ''
            du=(datadir.text or '').strip() if datadir is not None else ''
            if iu and du:
                endpoints.append({'info':iu,'datadir':du})
    return {'id':aid,'name':name,'endpoints':endpoints,'bytes':data}



def _download_catalog_repo_to_temp(repo):
    tmpdir=os.path.join(PROFILE,'repo_downloads')
    os.makedirs(tmpdir,exist_ok=True)
    tmp=os.path.join(tmpdir,'%s-%d.zip' % (repo.get('id','repository.catalog'),int(time.time())))
    from khc_download import download_zip
    monitor = xbmc.Monitor()
    download_zip(repo['zip'], tmp, cancelled=monitor.abortRequested)
    return tmp

def install_catalog_repository(repo, reason=''):
    """Install one approved catalog repository after explicit user approval."""
    rid=repo.get('id'); name=repo.get('name') or rid
    if installed(rid):
        if addon_enabled(rid) is not True:
            set_enabled(rid,True,record=False)
        return True
    msg='%s\n\nRepository ID:\n%s' % (name,rid)
    if reason:
        msg+='\n\nNeeded for:\n%s' % reason
    msg+='\n\nInstall this approved repository and continue?'
    if not xbmcgui.Dialog().yesno('Repository required',msg):
        return False
    tmp=None
    try:
        tmp=_download_catalog_repo_to_temp(repo)
        return _install_repository_zip(tmp)
    except Exception as e:
        xbmcgui.Dialog().ok('Repository catalog','Could not install %s.\n\n%s' % (name,e))
        return False
    finally:
        try:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass

def approved_repository_catalog_menu():
    """Let the user inspect/install any approved fallback repository manually."""
    dlg=xbmcgui.Dialog()
    while True:
        labels=[]
        for r in APPROVED_REPO_CATALOG:
            state='INSTALLED' if installed(r['id']) else 'AVAILABLE'
            labels.append('[%s] %s' % (state,r['name']))
        labels.append('Back')
        i=dlg.select('Approved Repository Catalog',labels)
        if i<0 or i>=len(APPROVED_REPO_CATALOG):
            return
        r=APPROVED_REPO_CATALOG[i]
        if installed(r['id']):
            dlg.ok(r['name'],'Already installed and available to Kodi.')
            continue
        if dlg.yesno(r['name'],'Install this approved repository?\n\n%s' % r['id']):
            install_catalog_repository(r)


def repository_installer():
    """Built-in repository ZIP installer. Nothing is installed without confirmation."""
    while True:
        items=['Approved Repository Catalog','Install repository from ZIP URL','Install repository from local ZIP','Refresh installed repositories','Back']
        i=xbmcgui.Dialog().select('Dependency Sources (A-Z)',items)
        if i in (-1,4): return
        if i==0: approved_repository_catalog_menu()
        elif i==1: install_repository_from_url()
        elif i==2: install_repository_from_local_zip()
        elif i==3:
            xbmc.executebuiltin('UpdateLocalAddons'); xbmc.executebuiltin('UpdateAddonRepos')
            xbmcgui.Dialog().notification('Dependency Sources (A-Z)','Repository refresh requested',xbmcgui.NOTIFICATION_INFO,2000)



def export_installed_addon():
    """Export any installed Kodi add-on as a ZIP; optionally include its addon_data."""
    import os, zipfile, time
    import xml.etree.ElementTree as ET
    dlg=xbmcgui.Dialog()
    addons_root=xbmcvfs.translatePath('special://home/addons/')
    addon_data_root=xbmcvfs.translatePath('special://profile/addon_data/')
    if not os.path.isdir(addons_root):
        dlg.ok('Add-on Exporter','Kodi add-ons folder could not be accessed.')
        return

    rows=[]
    for addon_id in sorted(os.listdir(addons_root), key=str.lower):
        folder=os.path.join(addons_root,addon_id)
        xml=os.path.join(folder,'addon.xml')
        if not os.path.isdir(folder) or not os.path.isfile(xml):
            continue
        name=addon_id; version=''
        try:
            root=ET.parse(xml).getroot()
            name=root.attrib.get('name') or addon_id
            version=root.attrib.get('version') or ''
        except Exception:
            pass
        rows.append((addon_id,name,version,folder))
    if not rows:
        dlg.ok('Add-on Exporter','No installed add-ons were found.')
        return

    # Put Easy Repo Installer first for the current troubleshooting workflow.
    rows.sort(key=lambda r:(0 if r[0]=='plugin.video.ezrepoinstaller' else 1, r[1].lower()))
    labels=[]
    for aid,name,version,_ in rows:
        ver=(' v'+version) if version else ''
        labels.append('%s%s  [%s]'%(name,ver,aid))
    labels.append('Cancel')
    i=dlg.select('Add-on Exporter — choose installed add-on',labels)
    if i<0 or i>=len(rows): return
    addon_id,name,version,folder=rows[i]

    mode=dlg.select('What should be exported?',[
        'Add-on files only (recommended for sharing/inspection)',
        'Add-on files + saved settings/data',
        'Cancel'])
    if mode<0 or mode==2: return
    include_data=(mode==1)
    data_folder=os.path.join(addon_data_root,addon_id)
    data_exists=os.path.isdir(data_folder)
    if include_data and not data_exists:
        dlg.ok('Add-on Exporter','No saved addon_data folder exists for this add-on.\n\nThe add-on files will still be exported.')
        include_data=False

    what='add-on files + saved settings/data' if include_data else 'add-on files'
    if not dlg.yesno('Add-on Exporter','Export:\n\n%s\n%s\n\nContents: %s\n\nContinue?'%(name,addon_id,what)):
        return

    export_dir=xbmcvfs.translatePath('special://profile/addon_data/script.kodihealthcenter/exports/')
    os.makedirs(export_dir,exist_ok=True)
    safe_id=''.join(c if c.isalnum() or c in '._-' else '_' for c in addon_id)
    out=os.path.join(export_dir,'%s-export-%s.zip'%(safe_id,time.strftime('%Y%m%d-%H%M%S')))

    entries=[]
    def collect(src, arcroot):
        if not os.path.isdir(src): return
        for root,dirs,names in os.walk(src):
            dirs[:]=[d for d in dirs if d!='__pycache__']
            for fn in names:
                if fn.endswith(('.pyc','.pyo')): continue
                path=os.path.join(root,fn)
                rel=os.path.relpath(path,src).replace('\\','/')
                entries.append((path,arcroot+'/'+rel))
    collect(folder,addon_id)
    if include_data:
        collect(data_folder,'addon_data/'+addon_id)

    progress=xbmcgui.DialogProgress(); progress.create('Add-on Exporter','Preparing %s...'%name)
    try:
        total=max(1,len(entries))
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as zf:
            for n,(path,arcname) in enumerate(entries,1):
                if progress.iscanceled(): raise KeyboardInterrupt()
                zf.write(path,arcname)
                if n==1 or n%10==0 or n==total:
                    progress.update(int(n*100.0/total),'Exporting %s...\n%d of %d files'%(name,n,total))
        progress.close()
    except KeyboardInterrupt:
        try: progress.close()
        except: pass
        try: os.remove(out)
        except: pass
        dlg.ok('Export Canceled','Incomplete export removed.')
        return
    except Exception as e:
        try: progress.close()
        except: pass
        try: os.remove(out)
        except: pass
        dlg.ok('Export Failed','%s: %s'%(type(e).__name__,e)); return

    size=os.path.getsize(out) if os.path.exists(out) else 0
    choice=dlg.select('Add-on Exported — %.1f MB'%(size/1048576.0),[
        'Copy to a folder I choose',
        'Keep inside Kodi profile'])
    if choice==0:
        dest=dlg.browseSingle(3,'Choose export destination','files','',False,False,'')
        if dest:
            target=dest.rstrip('/\\')+'/'+os.path.basename(out)
            if xbmcvfs.copy(out,target):
                dlg.ok('Add-on Exported','Saved successfully:\n\n%s'%target); return
            dlg.ok('Copy Failed','Export was created, but Kodi could not copy it there.\n\nInternal copy:\n%s'%out); return
    dlg.ok('Add-on Exported','Export saved inside Kodi:\n\n%s'%out)



# ---- Infinity Clean-Core Skin Exporter 2.5.2 -------------------------------
def export_infinity_skin_package():
    """Read-only export of the installed clean-core Infinity skin and its saved data."""
    dlg = xbmcgui.Dialog()
    skin_id = 'skin.infinity'
    addons_root = xbmcvfs.translatePath('special://home/addons/')
    addon_data_root = xbmcvfs.translatePath('special://profile/addon_data/')
    skin_root = os.path.join(addons_root, skin_id)

    if not os.path.isdir(skin_root):
        dlg.ok('Infinity Skin Export',
               'skin.infinity was not found in Kodi add-ons.\n\n'
               'Install or select the clean-core Infinity skin, then run this exporter again.')
        return

    if not dlg.yesno('Infinity Skin Export',
        'Create a read-only ZIP of the installed Infinity skin?\n\n'
        'Included:\n- Complete skin.infinity files\n'
        '- skin.infinity saved skin data when present\n\n'
        'Nothing is changed or removed. Nothing uploads automatically.'):
        return

    export_dir = os.path.join(PROFILE, 'exports')
    os.makedirs(export_dir, exist_ok=True)
    target = os.path.join(
        export_dir,
        'Infinity-Clean-Core-Skin-Export-%s.zip' % time.strftime('%Y%m%d-%H%M%S')
    )

    entries = []
    omitted = []

    def collect(src, arcroot):
        if not os.path.isdir(src):
            omitted.append(src)
            return
        for base, dirs, names in os.walk(src):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for fn in names:
                if fn.endswith(('.pyc', '.pyo')):
                    continue
                path = os.path.join(base, fn)
                rel = os.path.relpath(path, src).replace('\\', '/')
                entries.append((path, arcroot + '/' + rel))

    collect(skin_root, skin_id)
    collect(os.path.join(addon_data_root, skin_id), 'addon_data/' + skin_id)

    manifest = {
        'export_type': 'Infinity clean-core skin source export',
        'health_center_version': xbmcaddon.Addon().getAddonInfo('version'),
        'skin_id': skin_id,
        'created_local': time.strftime('%Y-%m-%d %H:%M:%S'),
        'included_roots': [skin_id, 'addon_data/' + skin_id],
        'missing_optional_roots': omitted,
        'read_only_export': True
    }

    progress = xbmcgui.DialogProgress()
    progress.create('Infinity Skin Export', 'Collecting Infinity skin files...')
    try:
        total = max(1, len(entries))
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for n, (path, arcname) in enumerate(entries, 1):
                if progress.iscanceled():
                    raise KeyboardInterrupt()
                zf.write(path, arcname)
                if n == 1 or n % 25 == 0 or n == total:
                    progress.update(int(n * 100.0 / total),
                                    'Packing Infinity skin...\n%d of %d files' % (n, total))
            zf.writestr('INFINITY_CLEAN_CORE_EXPORT_MANIFEST.json',
                        json.dumps(manifest, indent=2, sort_keys=True))
        progress.close()
    except KeyboardInterrupt:
        try: progress.close()
        except: pass
        try: os.remove(target)
        except: pass
        dlg.ok('Infinity Skin Export', 'Export canceled. Incomplete ZIP removed.')
        return
    except Exception as e:
        try: progress.close()
        except: pass
        try: os.remove(target)
        except: pass
        dlg.ok('Infinity Skin Export', 'Export failed: %s: %s' % (type(e).__name__, e))
        return

    try:
        with zipfile.ZipFile(target, 'r') as zf:
            bad = zf.testzip()
            names = zf.namelist()
        if bad or not any(n.startswith(skin_id + '/') for n in names):
            raise ValueError('ZIP verification failed')
    except Exception as e:
        try: os.remove(target)
        except: pass
        dlg.ok('Infinity Skin Export', 'The ZIP did not pass verification: %s' % e)
        return

    size = os.path.getsize(target)
    choice = dlg.select(
        'Infinity Skin Export — %.1f MB' % (size / 1048576.0),
        ['Copy ZIP to a folder I choose', 'Keep inside Kodi profile']
    )
    if choice == 0:
        dest = dlg.browseSingle(3, 'Choose export destination', 'files', '', False, False, '')
        if dest:
            dest_path = dest.rstrip('/\\') + '/' + os.path.basename(target)
            if xbmcvfs.copy(target, dest_path) and xbmcvfs.exists(dest_path):
                dlg.ok('Infinity Skin Export', 'Export complete.\n\nSaved to:\n\n' + dest_path)
                return
            dlg.ok('Infinity Skin Export',
                   'Could not verify the copy. The original is still safe here:\n\n' + target)
            return

    dlg.ok('Infinity Skin Export', 'Export complete.\n\nSaved inside Kodi:\n\n' + target)


# ---- Add-on Doctor 2.5 ------------------------------------------------------
def _doctor_state():
    from khc_doctor import scan_addons
    return scan_addons(write=True)


def addon_doctor():
    from khc_doctor import scan_addons, install_events, crash_correlation, export_report
    dlg=xbmcgui.Dialog()
    while True:
        items=['Scan add-on health','Missing / disabled dependencies','Install & update history','Crash correlation','Export doctor report','Back']
        i=dlg.select('Add-on Doctor',items)
        if i<0 or i==5:return
        if i==0:
            state=scan_addons(write=True)
            msg='Installed add-ons: %d\nIssues: %d\nErrors: %d\nWarnings: %d\nOrphaned addon_data: %d' % (
                state.get('installed_count',0),state.get('issue_count',0),state.get('error_count',0),
                state.get('warning_count',0),len(state.get('orphaned_addon_data',[])))
            if not state.get('issues'):
                dlg.ok('Add-on Doctor',msg+'\n\nNo required dependency or addon.xml problems were found.')
                continue
            if dlg.yesno('Add-on Doctor',msg+'\n\nView issues?'):
                while True:
                    issues=state.get('issues',[])
                    labels=[('[ERROR] ' if x.get('severity')=='error' else '[WARN] ')+x.get('name',x.get('addon_id','?'))+' — '+x.get('kind','issue') for x in issues]
                    j=dlg.select('Add-on Doctor — Issues',labels+['Back'])
                    if j<0 or j>=len(issues):break
                    issue=issues[j]
                    dep=issue.get('dependency')
                    detail=issue.get('addon_id','?')+'\n\n'+issue.get('detail','')
                    if dep: detail+='\n\nDependency: '+dep
                    if issue.get('kind')=='missing-dependency' and dep:
                        if dlg.yesno('Missing Dependency',detail+'\n\nOpen Health Center dependency repair?'):
                            dependency_repair_menu({'id':dep,'version':'','optional':False},issue.get('addon_id'))
                    elif issue.get('kind')=='disabled-dependency' and dep:
                        if dlg.yesno('Disabled Dependency',detail+'\n\nEnable this dependency?'):
                            ok=set_enabled(dep,True)
                            dlg.notification('Add-on Doctor','Enabled '+dep if ok else 'Could not enable '+dep,xbmcgui.NOTIFICATION_INFO if ok else xbmcgui.NOTIFICATION_ERROR,3500)
                    else:
                        dlg.ok('Add-on Doctor',detail)
        elif i==1:
            state=scan_addons(write=True)
            issues=[x for x in state.get('issues',[]) if x.get('kind') in ('missing-dependency','disabled-dependency')]
            if not issues:
                dlg.ok('Dependencies','No missing or disabled required dependencies were found.');continue
            while True:
                labels=[x.get('addon_id','?')+' → '+x.get('dependency','?')+' ['+x.get('kind','')+']' for x in issues]
                j=dlg.select('Dependency Doctor',labels+['Back'])
                if j<0 or j>=len(issues):break
                issue=issues[j];dep=issue.get('dependency','')
                if issue.get('kind')=='missing-dependency':
                    dependency_repair_menu({'id':dep,'version':'','optional':False},issue.get('addon_id'))
                elif dlg.yesno('Enable Dependency?',issue.get('addon_id','?')+' requires '+dep+' but it is disabled.\n\nEnable it?'):
                    set_enabled(dep,True)
        elif i==2:
            events=install_events(120)
            if not events:
                dlg.ok('Install Diagnostics','No install/update changes have been recorded yet.\n\nThe 2.5 service begins recording after Infinity is restarted.');continue
            while True:
                labels=[]
                for e in events:
                    when=time.strftime('%m-%d %H:%M',time.localtime(int(e.get('timestamp',0) or 0)))
                    labels.append('%s  %s — %s' % (when,e.get('kind','changed').upper(),e.get('name') or e.get('addon_id','?')))
                j=dlg.select('Install & Update History',labels+['Back'])
                if j<0 or j>=len(events):break
                e=events[j]
                dlg.ok('Install Diagnostic', '%s\n\nEvent: %s\nBefore: %s\nAfter: %s\n\nThis is a local inventory observation, not a claim about why an add-on changed.' % (
                    e.get('addon_id','?'),e.get('kind','?'),e.get('version_before','-'),e.get('version_after','-')))
        elif i==3:
            c=crash_correlation()
            changes=c.get('correlated_changes',[])
            if not changes:
                dlg.ok('Crash Correlation',c.get('evidence_note','No correlation data is available.'));continue
            text=[c.get('evidence_note','') ,'']
            for x in changes:
                text.append('%s — %s min before start (%s)' % (x.get('name') or x.get('addon_id','?'),x.get('minutes_before_start','?'),x.get('evidence','?')))
            dlg.textviewer('Crash Correlation', '\n'.join(text), usemono=False)
        elif i==4:
            try:
                target=export_report();dlg.ok('Doctor Report','Saved:\n\n'+str(target))
            except Exception as e:
                dlg.ok('Doctor Report','Could not export: '+type(e).__name__)

# ---- Crash Center 2.2 -------------------------------------------------------
def _crash_dir():
    p=os.path.join(PROFILE,'crash_reports'); os.makedirs(p,exist_ok=True); return p

def _crash_reports():
    out=[]
    try:
        for n in os.listdir(_crash_dir()):
            if n.endswith('.json'):
                p=os.path.join(_crash_dir(),n)
                try:
                    with open(p,'r',encoding='utf-8') as f: d=json.load(f)
                    d['_path']=p; out.append(d)
                except: pass
    except: pass
    return sorted(out,key=lambda x:x.get('timestamp',''),reverse=True)

def crash_center():
    # The existing Crash Center menu now opens the bounded 2.3 recorder/exporter.
    from khc_kodi import crash_center as open_diagnostics
    open_diagnostics()


def _legacy_simple_mode():
    while True:
        items=['Scan Kodi','Crash Center','Start Fresh','Refresh Codes','Add-on Doctor','Auto Repair','Clean Mode','Repository Manager','Infinity Skin Export','Add-on Exporter','Send Logs for Help','More Tools','Help & Guide']
        i=xbmcgui.Dialog().select('Kodi Health Center ' + xbmcaddon.Addon().getAddonInfo('version'),items)
        if i==-1: return
        if i==0: check_kodi()
        elif i==1: crash_center()
        elif i==2:
            from khc_kodi import start_fresh
            start_fresh()
        elif i==3:
            from khc_kodi import refresh_codes
            refresh_codes()
        elif i==4: addon_doctor()
        elif i==5: fix_my_kodi()
        elif i==6: quick_clean()
        elif i==7: repository_manager()
        elif i==8: export_infinity_skin_package()
        elif i==9: export_installed_addon()
        elif i==10: support_package()
        elif i==11: advanced_mode()
        elif i==12: help_guide()


def _publish_dashboard_state():
    home=xbmcgui.Window(10000)
    try:
        scan=_scan_collect('dashboard-fresh-read')
        needs=scan.get('status')=='NEEDS ATTENTION'
        home.setProperty('KHC.Status','Needs attention' if needs else 'Healthy')
        home.setProperty('KHC.StatusDetail','Current verification needs attention' if needs else 'No current verified failures')
    except Exception:
        home.setProperty('KHC.Status','Unverified')
        home.setProperty('KHC.StatusDetail','Current health scan unavailable')
    try:
        when=time.localtime(os.path.getmtime(SCAN_STATE_FILE))
        home.setProperty('KHC.LastScan',time.strftime('%b %d, %I:%M %p',when))
    except Exception:
        home.setProperty('KHC.LastScan','Not scanned yet')
    try:
        path=os.path.join(PROFILE,'diagnostics-v3','baseline.json')
        with open(path,'r',encoding='utf-8') as f: baseline=json.load(f)
        epoch=float(baseline.get('epoch') or 0)
        if epoch:
            home.setProperty('KHC.Baseline','Fresh baseline • '+time.strftime('%b %d, %I:%M %p',time.localtime(epoch)))
        else:
            home.setProperty('KHC.Baseline','Crash baseline not set')
    except Exception:
        home.setProperty('KHC.Baseline','Crash baseline not set')
    try:
        home.setProperty('KHC.Version',xbmcaddon.Addon().getAddonInfo('version'))
    except Exception:
        pass


def _open_skin_dashboard():
    """Open the matched Infinity skin dashboard and return immediately.

    Do not poll getCurrentWindowId() here. ActivateWindow is asynchronous on Kodi's
    GUI thread; on-device the window can visibly open after this script's 120 ms
    check, which made 2.5.5 falsely assume failure and launch the legacy select menu
    on top of the real dashboard.
    """
    _publish_dashboard_state()
    xbmc.executebuiltin('ActivateWindow(1188)')
    return True


def _run_dashboard_command(command):
    commands={
        'scan':check_kodi,
        'crash':crash_center,
        'start-fresh':lambda:__import__('khc_kodi').start_fresh(),
        'refresh-codes':lambda:__import__('khc_kodi').refresh_codes(),
        'doctor':addon_doctor,
        'auto-repair':fix_my_kodi,
        'clean':quick_clean,
        'repositories':repository_manager,
        'skin-export':export_infinity_skin_package,
        'addon-export':export_installed_addon,
        'send-logs':support_package,
        'more-tools':advanced_mode,
        'authorization-health':authorization_health,
        'help':help_guide,
        'publish':_publish_dashboard_state,
    }
    fn=commands.get(command)
    if not fn:
        return False
    fn()
    _publish_dashboard_state()
    return True


def simple_mode():
    if _open_skin_dashboard():
        return
    _legacy_simple_mode()

def _khc_sha256(path, chunk=1024*1024):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        while True:
            b=f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()


def _khc_backup_files(src_root, arc_root, excluded_roots=None):
    """Return durable files only; caches, logs and our own backup output are excluded."""
    excluded_roots=[os.path.realpath(x) for x in (excluded_roots or [])]
    skip_names={'kodi.log','kodi.old.log','commoncache.db','textures13.db-shm','textures13.db-wal'}
    out=[]
    if not os.path.isdir(src_root): return out
    for root,dirs,files in os.walk(src_root):
        real_root=os.path.realpath(root)
        if any(real_root==x or real_root.startswith(x+os.sep) for x in excluded_roots):
            dirs[:]=[]; continue
        dirs[:]=[d for d in dirs if d not in ('cache','temp','Thumbnails','__pycache__')]
        for name in files:
            if name in skip_names or name.endswith(('-journal','-shm','-wal')): continue
            path=os.path.join(root,name)
            real_path=os.path.realpath(path)
            if any(real_path==x or real_path.startswith(x+os.sep) for x in excluded_roots): continue
            out.append((path,os.path.join(arc_root,os.path.relpath(path,src_root)).replace('\\','/')))
    return out


def _khc_snapshot_file(src, tmpdir):
    """No raw database fallback: an unsafe snapshot aborts the full backup."""
    return snapshot_file(src, tmpdir)


def _khc_read_manifest(zf):
    if 'KHC_BACKUP_MANIFEST.json' not in zf.namelist():
        raise ValueError('Not a Kodi Health Center full backup')
    manifest=json.loads(zf.read('KHC_BACKUP_MANIFEST.json').decode('utf-8','replace'))
    if manifest.get('format')!=2 or not isinstance(manifest.get('files'),dict):
        raise ValueError('Unsupported or incomplete Health Center backup format')
    return manifest


def verify_full_kodi_backup(path=None, quiet=False):
    dlg=xbmcgui.Dialog()
    if not path:
        path=dlg.browseSingle(1,'Select Kodi Full Backup ZIP','files','.zip',False,False,'')
    if not path: return None
    local=xbmcvfs.translatePath(path)
    try:
        with zipfile.ZipFile(local,'r') as zf:
            manifest=_khc_read_manifest(zf)
            names=set(zf.namelist())
            for arc,meta in manifest['files'].items():
                if arc not in names: raise ValueError('Backup is missing: '+arc)
                data=zf.read(arc)
                if hashlib.sha256(data).hexdigest()!=meta.get('sha256'):
                    raise ValueError('Backup checksum failed: '+arc)
        if not quiet:
            dlg.ok('Backup Verified','Archive checksums passed. This does not certify a complete restore or global database consistency.\n\nFiles: %d\nCreated: %s\nKodi: %s' % (
                len(manifest['files']),manifest.get('created','?'),manifest.get('kodi_build','?')))
        return local,manifest
    except Exception as e:
        if not quiet: dlg.ok('Backup Verification Failed','%s: %s' % (type(e).__name__,e))
        return None


def create_full_kodi_backup():
    """Capture checked individual SQLite snapshots; not a globally atomic app snapshot."""
    progress=None; zip_path=None; tmpdir=None; zip_created=False
    dlg=xbmcgui.Dialog()
    try:
        if not dlg.yesno('Create Complete Kodi Backup',
            'Backs up Kodi settings, databases, sources, favourites, add-ons and add-on data.\n\nCaches, thumbnails, logs and temporary files are excluded because they can be rebuilt.\n\nContinue?'):
            return
        profile=xbmcvfs.translatePath('special://profile/')
        addons=xbmcvfs.translatePath('special://home/addons/')
        exports=xbmcvfs.translatePath('special://profile/addon_data/script.kodihealthcenter/full_backups/')
        temp_root=xbmcvfs.translatePath('special://temp/')
        os.makedirs(exports,exist_ok=True)
        tmpdir=tempfile.mkdtemp(prefix='khc-backup-snapshot-', dir=temp_root)
        stamp=time.strftime('%Y%m%d-%H%M%S'); zip_path=os.path.join(exports,'Kodi_Complete_Backup_%s_%s.zip' % (stamp, uuid.uuid4().hex[:12]))
        files=_khc_backup_files(profile,'profile',[exports])+_khc_backup_files(addons,'addons',[exports])
        progress=xbmcgui.DialogProgress();progress.create('Kodi Health Center','Preparing complete backup...')
        manifest={'format':2,'created':time.strftime('%Y-%m-%d %H:%M:%S'),'kodi_build':xbmc.getInfoLabel('System.BuildVersion'),
                  'health_center_version':xbmcaddon.Addon().getAddonInfo('version'),'contains_profile':True,'contains_addons':True,'sqlite_snapshot_policy':'required-online-backup-quick-check','globally_atomic':False,
                  'excluded':['cache','temp','Thumbnails','logs','SQLite WAL/SHM files','Health Center full_backups'],'files':{}}
        with zipfile.ZipFile(zip_path,'x',zipfile.ZIP_DEFLATED,allowZip64=True) as zf:
            zip_created=True
            total=max(1,len(files))
            for i,(path,arc) in enumerate(files,1):
                if progress.iscanceled(): raise KeyboardInterrupt('Backup canceled')
                try:
                    stable,sqlite_snapshot=_khc_snapshot_file(path,tmpdir)
                    zf.write(stable,arc)
                    manifest['files'][arc]={'sha256':_khc_sha256(stable),'size':os.path.getsize(stable),'sqlite_snapshot':bool(sqlite_snapshot)}
                except Exception as e:
                    raise RuntimeError('Could not safely back up %s: %s' % (arc,e))
                if i==1 or i%10==0 or i==total:
                    progress.update(int(i*100.0/total),'Backing up Kodi...\n%d of %d files\n%s' % (i,total,os.path.basename(path)))
            zf.writestr('KHC_BACKUP_MANIFEST.json',json.dumps(manifest,indent=2,sort_keys=True))
        progress.close();progress=None
        verified=verify_full_kodi_backup(zip_path,quiet=True)
        if not verified: raise RuntimeError('Backup was written but failed its verification pass')
        size=os.path.getsize(zip_path); choice=dlg.select('Complete Backup Created',['Keep inside Kodi profile','Copy to a folder I choose'])
        if choice==1:
            dest=dlg.browseSingle(3,'Choose backup destination','files','',False,False,'')
            if dest:
                target=dest.rstrip('/\\')+'/'+os.path.basename(zip_path)
                if xbmcvfs.copy(zip_path,target):
                    dlg.ok('Complete Backup Created','Verified backup saved.\n\nFiles: %d\nSize: %.1f MB\n%s' % (len(manifest['files']),size/1048576.0,target)); return
        dlg.ok('Complete Backup Created','Verified backup completed.\n\nFiles: %d\nSize: %.1f MB\n%s' % (len(manifest['files']),size/1048576.0,zip_path))
    except KeyboardInterrupt:
        try:
            if progress: progress.close()
            if zip_created and zip_path and os.path.isfile(zip_path): os.remove(zip_path)
        except: pass
        dlg.ok('Backup Canceled','The incomplete backup was removed.')
    except Exception as e:
        try:
            if progress: progress.close()
            if zip_created and zip_path and os.path.isfile(zip_path): os.remove(zip_path)
        except: pass
        dlg.ok('Complete Backup Error','%s: %s' % (type(e).__name__,e))
    finally:
        if tmpdir: shutil.rmtree(tmpdir,ignore_errors=True)


def _infinity_restore_request_path():
    return os.path.join(PROFILE,'pending_complete_restore.json')


def _infinity_controller_restore_supported():
    """The future Controller advertises this only when it can restore before Kodi opens live state."""
    try:
        return xbmcgui.Window(10000).getProperty('Infinity.MaintenanceRestore')=='1'
    except Exception:
        return False


def restore_full_kodi_backup():
    """Queue an exact restore for the Infinity Controller maintenance/startup phase.

    Health Center deliberately refuses to overwrite live Kodi DB/settings in-process.
    That old behavior could produce a mixed state even when the copy appeared successful.
    """
    dlg=xbmcgui.Dialog(); selected=dlg.browseSingle(1,'Select Complete Kodi Backup ZIP','files','.zip',False,False,'')
    if not selected:return
    verified=verify_full_kodi_backup(selected,quiet=True)
    if not verified:
        dlg.ok('Restore Blocked','The selected backup did not pass Health Center integrity verification.');return
    local,manifest=verified
    if not _infinity_controller_restore_supported():
        dlg.ok('Exact Restore Not Available Yet',
               'This backup is valid, but Health Center will NOT overwrite live Kodi databases/settings while Kodi is running.\n\n'
               'Exact point-in-time restore requires the Infinity Controller maintenance-restore capability. That keeps restore outside Kodi\'s live database/session state.\n\n'
               'Your backup is safe to keep; restore will become available when that Controller capability is present.')
        return
    if not dlg.yesno('Queue Exact Restore',
                     'Restore Kodi to this exact Health Center snapshot?\n\nCreated: %s\nFiles: %d\n\nInfinity will apply it in maintenance mode and restart Kodi.' % (manifest.get('created','?'),len(manifest['files']))):
        return
    # The Controller consumes this request before normal live state is opened. No archive is extracted here.
    request={'format':1,'backup_zip':local,'backup_sha256':_khc_sha256(local),'requested':time.strftime('%Y-%m-%d %H:%M:%S'),
             'manifest_created':manifest.get('created'),'file_count':len(manifest['files'])}
    with open(_infinity_restore_request_path(),'w',encoding='utf-8') as f:json.dump(request,f,indent=2)
    xbmcgui.Window(10000).setProperty('Infinity.MaintenanceRestoreRequested','1')
    dlg.ok('Restore Queued','Exact restore has been queued for Infinity maintenance mode.\n\nKodi will close/restart when the Controller accepts the request.')


def recovery_menu():
    while True:
        items=['Create Complete Kodi Backup','Verify a Backup','Restore Complete Backup','Undo Last Change','Back']
        i=xbmcgui.Dialog().select('Backup & Recovery',items)
        if i in (-1,4):return
        if i==0:create_full_kodi_backup()
        elif i==1:verify_full_kodi_backup()
        elif i==2:restore_full_kodi_backup()
        elif i==3:undo_last_repair()

def advanced_mode():
    while True:
        items=['Authorization Health','Manual Repair','Add-on Dependencies','Storage Info','Backup & Recovery','Back']
        i=xbmcgui.Dialog().select('More Tools',items)
        if i in (-1,5): return
        if i==0: authorization_health()
        elif i==1: repairs()
        elif i==2: dependency_manager()
        elif i==3: storage_manager()
        elif i==4: recovery_menu()

def main():
    command=(sys.argv[1].strip().lower() if len(sys.argv)>1 else '')
    if command:
        if _run_dashboard_command(command):
            return
    simple_mode()

if __name__=='__main__': main()
