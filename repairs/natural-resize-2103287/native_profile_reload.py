#!/usr/bin/env python3
"""Make Kodi re-evaluate the active skin resolution profile after Android window aspect changes.

The Android bridge already publishes settled SurfaceView dimensions and the render thread already
commits those dimensions. Kodi 21.3, however, keeps each loaded CGUIWindow's m_coordsRes/profile
from the time that XML was first loaded. GUI_MSG_WINDOW_RESIZE only reaches child controls; it does
not re-run CSkinInfo::GetSkinPath. On a Fold/orientation transition that leaves a portrait/16:9/etc
XML profile active against a different window aspect, producing stretched or crushed UI.

This patch does not invent a layout. It reloads the same window XML from the profile Kodi itself
now considers closest to the committed window size. Existing control state is saved/restored, no
window deinit/init action is run, and media list objects remain owned by their window.
"""
from pathlib import Path
import argparse, hashlib, json

H=Path("xbmc/guilib/GUIWindow.h")
C=Path("xbmc/guilib/GUIWindow.cpp")
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def once(s,a,b,label):
    n=s.count(a)
    if n!=1: raise RuntimeError(f"{label}: expected one anchor, got {n}")
    return s.replace(a,b,1)

def patch_h(s):
    s=once(s,
"""  bool NeedLoad() const;

  virtual void SetDefaults();
""",
"""  bool NeedLoad() const;
  // Android window geometry can cross a skin aspect/profile boundary without a skin reload.
  // Defer the actual XML profile swap until DoProcess, outside the resize-message iteration.
  bool InfinitySkinProfileChanged() const;
  void InfinityReloadSkinProfile();

  virtual void SetDefaults();
""","declarations")
    s=once(s,
"""  bool m_custom;

private:
""",
"""  bool m_custom;
  bool m_infinityProfileReloadPending{false};

private:
""","pending member")
    return s

