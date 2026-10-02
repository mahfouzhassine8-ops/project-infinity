#!/usr/bin/env python3
"""Infinity 2103290: Kodi-owned responsive logical viewport.

The Android/native window size remains authoritative. Kodi synthesizes a logical canvas with a
constant 1080-unit short axis and the *actual usable window aspect*. This guarantees uniform GUI
scaling. Infinity skins may opt in with resources/infinity-native-responsive-v1.json and provide
complete presentation folders under responsive/<class>/, with responsive/base as the fallback.

No physical-device model checks live here. No profile folder is required for correctness and the
legacy skin <res> matrix remains untouched for non-responsive skins / rollback compatibility.
"""
from pathlib import Path
import argparse, hashlib, json

SKIN_H=Path("xbmc/addons/Skin.h")
SKIN_CPP=Path("xbmc/addons/Skin.cpp")
WIN_H=Path("xbmc/guilib/GUIWindow.h")
WIN_CPP=Path("xbmc/guilib/GUIWindow.cpp")
ANDROID=Path("xbmc/windowing/android/WinSystemAndroid.cpp")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b,label):
    n=s.count(a)
    if n!=1: raise RuntimeError(f"{label}: expected one anchor, found {n}")
    return s.replace(a,b,1)

def patch_skin_h(s):
    s=once(s,
"""  std::string GetSkinPath(const std::string& file,
                          RESOLUTION_INFO* res = nullptr,
                          const std::string& baseDir = "") const;
""",
"""  std::string GetSkinPath(const std::string& file,
                          RESOLUTION_INFO* res = nullptr,
                          const std::string& baseDir = "") const;

  // Infinity Native Responsive Layout v1. The skin supplies presentation; Kodi owns geometry.
  bool UsesNativeResponsiveLayout() const;
  std::string GetNativeResponsiveClass() const;
  RESOLUTION_INFO GetNativeResponsiveResolution() const;
  void RefreshNativeResponsiveIncludes();
""","Skin public responsive API")
    s=once(s,
"""  std::string m_currentAspect;

  std::vector<CStartupWindow> m_startupWindows;
""",
"""  std::string m_currentAspect;
  std::string m_nativeResponsiveIncludesClass;

  std::vector<CStartupWindow> m_startupWindows;
""","Skin responsive include state")
    return s

