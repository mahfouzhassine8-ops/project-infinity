# -*- coding: utf-8 -*-
import xbmc, xbmcaddon, xbmcgui
OWNER="script.module.acctmgr"
SERVICES=[
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
def run(action):
 if not xbmc.getCondVisibility("System.HasAddon(%s)"%OWNER):
  xbmcgui.Dialog().ok("Infinity Authorization & Accounts","Account Manager Lite is required for authorization.")
  return
 xbmc.executebuiltin("RunScript(%s, action=%s)"%(OWNER,action))
def main():
 i=xbmcgui.Dialog().select("Infinity Authorization & Accounts",[x[0] for x in SERVICES])
 if i<0:return
 if i==0:
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
