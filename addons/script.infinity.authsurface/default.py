# -*- coding: utf-8 -*-
"""Infinity Authorization & Accounts 0.5.0.

Infinity front door for Account Manager Lite plus the narrowly-scoped Trakt
refresh-token repair. Credentials remain owned by Account Manager Lite.
"""
import hashlib, json, os, shutil, time
import xbmc, xbmcaddon, xbmcgui, xbmcvfs
from repair_core import patch_sync, patch_select, patch_default, source_status

OWNER="script.module.acctmgr"
SELF=xbmcaddon.Addon()
PROFILE=xbmcvfs.translatePath(SELF.getAddonInfo("profile"))
RECEIPT=os.path.join(PROFILE,"am-lite-trakt-repair-receipt.json")

SERVICES=[
 ("⚡ Trakt Everywhere","traktAuthAll","traktReSyncAll"),
 ("Real-Debrid Everywhere","realdebridAuth","realdebridReSync"),
 ("Premiumize","premiumizeAuth","premiumizeReSync"),
 ("All-Debrid","alldebridAuth","alldebridReSync"),
 ("TorBox","torboxAuth","torboxReSync"),
 ("OffCloud","offcloudAuth","offcloudReSync"),
 ("Easynews","easynewsAuth","easynewsReSync"),
 ("MDBList","mdblistAuth","mdblistReSync"),
]

def ready():
    return xbmc.getCondVisibility("System.HasAddon(%s)"%OWNER)

def run(action):
    if not ready():
        xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Account Manager Lite 1.1.6 is required.")
        return False
    xbmc.executebuiltin("RunScript(%s, action=%s)"%(OWNER,action))
    return True

def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _read(path):
    with open(path,"r",encoding="utf-8") as f:
        return f.read()

def _atomic_write(path,text):
    compile(text,path,"exec")
    tmp=path+".infinity-tmp"
    with open(tmp,"w",encoding="utf-8",newline="") as f:
        f.write(text)
    os.replace(tmp,path)

def _target():
    try:
        addon=xbmcaddon.Addon(OWNER)
        return addon, addon.getAddonInfo("version") or "", xbmcvfs.translatePath(addon.getAddonInfo("path"))
    except Exception:
        return None,"",""

def _paths(root):
    return {
      "lib/acctmgr/modules/sync/trakt_sync.py":os.path.join(root,"lib","acctmgr","modules","sync","trakt_sync.py"),
      "lib/acctmgr/modules/sync/trakt_select.py":os.path.join(root,"lib","acctmgr","modules","sync","trakt_select.py"),
      "lib/default.py":os.path.join(root,"lib","default.py"),
    }

def repair_status(show=False):
    addon,version,root=_target()
    if not addon:
        status="AM Lite missing"
    elif not version.startswith("1.1.6"):
        status="Unsupported AM Lite version: "+version
    else:
        try:
            p=_paths(root)
            sync=_read(p["lib/acctmgr/modules/sync/trakt_sync.py"])
            sel=_read(p["lib/acctmgr/modules/sync/trakt_select.py"])
            default=_read(p["lib/default.py"])
            state=source_status(sync,sel,default)
            status={
              "APPLIED":"APPLIED — real refresh token + Trakt Everywhere active",
              "READY":"READY — AM Lite 1.1.6 recognized; repair not yet applied",
              "PARTIAL":"PARTIAL — repair markers are incomplete; use Rollback or re-apply from a clean AM Lite 1.1.6",
              "UNSUPPORTED":"UNSUPPORTED — source does not match the audited AM Lite 1.1.6 shapes",
            }[state]
        except Exception as e:
            status="Status check failed safely: "+str(e)
    if show:
        extra="\n\nA rollback backup is available." if os.path.isfile(RECEIPT) else "\n\nNo Infinity rollback backup is currently recorded."
        xbmcgui.Dialog().ok("Trakt Repair Status",status+extra)
    return status