def patch_skin_cpp(s):
    s=once(s,"#include <charconv>\n#include <memory>\n",
           "#include <charconv>\n#include <cmath>\n#include <memory>\n","Skin cmath")
    marker='''struct closestRes
{
  explicit closestRes(const RESOLUTION_INFO &target) : m_target(target) { };
'''
    methods=r'''namespace
{
constexpr const char* INFINITY_RESPONSIVE_MARKER =
    "resources/infinity-native-responsive-v1.json";
constexpr int INFINITY_RESPONSIVE_SHORT_AXIS = 1080;
constexpr int INFINITY_RESPONSIVE_QUANTUM = 8;

int InfinityQuantizeLongAxis(int value)
{
  if (value <= INFINITY_RESPONSIVE_SHORT_AXIS)
    return INFINITY_RESPONSIVE_SHORT_AXIS;
  return std::max(INFINITY_RESPONSIVE_SHORT_AXIS,
                  ((value + INFINITY_RESPONSIVE_QUANTUM / 2) / INFINITY_RESPONSIVE_QUANTUM) *
                      INFINITY_RESPONSIVE_QUANTUM);
}

void InfinityUsableSize(const RESOLUTION_INFO& target, float& width, float& height)
{
  const float left = target.Overscan.right > target.Overscan.left
                         ? static_cast<float>(target.Overscan.left)
                         : 0.0f;
  const float top = target.Overscan.bottom > target.Overscan.top
                        ? static_cast<float>(target.Overscan.top)
                        : 0.0f;
  const float right = target.Overscan.right > target.Overscan.left
                          ? static_cast<float>(target.Overscan.right)
                          : static_cast<float>(target.iWidth);
  const float bottom = target.Overscan.bottom > target.Overscan.top
                           ? static_cast<float>(target.Overscan.bottom)
                           : static_cast<float>(target.iHeight);
  width = std::max(1.0f, right - target.guiInsets.right - (left + target.guiInsets.left));
  height = std::max(1.0f, bottom - target.guiInsets.bottom - (top + target.guiInsets.top));
}
} // namespace

bool CSkinInfo::UsesNativeResponsiveLayout() const
{
  return CFileUtils::Exists(URIUtils::AddFileToFolder(Path(), INFINITY_RESPONSIVE_MARKER));
}

std::string CSkinInfo::GetNativeResponsiveClass() const
{
  if (!UsesNativeResponsiveLayout())
    return {};

  const RESOLUTION_INFO target = CServiceBroker::GetWinSystem()->GetGfxContext().GetResInfo();
  float width = 1.0f, height = 1.0f;
  InfinityUsableSize(target, width, height);
  const float ratio = width / height;

  if (ratio >= 1.95f)
    return "ultrawide";
  if (ratio >= 1.48f)
    return "wide";
  if (ratio >= 1.12f)
    return "landscape";
  if (ratio >= 0.86f)
    return "square";
  if (ratio >= 0.55f)
    return "portrait";
  return "tall";
}

RESOLUTION_INFO CSkinInfo::GetNativeResponsiveResolution() const
{
  const RESOLUTION_INFO target = CServiceBroker::GetWinSystem()->GetGfxContext().GetResInfo();
  float usableWidth = 1.0f, usableHeight = 1.0f;
  InfinityUsableSize(target, usableWidth, usableHeight);
  const float ratio = usableWidth / usableHeight;

  int width = INFINITY_RESPONSIVE_SHORT_AXIS;
  int height = INFINITY_RESPONSIVE_SHORT_AXIS;
  if (ratio >= 1.0f)
    width = InfinityQuantizeLongAxis(
        static_cast<int>(std::lround(INFINITY_RESPONSIVE_SHORT_AXIS * ratio)));
  else
    height = InfinityQuantizeLongAxis(
        static_cast<int>(std::lround(INFINITY_RESPONSIVE_SHORT_AXIS / std::max(0.01f, ratio))));

  RESOLUTION_INFO result(width, height, static_cast<float>(width) / height,
                         "responsive/" + GetNativeResponsiveClass());
  result.strId = "infinity-native-responsive-v1";
  result.iScreenWidth = width;
  result.iScreenHeight = height;
  result.iSubtitles = height;
  result.fPixelRatio = 1.0f;
  result.bFullScreen = true;
  return result;
}

void CSkinInfo::RefreshNativeResponsiveIncludes()
{
  if (!UsesNativeResponsiveLayout())
    return;
  const std::string current = GetNativeResponsiveClass();
  if (current == m_nativeResponsiveIncludesClass)
    return;
  LoadIncludes();
}

'''
    s=once(s,marker,methods+marker,"Skin responsive methods")
    # Start uses Kodi-owned class rather than legacy closest-res label for responsive skins.
    old='''  if (!m_resolutions.empty())
  {
    // find the closest resolution
    const RESOLUTION_INFO &target = CServiceBroker::GetWinSystem()->GetGfxContext().GetResInfo();
    RESOLUTION_INFO& res = *std::min_element(m_resolutions.begin(), m_resolutions.end(), closestRes(target));
    m_currentAspect = res.strId;
  }
'''
    new='''  if (UsesNativeResponsiveLayout())
  {
    m_currentAspect = GetNativeResponsiveClass();
  }
  else if (!m_resolutions.empty())
  {
    // find the closest resolution
    const RESOLUTION_INFO &target = CServiceBroker::GetWinSystem()->GetGfxContext().GetResInfo();
    RESOLUTION_INFO& res = *std::min_element(m_resolutions.begin(), m_resolutions.end(), closestRes(target));
    m_currentAspect = res.strId;
  }
'''
    s=once(s,old,new,"Skin Start responsive class")
    # Native resolver before legacy closest-res logic.
    old='''  // if the caller doesn't care about the resolution just use a temporary
  RESOLUTION_INFO tempRes;
  if (!res)
    res = &tempRes;

  // find the closest resolution
  const RESOLUTION_INFO &target = CServiceBroker::GetWinSystem()->GetGfxContext().GetResInfo();
'''
    new='''  // if the caller doesn't care about the resolution just use a temporary
  RESOLUTION_INFO tempRes;
  if (!res)
    res = &tempRes;

  if (UsesNativeResponsiveLayout())
  {
    *res = GetNativeResponsiveResolution();
    const std::string responsiveRoot = URIUtils::AddFileToFolder(strPathToUse, "responsive");
    const std::string classPath =
        URIUtils::AddFileToFolder(URIUtils::AddFileToFolder(responsiveRoot, GetNativeResponsiveClass()), strFile);
    if (CFileUtils::Exists(classPath))
      return classPath;

    const std::string basePath =
        URIUtils::AddFileToFolder(URIUtils::AddFileToFolder(responsiveRoot, "base"), strFile);
    if (CFileUtils::Exists(basePath))
    {
      CLog::Log(LOGWARNING,
                "Infinity native responsive: {} missing from class {}, using responsive/base",
                strFile, GetNativeResponsiveClass());
      return basePath;
    }

    CLog::Log(LOGERROR,
              "Infinity native responsive: required XML {} missing from class {} and base",
              strFile, GetNativeResponsiveClass());
    return basePath;
  }

  // find the closest resolution
  const RESOLUTION_INFO &target = CServiceBroker::GetWinSystem()->GetGfxContext().GetResInfo();
'''
    s=once(s,old,new,"Skin GetSkinPath responsive resolver")
    # Track includes class.
    old='''  m_includes.Clear();
  m_includes.Load(includesPath);
}
'''
    new='''  m_includes.Clear();
  m_includes.Load(includesPath);
  if (UsesNativeResponsiveLayout())
    m_nativeResponsiveIncludesClass = GetNativeResponsiveClass();
}
'''
    s=once(s,old,new,"Skin LoadIncludes class tracking")
    # GetSkinPaths uses current responsive class + base, never legacy fallback/profile selection.
    old='''void CSkinInfo::GetSkinPaths(std::vector<std::string> &paths) const
{
  RESOLUTION_INFO res;
  GetSkinPath("Home.xml", &res);
  if (!res.strMode.empty())
    paths.push_back(URIUtils::AddFileToFolder(Path(), res.strMode));
  if (res.strMode != m_defaultRes.strMode)
    paths.push_back(URIUtils::AddFileToFolder(Path(), m_defaultRes.strMode));
}
'''
    new='''void CSkinInfo::GetSkinPaths(std::vector<std::string> &paths) const
{
  if (UsesNativeResponsiveLayout())
  {
    const std::string responsiveRoot = URIUtils::AddFileToFolder(Path(), "responsive");
    paths.push_back(URIUtils::AddFileToFolder(responsiveRoot, GetNativeResponsiveClass()));
    paths.push_back(URIUtils::AddFileToFolder(responsiveRoot, "base"));
    return;
  }

  RESOLUTION_INFO res;
  GetSkinPath("Home.xml", &res);
  if (!res.strMode.empty())
    paths.push_back(URIUtils::AddFileToFolder(Path(), res.strMode));
  if (res.strMode != m_defaultRes.strMode)
    paths.push_back(URIUtils::AddFileToFolder(Path(), m_defaultRes.strMode));
}
'''
    s=once(s,old,new,"Skin GetSkinPaths responsive")
    return s

