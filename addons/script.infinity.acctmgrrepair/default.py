# -*- coding: utf-8 -*-
"""Infinity Account Manager Repair 0.1.0

Tightly-scoped device patch for Account Manager Lite 1.1.6:
1) propagate the real Trakt refresh token instead of literal "1";
2) add AM Lite-owned traktAuthAll public action;
3) add deterministic all-installed-supported target list;
4) preserve exact preimages for rollback.

No tokens are read, logged, exported or copied by this repair add-on.
"""
import hashlib, json, os, shutil, sys, time
import xbmc, xbmcaddon, xbmcgui, xbmcvfs

TARGET="script.module.acctmgr"
SELF=xbmcaddon.Addon()
PROFILE=xbmcvfs.translatePath(SELF.getAddonInfo("profile"))
RECEIPT=os.path.join(PROFILE,"repair-receipt.json")

def sha(data): return hashlib.sha256(data.encode("utf-8")).hexdigest()

def read(path):
    with open(path,"r",encoding="utf-8") as f:return f.read()

def atomic_write(path,text):
    tmp=path+".infinity-tmp"
    with open(tmp,"w",encoding="utf-8",newline="") as f:f.write(text)
    compile(text,path,"exec")
    os.replace(tmp,path)

def target_root():
    try:
        a=xbmcaddon.Addon(TARGET)
        ver=a.getAddonInfo("version") or ""
        path=xbmcvfs.translatePath(a.getAddonInfo("path"))
        return a,ver,path
    except Exception:
        return None,"",""

def backup(paths,root,version):
    stamp=time.strftime("%Y%m%dT%H%M%S",time.gmtime())
    bdir=os.path.join(PROFILE,"backups",stamp)
    os.makedirs(bdir,exist_ok=True)
    rows={}
    for rel,path in paths.items():
        data=read(path)
        out=os.path.join(bdir,rel.replace("/","__"))
        with open(out,"w",encoding="utf-8",newline="") as f:f.write(data)
        rows[rel]={"backup":out,"sha256":sha(data)}
    return bdir,{"target_version":version,"target_root":root,"created_at":int(time.time()),"files":rows}

def patch_sync(text):
    old="your_refresh = '1'"
    new="your_refresh = acctmgr.getSetting(\"trakt.refresh\")"
    if new in text:return text,False
    if text.count(old)!=1:raise RuntimeError("Unexpected AM Lite trakt_sync.py preimage")
    return text.replace(old,new,1),True

ALL_METHOD=r'''
    def create_all_list(self):
        """Save every installed target already supported by this AM Lite build."""
        addon_list = []
        def add_if(path, name):
            if xbmcvfs.exists(path) and name not in addon_list:
                addon_list.append(name)

        add_if(var.chk_nxtflixlt, 'NXTFlix Light')
        add_if(var.chk_gears, 'The Gears')
        add_if(var.chk_red, 'Red Light')
        add_if(var.chk_umb, 'Umbrella')
        add_if(var.chk_pov, 'POV')
        add_if(var.chk_coal, 'The Coalition')
        add_if(var.chk_genocide, 'Genocide')
        add_if(var.chk_shadow, 'Shadow')
        add_if(var.chk_ghost, 'Ghost')
        add_if(var.chk_chains, 'The Chains')
        add_if(var.chk_home, 'Homelander')
        add_if(var.chk_night, 'Nightwing')
        add_if(var.chk_absol, 'Jokers Absolution')
        add_if(var.chk_scrubs, 'Scrubs V2')
        add_if(var.chk_redg, 'Gratis Red')
        add_if(var.chk_crew, 'The Crew')
        add_if(var.chk_salts, 'SALTS')
        add_if(var.chk_tmdbh, 'TMDb Helper')
        add_if(var.chk_trakt, 'Trakt Addon')

        if not addon_list:
            control.notification('Account Manager Lite', 'No supported Trakt add-ons found!', icon=trakt_icon)
            return []

        if not xbmcvfs.exists(var.acctmgr_datapath):
            xbmcvfs.mkdirs(var.acctmgr_datapath)
        try:
            with open(var.tk_sync_list, 'w') as synclist:
                json.dump({'addon_list': addon_list}, synclist, indent=4)
        except Exception as e:
            log_utils.error(f"Failed to save all-installed Trakt sync list: {e}")
            return []

        control.notification('Account Manager Lite', 'All installed Trakt targets selected!', icon=trakt_icon)
        return addon_list

'''

def patch_select(text):
    if "def create_all_list(self):" in text:return text,False
    anchor="class tk_list():\n\tdef create_list(self):"
    if anchor not in text:raise RuntimeError("Unexpected AM Lite trakt_select.py preimage")
    method=ALL_METHOD.replace("    ","\t")
    return text.replace("class tk_list():\n", "class tk_list():\n"+method,1),True

