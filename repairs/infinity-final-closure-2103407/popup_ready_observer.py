"""Observe actual popup rows within its original readiness budget."""
import time

BEFORE="                ui.select_native_item(50,lambda:xbmc.getInfoLabel('Container(50).ListItem.Label')==label,label)"
AFTER="""                from popup_ready_observer import wait_rows
                wait_rows(xbmc,xbmcgui,ui,began,result)
"""+BEFORE


def wait_rows(xbmc,xbmcgui,ui,began,result):
    remaining=90-(time.monotonic()-began)
    if remaining<=0:raise AssertionError('Original popup readiness deadline expired')
    def ready():
        dialog=xbmcgui.getCurrentWindowDialogId()
        count=int(xbmc.getInfoLabel('Container(50).NumItems') or 0)
        value=dict(dialog=dialog,count=count,
            popup=xbmcgui.Window(dialog).getProperty('Infinity.UI.Popup'),
            focus=xbmc.getCondVisibility('Control.HasFocus(50)'))
        result['popup_readiness_observation']=value
        return value if value['popup']=='1' and 0<count<=1000 and value['focus'] else None
    value=ui.until(ready,'actual selected popup rows/focus',remaining)
    value['actual_row_labels']=[xbmc.getInfoLabel('Container(50).ListItemAbsolute(%d).Label'%i)
                                for i in range(value['count']+1)]
    value['deadline_monotonic']=began+90
    return value


def instrument(text):
    if text.count(BEFORE)!=1:raise ValueError('Original selected popup boundary differs')
    return text.replace(BEFORE,AFTER,1)


def restore(text):return text.replace(AFTER,BEFORE,1)