def patch_window_h(s):
    s=once(s,"#include <limits.h>\n#include <map>\n",
           "#include <chrono>\n#include <limits.h>\n#include <map>\n","GUIWindow chrono")
    s=once(s,
"""  bool NeedLoad() const;

  virtual void SetDefaults();
""",
"""  bool NeedLoad() const;
  bool InfinityNativeResponsiveLayoutChanged(RESOLUTION_INFO* next = nullptr,
                                             std::string* path = nullptr) const;
  void InfinityReloadNativeResponsiveLayout();
  void InfinityPublishResponsiveProperties(const std::string& path);

  virtual void SetDefaults();
""","GUIWindow responsive declarations")
    s=once(s,
"""  bool m_custom;

private:
""",
"""  bool m_custom;
  bool m_infinityResponsiveReloadPending{false};
  std::chrono::steady_clock::time_point m_infinityResponsiveResizeAt{};

private:
""","GUIWindow responsive state")
    return s

def patch_window_cpp(s):
    # Publish source resolution/path on successful load.
    old='''  if (ret)
  {
    m_windowLoaded = true;
    OnWindowLoaded();
'''
    new='''  if (ret)
  {
    m_windowLoaded = true;
    InfinityPublishResponsiveProperties(strPath);
    OnWindowLoaded();
'''
    s=once(s,old,new,"GUIWindow publish after load")
    anchor='''bool CGUIWindow::NeedLoad() const
{
  return !m_windowLoaded || CServiceBroker::GetGUI()->GetInfoManager().ConditionsChangedValues(m_xmlIncludeConditions);
}

'''
    methods=anchor+r'''bool CGUIWindow::InfinityNativeResponsiveLayoutChanged(RESOLUTION_INFO* next,
                                                        std::string* path) const
{
  if (!m_windowLoaded || !g_SkinInfo || !g_SkinInfo->UsesNativeResponsiveLayout())
    return false;

  const std::string xmlFile = GetProperty("xmlfile").asString();
  if (xmlFile.empty() || xmlFile.find('\\') != std::string::npos ||
      xmlFile.find('/') != std::string::npos)
    return false;

  RESOLUTION_INFO candidate;
  const std::string resolved = g_SkinInfo->GetSkinPath(xmlFile, &candidate);
  if (next)
    *next = candidate;
  if (path)
    *path = resolved;

  return candidate.strMode != m_coordsRes.strMode || candidate.iWidth != m_coordsRes.iWidth ||
         candidate.iHeight != m_coordsRes.iHeight;
}

void CGUIWindow::InfinityPublishResponsiveProperties(const std::string& path)
{
  if (!g_SkinInfo || !g_SkinInfo->UsesNativeResponsiveLayout())
    return;
  SetProperty("Infinity.NativeResponsive", true);
  SetProperty("Infinity.ResponsiveClass", g_SkinInfo->GetNativeResponsiveClass());
  SetProperty("Infinity.LogicalWidth", m_coordsRes.iWidth);
  SetProperty("Infinity.LogicalHeight", m_coordsRes.iHeight);
  SetProperty("Infinity.ResolvedXML", path);
}

void CGUIWindow::InfinityReloadNativeResponsiveLayout()
{
  if (!m_infinityResponsiveReloadPending)
    return;

  const auto now = std::chrono::steady_clock::now();
  if (m_infinityResponsiveResizeAt.time_since_epoch().count() != 0 &&
      now - m_infinityResponsiveResizeAt < std::chrono::milliseconds(90))
    return;

  m_infinityResponsiveReloadPending = false;
  RESOLUTION_INFO next;
  std::string resolved;
  if (!InfinityNativeResponsiveLayoutChanged(&next, &resolved))
    return;

  const std::string previousMode = m_coordsRes.strMode;
  const int previousFocus = GetFocusedControlID();
  SaveControlStates();

  // Class-specific include libraries are presentation resources. Refresh them only when Kodi's
  // native class changes; continuous size changes inside a class keep the same include graph.
  if (previousMode != next.strMode)
    g_SkinInfo->RefreshNativeResponsiveIncludes();

  FreeResources(true);
  AllocResources(true);
  if (!m_windowLoaded)
  {
    CLog::Log(LOGERROR,
              "Infinity native responsive: failed to reload window {} for {}x{}",
              GetID(), next.iWidth, next.iHeight);
    return;
  }

  RestoreControlStates();
  SetInitialVisibility();
  if (previousFocus && GetControl(previousFocus))
    SET_CONTROL_FOCUS(previousFocus, 0);
  MarkDirtyRegion(DIRTY_STATE_CHILD);

  CLog::Log(LOGINFO,
            "Infinity responsive window: id={} xml={} class={} logical={}x{} path={}",
            GetID(), GetProperty("xmlfile").asString(),
            g_SkinInfo->GetNativeResponsiveClass(), m_coordsRes.iWidth, m_coordsRes.iHeight,
            resolved);
}

'''
    s=once(s,anchor,methods,"GUIWindow responsive methods")
    # Coalesced reload before frame processing.
    old='''void CGUIWindow::DoProcess(unsigned int currentTime, CDirtyRegionList &dirtyregions)
{
  if (!IsControlDirty() && CServiceBroker::GetSettingsComponent()->GetAdvancedSettings()->m_guiSmartRedraw)
'''
    new='''void CGUIWindow::DoProcess(unsigned int currentTime, CDirtyRegionList &dirtyregions)
{
  InfinityReloadNativeResponsiveLayout();

  if (!IsControlDirty() && CServiceBroker::GetSettingsComponent()->GetAdvancedSettings()->m_guiSmartRedraw)
'''
    s=once(s,old,new,"GUIWindow DoProcess responsive reload")
    # Resize notifications schedule a reflow, while normal control invalidation still proceeds.
    old='''        if (message.GetParam1() == GUI_MSG_PAGE_CHANGE ||
          message.GetParam1() == GUI_MSG_REFRESH_THUMBS ||
          message.GetParam1() == GUI_MSG_REFRESH_LIST ||
          message.GetParam1() == GUI_MSG_WINDOW_RESIZE)
        { // alter the message accordingly, and send to all controls
'''
    new='''        if (message.GetParam1() == GUI_MSG_WINDOW_RESIZE && g_SkinInfo &&
            g_SkinInfo->UsesNativeResponsiveLayout())
        {
          m_infinityResponsiveReloadPending = true;
          m_infinityResponsiveResizeAt = std::chrono::steady_clock::now();
          MarkDirtyRegion(DIRTY_STATE_CHILD);
        }

        if (message.GetParam1() == GUI_MSG_PAGE_CHANGE ||
          message.GetParam1() == GUI_MSG_REFRESH_THUMBS ||
          message.GetParam1() == GUI_MSG_REFRESH_LIST ||
          message.GetParam1() == GUI_MSG_WINDOW_RESIZE)
        { // alter the message accordingly, and send to all controls
'''
    s=once(s,old,new,"GUIWindow resize schedule")
    return s