def apply_repair():
    addon,version,root=_target()
    if not addon:
        xbmcgui.Dialog().ok("Trakt Repair","Account Manager Lite is not installed.")
        return False
    if not version.startswith("1.1.6"):
        xbmcgui.Dialog().ok("Trakt Repair","Repair is scoped to Account Manager Lite 1.1.6. Installed: "+version)
        return False
    paths=_paths(root)
    try:
        originals={rel:_read(path) for rel,path in paths.items()}
        state=source_status(
            originals["lib/acctmgr/modules/sync/trakt_sync.py"],
            originals["lib/acctmgr/modules/sync/trakt_select.py"],
            originals["lib/default.py"])
        if state=="APPLIED":
            xbmcgui.Dialog().ok("Trakt Repair","Repair is already applied.")
            return True
        if state=="PARTIAL":
            raise RuntimeError("Partial repair detected. Roll back first or reinstall clean AM Lite 1.1.6.")
        if state=="UNSUPPORTED":
            raise RuntimeError("Installed AM Lite source does not match the audited 1.1.6 repair signatures.")

        new_sync,_=patch_sync(originals["lib/acctmgr/modules/sync/trakt_sync.py"])
        new_sel,_=patch_select(originals["lib/acctmgr/modules/sync/trakt_select.py"])
        new_default,_=patch_default(originals["lib/default.py"])

        # Compile every transformed Python file before touching the installation.
        compile(new_sync,paths["lib/acctmgr/modules/sync/trakt_sync.py"],"exec")
        compile(new_sel,paths["lib/acctmgr/modules/sync/trakt_select.py"],"exec")
        compile(new_default,paths["lib/default.py"],"exec")

        os.makedirs(PROFILE,exist_ok=True)
        stamp=time.strftime("%Y%m%dT%H%M%S",time.gmtime())
        backup_dir=os.path.join(PROFILE,"am-lite-backups",stamp)
        os.makedirs(backup_dir,exist_ok=True)
        receipt={"target_version":version,"created_at":int(time.time()),"files":{}}
        for rel,path in paths.items():
            backup=os.path.join(backup_dir,rel.replace("/","__"))
            with open(backup,"w",encoding="utf-8",newline="") as f:
                f.write(originals[rel])
            receipt["files"][rel]={"backup":backup,"pre_sha256":_sha(originals[rel])}

        try:
            _atomic_write(paths["lib/acctmgr/modules/sync/trakt_sync.py"],new_sync)
            _atomic_write(paths["lib/acctmgr/modules/sync/trakt_select.py"],new_sel)
            _atomic_write(paths["lib/default.py"],new_default)
        except Exception:
            for rel,row in receipt["files"].items():
                shutil.copy2(row["backup"],paths[rel])
            raise

        for rel,path in paths.items():
            receipt["files"][rel]["post_sha256"]=_sha(_read(path))
        receipt["status"]="applied"
        with open(RECEIPT,"w",encoding="utf-8") as f:
            json.dump(receipt,f,indent=2,sort_keys=True)

        xbmcgui.Dialog().ok("Trakt Repair",
          "Applied successfully.\n\nThe real Trakt refresh token will now propagate to AM Lite-supported add-ons, and Trakt Everywhere can select all supported installed targets.\n\nRestart Infinity once before using Trakt Everywhere.")
        return True
    except Exception as e:
        xbmc.log("InfinityAuthSurface repair stopped: "+repr(e),xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Trakt Repair",
          "Repair stopped safely. "+str(e)+"\n\nNo unknown AM Lite source was modified.")
        return False

def rollback_repair():
    if not os.path.isfile(RECEIPT):
        xbmcgui.Dialog().ok("Trakt Repair","No Infinity repair backup is available.")
        return False
    if not xbmcgui.Dialog().yesno("Trakt Repair","Restore the exact pre-repair Account Manager Lite files?"):
        return False
    try:
        data=json.load(open(RECEIPT,"r",encoding="utf-8"))
        addon,version,root=_target()
        if not addon:
            raise RuntimeError("Account Manager Lite is not installed.")
        paths=_paths(root)
        for rel,row in data.get("files",{}).items():
            backup=row.get("backup")
            if not backup or not os.path.isfile(backup):
                raise RuntimeError("Rollback backup is incomplete.")
        for rel,row in data["files"].items():
            shutil.copy2(row["backup"],paths[rel])
        data["status"]="rolled_back"
        data["rolled_back_at"]=int(time.time())
        with open(RECEIPT,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=2,sort_keys=True)
        xbmcgui.Dialog().ok("Trakt Repair","Exact pre-repair AM Lite files restored. Restart Infinity once.")
        return True
    except Exception as e:
        xbmcgui.Dialog().ok("Trakt Repair","Rollback stopped: "+str(e))
        return False

def repair_menu():
    while True:
        i=xbmcgui.Dialog().select("Trakt Repair & Status",[
          "Check repair status",
          "Apply / repair Account Manager Lite",
          "Rollback Infinity repair",
          "Back"])
        if i<0 or i==3:return
        if i==0:repair_status(show=True)
        elif i==1:apply_repair()
        elif i==2:rollback_repair()

def trakt_menu(name,auth,sync):
    status=repair_status(show=False)
    if not status.startswith("APPLIED"):
        if xbmcgui.Dialog().yesno("Trakt Everywhere",
          "The AM Lite Trakt backend repair is not active.\n\nApply it now inside Authorization & Accounts?"):
            if apply_repair():
                return
        else:
            return
    j=xbmcgui.Dialog().select(name,[
      "Authorize / Reauthorize Trakt everywhere",
      "ReSync current Trakt authorization everywhere",
      "Repair / status / rollback",
      "Back"])
    if j==0:run(auth)
    elif j==1:run(sync)
    elif j==2:repair_menu()

def main():
    if not ready():
        xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Account Manager Lite is not installed or enabled.")
        return
    labels=[x[0] for x in SERVICES]+["🛠 Trakt Repair & Status","Open Account Manager Lite"]
    i=xbmcgui.Dialog().select("Infinity Authorization & Accounts",labels)
    if i<0:return
    if i==len(SERVICES):
        repair_menu();return
    if i==len(SERVICES)+1:
        xbmc.executebuiltin("RunAddon(%s)"%OWNER);return
    name,auth,sync=SERVICES[i]
    if i==0:
        trakt_menu(name,auth,sync)
        return
    j=xbmcgui.Dialog().select(name,["Authorize / Reauthorize","ReSync installed add-ons","Back"])
    if j==0:run(auth)
    elif j==1:run(sync)

if __name__=="__main__":
    main()
