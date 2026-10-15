import os,sys
sys.dont_write_bytecode=True
import xbmcaddon,xbmcgui,xbmcvfs
from collector import IDS,export

def main():
    dialog=xbmcgui.Dialog()
    if not dialog.yesno('Recover shutdown evidence',
      'Read the existing native critical traces and source hashes of the eight pending services? '
      'No new Close test is required. No installed add-on, setting or user data is changed.'):
        return
    roots={}
    for addon_id in IDS:
        try:roots[addon_id]=xbmcvfs.translatePath(xbmcaddon.Addon(addon_id).getAddonInfo('path'))
        except Exception:pass
    destination=dialog.browseSingle(3,'Choose local output folder','local','',False,False,'')
    if not destination:return
    try:
        trace_root='/data/data/com.projectinfinity.kodi/files'
        output=export(xbmcvfs.translatePath(destination),roots,trace_root)
        dialog.ok('Evidence saved',os.path.basename(output)+'\nShare this ZIP. This is evidence recovery, not a shutdown repair.')
    except Exception:
        dialog.ok('Capture unavailable','The allowlisted files or output folder could not be accessed. '
          'Keep your session open. No force close or data reset is required by this tool.')
if __name__=='__main__':main()