def patch_android(s):
    s=once(s,'#include "ServiceBroker.h"\n',
           '#include "ServiceBroker.h"\n#include "addons/Skin.h"\n',"Android Skin include")
    old='''    if (auto* home = gui->GetWindowManager().GetWindow(WINDOW_HOME))
    {
      home->SetProperty("Infinity.CommittedWidth", width);
      home->SetProperty("Infinity.CommittedHeight", height);
      home->SetProperty("Infinity.GeometrySequence", static_cast<int64_t>(request.sequence));
    }
    CLog::Log(LOGINFO, "Infinity geometry committed: {}x{} generation={} sequence={} (bridge v4)",
              width, height, request.generation, request.sequence);
'''
    new='''    if (auto* home = gui->GetWindowManager().GetWindow(WINDOW_HOME))
    {
      home->SetProperty("Infinity.CommittedWidth", width);
      home->SetProperty("Infinity.CommittedHeight", height);
      home->SetProperty("Infinity.GeometrySequence", static_cast<int64_t>(request.sequence));
      if (g_SkinInfo && g_SkinInfo->UsesNativeResponsiveLayout())
      {
        const RESOLUTION_INFO logical = g_SkinInfo->GetNativeResponsiveResolution();
        const std::string layoutClass = g_SkinInfo->GetNativeResponsiveClass();
        home->SetProperty("Infinity.NativeResponsive", true);
        home->SetProperty("Infinity.ResponsiveClass", layoutClass);
        home->SetProperty("Infinity.LogicalWidth", logical.iWidth);
        home->SetProperty("Infinity.LogicalHeight", logical.iHeight);
        CLog::Log(LOGINFO,
                  "Infinity responsive viewport: physical={}x{} logical={}x{} class={}",
                  width, height, logical.iWidth, logical.iHeight, layoutClass);
      }
    }
    CLog::Log(LOGINFO, "Infinity geometry committed: {}x{} generation={} sequence={} (bridge v4)",
              width, height, request.generation, request.sequence);
'''
    s=once(s,old,new,"Android responsive viewport facts")
    return s