def patch_cpp(s):
    anchor="""bool CGUIWindow::NeedLoad() const
{
  return !m_windowLoaded || CServiceBroker::GetGUI()->GetInfoManager().ConditionsChangedValues(m_xmlIncludeConditions);
}

"""
    methods=anchor+"""bool CGUIWindow::InfinitySkinProfileChanged() const
{
  if (!m_windowLoaded || !g_SkinInfo)
    return false;

  const std::string xmlFile = GetProperty("xmlfile").asString();
  if (xmlFile.empty() || xmlFile.find('\\\\') != std::string::npos ||
      xmlFile.find('/') != std::string::npos)
    return false; // explicit/custom paths have no skin-resolution routing contract

  RESOLUTION_INFO next;
  const std::string path = g_SkinInfo->GetSkinPath(xmlFile, &next);
  if (path.empty())
    return false;

  return next.strMode != m_coordsRes.strMode || next.iWidth != m_coordsRes.iWidth ||
         next.iHeight != m_coordsRes.iHeight ||
         std::fabs(next.fPixelRatio - m_coordsRes.fPixelRatio) > 0.0001f;
}

void CGUIWindow::InfinityReloadSkinProfile()
{
  if (!m_infinityProfileReloadPending)
    return;
  m_infinityProfileReloadPending = false;
  if (!InfinitySkinProfileChanged())
    return;

  const std::string previousMode = m_coordsRes.strMode;
  const int previousFocus = GetFocusedControlID();

  // Keep the window active and its higher-level model/list ownership intact. Rebuild only the
  // skin controls/XML so Load() asks CSkinInfo for the profile matching the *current* window.
  SaveControlStates();
  FreeResources(true);
  AllocResources(true);
  if (!m_windowLoaded)
  {
    CLog::Log(LOGERROR, "Infinity natural resize: failed to reload window {} after profile change",
              GetID());
    return;
  }
  RestoreControlStates();
  SetInitialVisibility();
  if (previousFocus && GetControl(previousFocus))
    SET_CONTROL_FOCUS(previousFocus, 0);

  CLog::Log(LOGINFO, "Infinity natural resize: window {} skin profile {} -> {} ({}x{})",
            GetID(), previousMode, m_coordsRes.strMode, m_coordsRes.iWidth, m_coordsRes.iHeight);
}

"""
    s=once(s,anchor,methods,"reload methods")
    s=once(s,
"""void CGUIWindow::DoProcess(unsigned int currentTime, CDirtyRegionList &dirtyregions)
{
  if (!IsControlDirty() && CServiceBroker::GetSettingsComponent()->GetAdvancedSettings()->m_guiSmartRedraw)
""",
"""void CGUIWindow::DoProcess(unsigned int currentTime, CDirtyRegionList &dirtyregions)
{
  // Geometry is committed by CWinSystemAndroid on Kodi's main/render loop. If that commit crossed
  // a skin profile boundary, rebuild the controls once before processing the next frame.
  InfinityReloadSkinProfile();

  if (!IsControlDirty() && CServiceBroker::GetSettingsComponent()->GetAdvancedSettings()->m_guiSmartRedraw)
""","DoProcess")
    old="""        if (message.GetParam1() == GUI_MSG_PAGE_CHANGE ||
          message.GetParam1() == GUI_MSG_REFRESH_THUMBS ||
          message.GetParam1() == GUI_MSG_REFRESH_LIST ||
          message.GetParam1() == GUI_MSG_WINDOW_RESIZE)
        { // alter the message accordingly, and send to all controls
"""
    new="""        if (message.GetParam1() == GUI_MSG_WINDOW_RESIZE && InfinitySkinProfileChanged())
        {
          // Never rebuild controls while WindowManager is broadcasting the resize. A single
          // latest-window profile reload is consumed by DoProcess on this window's next frame.
          m_infinityProfileReloadPending = true;
          MarkDirtyRegion(DIRTY_STATE_CHILD);
        }

        if (message.GetParam1() == GUI_MSG_PAGE_CHANGE ||
          message.GetParam1() == GUI_MSG_REFRESH_THUMBS ||
          message.GetParam1() == GUI_MSG_REFRESH_LIST ||
          message.GetParam1() == GUI_MSG_WINDOW_RESIZE)
        { // alter the message accordingly, and send to all controls
"""
    s=once(s,old,new,"resize notification")
    return s

def verify(root):
    h=(root/H).read_text(); c=(root/C).read_text()
    required=[
      "bool InfinitySkinProfileChanged() const;",
      "bool m_infinityProfileReloadPending{false};",
      "void CGUIWindow::InfinityReloadSkinProfile()",
      "g_SkinInfo->GetSkinPath(xmlFile, &next)",
      "FreeResources(true);",
      "AllocResources(true);",
      "RestoreControlStates();",
      "message.GetParam1() == GUI_MSG_WINDOW_RESIZE && InfinitySkinProfileChanged()",
      "InfinityReloadSkinProfile();",
    ]
    for token in required:
        if token not in h+c: raise RuntimeError("missing natural-resize contract: "+token)
    if "RunLoadActions();" in c[c.index("void CGUIWindow::InfinityReloadSkinProfile()"):c.index("void CGUIWindow::AllocResources")]:
        raise RuntimeError("profile reload must not replay window onload actions")
    return {"schema":1,"kodi":"21.3-Omega","owner":"CGUIWindow profile routing after committed geometry",
            "reload_deferred_outside_resize_broadcast":True,"preserves_window_model":True,
            "preserves_control_state":True,"runs_window_load_actions":False,
            "files":{str(H):sha(root/H),str(C):sha(root/C)}}

def main():
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["apply","verify"]);p.add_argument("--source",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);a=p.parse_args()
    root=a.source.resolve()
    if a.mode=="apply":
        hp=root/H;cp=root/C
        hp.write_text(patch_h(hp.read_text()))
        cp.write_text(patch_cpp(cp.read_text()))
    result=verify(root);a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("PASS: Kodi window XML profile follows committed Android window aspect without full skin reload")
if __name__=="__main__":main()
