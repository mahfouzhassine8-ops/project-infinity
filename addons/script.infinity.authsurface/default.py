# -*- coding: utf-8 -*-
"""Infinity Authorization & Accounts 0.3.0.
Public-API-only integration with Account Manager Lite. No imports of AM Lite internals.
"""
import xbmc, xbmcgui

OWNER="script.module.acctmgr"
SERVICES=[
 ("⚡ Trakt Everywhere","traktAuthAll","traktReSync"),
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
  xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Account Manager Lite 1.1.6 is required for this authorization surface.")
  return False
 xbmc.executebuiltin("RunScript(%s, action=%s)"%(OWNER,action))
 return True
def main():
 if not ready():
  xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Account Manager Lite is not installed or enabled.")
  return
 i=xbmcgui.Dialog().select("Infinity Authorization & Accounts",[x[0] for x in SERVICES]+["Open Account Manager Lite"])
 if i<0:return
 if i==len(SERVICES):
  xbmc.executebuiltin("RunAddon(%s)"%OWNER);return
 name,auth,sync=SERVICES[i]
 if i==0:
  # AM Lite owns target selection and credential propagation. Infinity invokes only its
  # supported public action; no private acctmgr imports, no credential reads/writes.
  xbmcgui.Dialog().ok("Trakt Everywhere",
   "Infinity will open Account Manager Lite's supported Trakt authorization flow.\n\n"
   "On the target screen, use Select all if your Kodi dialog provides it; otherwise AM Lite "
   "will preserve previously selected targets. After authorization, return here and use ReSync.")
 j=xbmcgui.Dialog().select(name,["Authorize / Reauthorize","ReSync installed add-ons","Back"])
 if j==0:run(auth)
 elif j==1:run(sync)
if __name__=="__main__":main()