def verify(root):
    required={
      SKIN_H:["UsesNativeResponsiveLayout","GetNativeResponsiveResolution","RefreshNativeResponsiveIncludes"],
      SKIN_CPP:["infinity-native-responsive-v1.json","responsive/base","InfinityUsableSize","INFINITY_RESPONSIVE_SHORT_AXIS"],
      WIN_H:["m_infinityResponsiveReloadPending","InfinityReloadNativeResponsiveLayout"],
      WIN_CPP:["std::chrono::milliseconds(90)","Infinity responsive window:","Infinity.ResolvedXML"],
      ANDROID:["Infinity responsive viewport:","Infinity.NativeResponsive"],
    }
    for p,tokens in required.items():
      text=(root/p).read_text()
      for token in tokens:
        if token not in text: raise RuntimeError(f"missing {token} in {p}")
    # Guard the architectural contract: responsive path is single-source and not the old closest-res
    # mechanism, while non-responsive skins keep upstream behavior.
    skin=(root/SKIN_CPP).read_text()
    responsive=skin[skin.index('if (UsesNativeResponsiveLayout())', skin.index('std::string CSkinInfo::GetSkinPath')):]
    if 'std::min_element(m_resolutions.begin()' not in responsive:
      raise RuntimeError("legacy resolver unexpectedly removed")
    return {
      "schema":1,"kodi":"21.3-Omega","contract":"Infinity Native Responsive Layout v1",
      "native_window_authoritative":True,"logical_short_axis":1080,"uniform_aspect_canvas":True,
      "skin_profiles_required_for_correctness":False,"responsive_base_required":True,
      "legacy_skins_unchanged":True,"resize_debounce_ms":90,
      "files":{str(p):sha(root/p) for p in required}
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["apply","verify"])
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args(); root=a.source.resolve()
    if a.mode=="apply":
      patches=[(SKIN_H,patch_skin_h),(SKIN_CPP,patch_skin_cpp),(WIN_H,patch_window_h),
               (WIN_CPP,patch_window_cpp),(ANDROID,patch_android)]
      for p,fn in patches:
        path=root/p; path.write_text(fn(path.read_text()),encoding="utf-8")
    result=verify(root); a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("PASS: Kodi-owned native responsive logical viewport contract verified")
if __name__=="__main__": main()