ALL_ACTION=r'''
elif action == 'traktAuthAll':
        # Infinity public action: authorize once and sync every installed target that
        # this exact AM Lite build already supports. AM Lite remains credential owner.
        from acctmgr.modules.sync import trakt_select
        installed = trakt_select.tk_list().create_all_list()
        if not installed:
                control.notification('Account Manager Lite', 'No supported Trakt targets found!', icon=trakt_icon)
                raise SystemExit

        from acctmgr.modules.auth import trakt
        if not control.setting('trakt.token') or not control.setting('trakt.refresh'):
                ok = trakt.Trakt().auth()
                if not ok:
                        control.notification('Account Manager Lite', 'Trakt authorization did not complete.', icon=trakt_icon)
                        raise SystemExit

        get_acctmgr().setSetting("api.service", "true")
        control.setSetting('api.stop', 'false')
        xbmc.sleep(500)

        from acctmgr.modules.sync import trakt_sync
        trakt_sync.Auth().trakt_auth(mode="auth")
        control.notification('Account Manager Lite', 'Trakt synced to all installed supported add-ons.', icon=trakt_icon)
        xbmc.sleep(500)
        control.updates_off()
        dialog.ok('Infinity Authorization & Accounts',
                  'Trakt authorization and sync completed. Restart Infinity once, then run Kodi Health Center Authorization Health.')

'''

def patch_default(text):
    if "action == 'traktAuthAll'" in text:return text,False
    anchor="elif action == 'traktAuth':"
    if text.count(anchor)!=1:raise RuntimeError("Unexpected AM Lite default.py preimage")
    return text.replace(anchor,ALL_ACTION+anchor,1),True

def apply():
    addon,version,root=target_root()
    if not addon:
        xbmcgui.Dialog().ok("Infinity Account Manager Repair","Account Manager Lite is not installed.")
        return
    if not version.startswith("1.1.6"):
        xbmcgui.Dialog().ok("Infinity Account Manager Repair",
            "This repair is scoped to Account Manager Lite 1.1.6. Installed version: "+version)
        return
    paths={
      "lib/acctmgr/modules/sync/trakt_sync.py":os.path.join(root,"lib","acctmgr","modules","sync","trakt_sync.py"),
      "lib/acctmgr/modules/sync/trakt_select.py":os.path.join(root,"lib","acctmgr","modules","sync","trakt_select.py"),
      "lib/default.py":os.path.join(root,"lib","default.py"),
    }
    for rel,p in paths.items():
        if not os.path.isfile(p):raise RuntimeError("Missing target file: "+rel)

    originals={rel:read(p) for rel,p in paths.items()}
    new_sync,c1=patch_sync(originals["lib/acctmgr/modules/sync/trakt_sync.py"])
    new_sel,c2=patch_select(originals["lib/acctmgr/modules/sync/trakt_select.py"])
    new_def,c3=patch_default(originals["lib/default.py"])

    if not any((c1,c2,c3)):
        xbmcgui.Dialog().ok("Infinity Account Manager Repair","Repair is already applied.")
        return

    bdir,receipt=backup(paths,root,version)
    try:
        atomic_write(paths["lib/acctmgr/modules/sync/trakt_sync.py"],new_sync)
        atomic_write(paths["lib/acctmgr/modules/sync/trakt_select.py"],new_sel)
        atomic_write(paths["lib/default.py"],new_def)
    except Exception:
        for rel,row in receipt["files"].items():
            shutil.copy2(row["backup"],paths[rel])
        raise

    receipt["status"]="applied"
    receipt["fixes"]=[
      "real Trakt refresh token propagation",
      "public traktAuthAll action",
      "all installed supported Trakt target selection",
      "no forced process exit in traktAuthAll path"
    ]
    receipt["after"]={rel:sha(read(p)) for rel,p in paths.items()}
    os.makedirs(PROFILE,exist_ok=True)
    with open(RECEIPT,"w",encoding="utf-8") as f:json.dump(receipt,f,indent=2,sort_keys=True)

    xbmcgui.Dialog().ok("Infinity Account Manager Repair",
        "Repair applied successfully.\n\nAccount Manager Lite now has Trakt Everywhere support and propagates the real refresh token.\n\nRestart Infinity once.")

def rollback():
    if not os.path.isfile(RECEIPT):
        xbmcgui.Dialog().ok("Infinity Account Manager Repair","No repair receipt/backup is available.")
        return
    data=json.load(open(RECEIPT,"r",encoding="utf-8"))
    _,_,root=target_root()
    if not root:return
    if not xbmcgui.Dialog().yesno("Infinity Account Manager Repair","Restore the exact pre-repair AM Lite files?"):return
    for rel,row in data.get("files",{}).items():
        dst=os.path.join(root,*rel.split("/"))
        shutil.copy2(row["backup"],dst)
    xbmcgui.Dialog().ok("Infinity Account Manager Repair","Exact pre-repair AM Lite files restored. Restart Infinity.")

def main():
    action="apply"
    for arg in sys.argv[1:]:
        if arg.startswith("action="):action=arg.split("=",1)[1]
    try:
        if action=="rollback":rollback()
        else:apply()
    except Exception as e:
        xbmc.log("InfinityAcctMgrRepair: "+repr(e),xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Infinity Account Manager Repair",
            "Repair stopped safely: "+str(e)+"\n\nNo unknown AM Lite source was modified.")

if __name__=="__main__":main()
