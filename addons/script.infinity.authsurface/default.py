# -*- coding: utf-8 -*-
import json
import xbmc, xbmcaddon, xbmcgui, xbmcvfs

OWNER="script.module.acctmgr"

SERVICES=[
 ("⚡ Authorize Trakt Everywhere","trakt_everywhere",None),
 ("Authorize Debrid & Trakt",None,None),
 ("Trakt","traktAuth","traktReSync"),
 ("Real-Debrid","realdebridAuth","realdebridReSync"),
 ("Premiumize","premiumizeAuth","premiumizeReSync"),
 ("All-Debrid","alldebridAuth","alldebridReSync"),
 ("TorBox","torboxAuth","torboxReSync"),
 ("OffCloud","offcloudAuth","offcloudReSync"),
 ("Easynews","easynewsAuth","easynewsReSync"),
 ("MDBList","mdblistAuth","mdblistReSync"),
]

def owner_ready():
 return xbmc.getCondVisibility("System.HasAddon(%s)"%OWNER)

def run(action):
 if not owner_ready():
  xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Account Manager Lite is required for authorization.")
  return
 xbmc.executebuiltin("RunScript(%s, action=%s)"%(OWNER,action))

def authorize_trakt_everywhere():
 """Use AM Lite's own supported-target map, but select every installed target automatically."""
 if not owner_ready():
  xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Account Manager Lite is required.")
  return
 try:
  from acctmgr.modules import var, control
  from acctmgr.modules.auth import trakt
  from acctmgr.modules.sync import trakt_sync

  targets=[
   ("NXTFlix Light",var.chk_nxtflixlt),("The Gears",var.chk_gears),("Red Light",var.chk_red),
   ("Umbrella",var.chk_umb),("POV",var.chk_pov),("The Coalition",var.chk_coal),
   ("Genocide",var.chk_genocide),("Shadow",var.chk_shadow),("Ghost",var.chk_ghost),
   ("The Chains",var.chk_chains),("Homelander",var.chk_home),("Nightwing",var.chk_night),
   ("Jokers Absolution",var.chk_absol),("Scrubs V2",var.chk_scrubs),("Gratis Red",var.chk_redg),
   ("The Crew",var.chk_crew),("SALTS",var.chk_salts),("TMDb Helper",var.chk_tmdbh),
   ("Trakt Addon",var.chk_trakt),
  ]
  installed=[name for name,path in targets if xbmcvfs.exists(path)]
  if not installed:
   xbmcgui.Dialog().ok("Infinity Authorization & Accounts","No AM Lite-supported Trakt targets are installed.")
   return

  preview="\n".join("• "+x for x in installed)
  if not xbmcgui.Dialog().yesno("Authorize Trakt Everywhere",
      "Infinity found %d compatible installed targets.\n\n%s\n\nAuthorize and sync all of them?"%(len(installed),preview)):
   return

  if not xbmcvfs.exists(var.acctmgr_datapath):
   xbmcvfs.mkdirs(var.acctmgr_datapath)
  with xbmcvfs.File(var.tk_sync_list,"w") as fh:
   fh.write(json.dumps({"addon_list":installed},indent=2))

  acct=xbmcaddon.Addon(OWNER)
  # Authorize only when the owner has no complete current pair. Otherwise use its current
  # authorization and simply synchronize every installed supported target.
  token=acct.getSetting("trakt.token")
  refresh=acct.getSetting("trakt.refresh")
  if not (token and refresh):
   ok=trakt.Trakt().auth()
   if not ok:
    xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Trakt authorization was cancelled or did not complete.")
    return

  acct.setSetting("api.service","true")
  control.setSetting("api.stop","false")
  trakt_sync.Auth().trakt_auth(mode="auth")

  # Verify target participation without reading/exporting any token values.
  xbmcgui.Dialog().ok("Infinity Authorization & Accounts",
      "Trakt authorization/sync completed for %d installed targets.\n\nRestart Infinity once, then Health Center can verify refresh behavior."%len(installed))
 except Exception as e:
  xbmc.log("InfinityAuthSurface: Trakt Everywhere failed: %s"%type(e).__name__,xbmc.LOGERROR)
  xbmcgui.Dialog().ok("Infinity Authorization & Accounts",
      "Trakt Everywhere could not complete. Nothing was revoked.\n\nUse the individual Trakt option or send a Health Center diagnostic ZIP.")

def main():
 i=xbmcgui.Dialog().select("Infinity Authorization & Accounts",[x[0] for x in SERVICES])
 if i<0:return
 if i==0:
  authorize_trakt_everywhere(); return
 if i==1:
  j=xbmcgui.Dialog().select("Authorize Debrid & Trakt",["Trakt","Real-Debrid","Back"])
  if j==0:run("traktAuth")
  elif j==1:run("realdebridAuth")
  return
 name,auth,sync=SERVICES[i]
 j=xbmcgui.Dialog().select(name,["Authorize / Reauthorize","ReSync installed add-ons","Open Account Manager Lite"])
 if j==0:run(auth)
 elif j==1:run(sync)
 elif j==2:xbmc.executebuiltin("RunAddon(%s)"%OWNER)

if __name__=="__main__":main()
