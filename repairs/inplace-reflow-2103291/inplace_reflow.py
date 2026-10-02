#!/usr/bin/env python3
"""Infinity 2103291: in-place Kodi GUI responsive reflow.

Layered strictly after the proven 2103290 native-responsive engine.

Goal:
  Android/Fold/window resize -> Kodi updates logical viewport -> existing controls recompute their
  authored geometry in place. Do not unload/recreate the active GUI window merely because its
  responsive class/canvas changed.

The skin remains declarative: the factory records the original left/right/center/size expressions
already present in the XML. Fixed dimensions stay fixed; percentage / reverse / edge constraints are
re-evaluated against the new parent size. Group children recurse against the group's new bounds.

This is marker-gated by the existing Infinity Native Responsive Layout v1 path at the window level.
Non-responsive Kodi skins keep the upstream behavior and never call the new reflow path.
"""
from pathlib import Path
import argparse, hashlib, json, re

CONTROL_H=Path("xbmc/guilib/GUIControl.h")
CONTROL_CPP=Path("xbmc/guilib/GUIControl.cpp")
GROUP_H=Path("xbmc/guilib/GUIControlGroup.h")
GROUP_CPP=Path("xbmc/guilib/GUIControlGroup.cpp")
FACTORY_CPP=Path("xbmc/guilib/GUIControlFactory.cpp")
WINDOW_H=Path("xbmc/guilib/GUIWindow.h")
WINDOW_CPP=Path("xbmc/guilib/GUIWindow.cpp")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b,label):
    n=s.count(a)
    if n!=1: raise RuntimeError(f"{label}: expected one anchor, found {n}")
    return s.replace(a,b,1)

def method_span(s, signature):
    start=s.index(signature)
    brace=s.index("{",start)
    depth=0
    for i in range(brace,len(s)):
        ch=s[i]
        if ch=="{": depth+=1
        elif ch=="}":
            depth-=1
            if depth==0:
                return start,i+1
    raise RuntimeError("Unbalanced method body for "+signature)

def patch_control_h(s):
    s=once(s,"#include <vector>\n","#include <string>\n#include <vector>\n","GUIControl string include")
    anchor='''struct GUICONTROLSTATS
{
'''
    spec=r'''struct GUIResponsiveAxisSpec
{
  std::string start;
  std::string end;
  std::string centerStart;
  std::string centerEnd;
  std::string size;
  std::string legacyPos;
  std::string sizeMin;
  std::string sizeMax;

  bool HasAny() const
  {
    return !start.empty() || !end.empty() || !centerStart.empty() || !centerEnd.empty() ||
           !size.empty() || !legacyPos.empty();
  }
};

struct GUIResponsiveHitRectSpec
{
  bool enabled{false};
  std::string x;
  std::string y;
  std::string width;
  std::string height;
  std::string right;
  std::string bottom;
};

struct GUIResponsiveLayoutSpec
{
  bool enabled{false};
  bool legacyPosXSubtractWidth{false};
  GUIResponsiveAxisSpec horizontal;
  GUIResponsiveAxisSpec vertical;
  GUIResponsiveHitRectSpec hitRect;
};

'''
    s=once(s,anchor,spec+anchor,"GUIControl responsive spec structs")
    s=once(s,
'''  virtual void SetPosition(float posX, float posY);
  virtual void SetHitRect(const CRect& rect, const UTILS::COLOR::Color& color);
''',
'''  virtual void SetPosition(float posX, float posY);
  void SetResponsiveLayoutSpec(const GUIResponsiveLayoutSpec& spec) { m_responsiveLayoutSpec = spec; }
  virtual bool ReflowResponsiveLayout(float parentWidth, float parentHeight);
  virtual void SetHitRect(const CRect& rect, const UTILS::COLOR::Color& color);
''',"GUIControl responsive API")
    s=once(s,
'''  float m_height;
  float m_width;
  CRect m_hitRect;
''',
'''  float m_height;
  float m_width;
  GUIResponsiveLayoutSpec m_responsiveLayoutSpec;
  CRect m_hitRect;
''',"GUIControl responsive state")
    return s

def patch_control_cpp(s):
    s=once(s,'#include "utils/log.h"\n',
           '#include "utils/log.h"\n\n#include <algorithm>\n#include <cstdlib>\n',"GUIControl responsive includes")
    anchor='''using namespace KODI;
using namespace GUILIB;

'''
    helpers=anchor+r'''namespace
{
float InfinityResponsiveParse(const std::string& text, float parentSize)
{
  if (text.empty())
    return 0.0f;
  char* end = nullptr;
  float value = static_cast<float>(std::strtod(text.c_str(), &end));
  if (end)
  {
    if (*end == 'r')
      value = parentSize - value;
    else if (*end == '%')
      value = value * parentSize / 100.0f;
  }
  return value;
}

bool InfinityResponsiveValue(const std::string& text, float parentSize, float& value)
{
  if (text.empty())
    return false;
  value = InfinityResponsiveParse(text, parentSize);
  return true;
}

bool InfinityResponsiveDimension(const GUIResponsiveAxisSpec& spec,
                                 float parentSize,
                                 float currentSize,
                                 float& value,
                                 float& minimum)
{
  if (spec.size.empty())
    return false;
  if (spec.size == "auto")
  {
    value = spec.sizeMax.empty() ? currentSize : InfinityResponsiveParse(spec.sizeMax, parentSize);
    minimum =
        spec.sizeMin.empty() ? 1.0f : InfinityResponsiveParse(spec.sizeMin, parentSize);
    if (minimum == 0.0f)
      minimum = 1.0f;
    return true;
  }
  value = InfinityResponsiveParse(spec.size, parentSize);
  return true;
}

bool InfinityResolveResponsiveAxis(const GUIResponsiveAxisSpec& spec,
                                   float parentSize,
                                   float currentStart,
                                   float currentSize,
                                   bool legacySubtractSize,
                                   float& start,
                                   float& size)
{
  if (!spec.HasAny())
    return false;

  start = currentStart;
  size = currentSize;
  float center = 0.0f;
  float end = 0.0f;
  float minimum = 0.0f;

  bool hasStart = InfinityResponsiveValue(spec.start, parentSize, start);
  bool hasCenter = InfinityResponsiveValue(spec.centerStart, parentSize, center);
  if (!hasCenter && InfinityResponsiveValue(spec.centerEnd, parentSize, center))
  {
    center = parentSize - center;
    hasCenter = true;
  }

  bool hasEnd = false;
  if (InfinityResponsiveValue(spec.end, parentSize, end))
  {
    end = parentSize - end;
    hasEnd = true;
  }

  bool hasSize =
      InfinityResponsiveDimension(spec, parentSize, currentSize, size, minimum);

  if (!hasStart)
  {
    if (hasCenter)
    {
      if (hasSize)
      {
        start = center - size / 2.0f;
        hasStart = true;
      }
      else if (hasEnd)
      {
        size = (end - center) * 2.0f;
        start = end - size;
        hasStart = true;
      }
    }
    else if (hasEnd && hasSize)
    {
      start = end - size;
      hasStart = true;
    }
  }

  if (!hasSize)
  {
    if (hasEnd)
    {
      size = std::max(0.0f, end - start);
      hasStart = true;
      hasSize = true;
    }
    else if (hasCenter)
    {
      if (hasStart)
      {
        size = std::max(0.0f, (center - start) * 2.0f);
        hasSize = true;
      }
      else if (center > 0.0f && center < parentSize)
      {
        size = std::max(0.0f, std::min(parentSize - center, center) * 2.0f);
        start = center - size / 2.0f;
        hasStart = true;
        hasSize = true;
      }
    }
    else if (hasStart)
    {
      size = std::max(0.0f, parentSize - start);
      hasSize = true;
    }
  }

  if ((!hasStart || !hasSize) && !spec.legacyPos.empty())
  {
    start = InfinityResponsiveParse(spec.legacyPos, parentSize);
    if (legacySubtractSize)
      start -= size;
    hasStart = true;
    if (!hasSize)
    {
      size = std::max(0.0f, parentSize - start);
      hasSize = true;
    }
  }

  return hasStart || hasSize;
}
} // namespace

'''
    s=once(s,anchor,helpers,"GUIControl responsive geometry helpers")
    anchor='''void CGUIControl::SetPosition(float posX, float posY)
{
'''
    method=r'''bool CGUIControl::ReflowResponsiveLayout(float parentWidth, float parentHeight)
{
  if (!m_responsiveLayoutSpec.enabled)
    return false;

  const float oldX = m_posX;
  const float oldY = m_posY;
  const float oldWidth = m_width;
  const float oldHeight = m_height;

  float nextX = oldX;
  float nextY = oldY;
  float nextWidth = oldWidth;
  float nextHeight = oldHeight;

  InfinityResolveResponsiveAxis(m_responsiveLayoutSpec.horizontal, parentWidth, oldX, oldWidth,
                                m_responsiveLayoutSpec.legacyPosXSubtractWidth, nextX, nextWidth);
  InfinityResolveResponsiveAxis(m_responsiveLayoutSpec.vertical, parentHeight, oldY, oldHeight,
                                false, nextY, nextHeight);

  // Size first so right-aligned legacy positions and derived control internals see the new extent.
  SetWidth(nextWidth);
  SetHeight(nextHeight);
  SetPosition(nextX, nextY);

  if (m_responsiveLayoutSpec.hitRect.enabled)
  {
    const auto& spec = m_responsiveLayoutSpec.hitRect;
    CRect hit = m_hitRect;
    hit.x1 = InfinityResponsiveParse(spec.x, parentWidth);
    hit.y1 = InfinityResponsiveParse(spec.y, parentHeight);
    if (!spec.width.empty())
      hit.x2 = static_cast<float>(std::atof(spec.width.c_str())) + hit.x1;
    else if (!spec.right.empty())
      hit.x2 = std::min(InfinityResponsiveParse(spec.right, parentWidth), hit.x1);
    else
      hit.x2 = hit.x1 + nextWidth;
    if (!spec.height.empty())
      hit.y2 = static_cast<float>(std::atof(spec.height.c_str())) + hit.y1;
    else if (!spec.bottom.empty())
      hit.y2 = std::min(InfinityResponsiveParse(spec.bottom, parentHeight), hit.y1);
    else
      hit.y2 = hit.y1 + nextHeight;
    SetHitRect(hit, m_hitColor);
  }

  const bool changed = oldX != m_posX || oldY != m_posY || oldWidth != m_width || oldHeight != m_height;
  if (changed)
    SetInvalid();
  return changed;
}

'''
    s=once(s,anchor,method+anchor,"GUIControl in-place reflow")
    return s

def patch_group_h(s):
    s=once(s,
'''  void Process(unsigned int currentTime, CDirtyRegionList &dirtyregions) override;
  void Render() override;
''',
'''  void Process(unsigned int currentTime, CDirtyRegionList &dirtyregions) override;
  bool ReflowResponsiveLayout(float parentWidth, float parentHeight) override;
  void Render() override;
''',"GUIControlGroup responsive override")
    return s

def patch_group_cpp(s):
    anchor='''void CGUIControlGroup::Process(unsigned int currentTime, CDirtyRegionList &dirtyregions)
{
'''
    method=r'''bool CGUIControlGroup::ReflowResponsiveLayout(float parentWidth, float parentHeight)
{
  const bool selfChanged = CGUIControl::ReflowResponsiveLayout(parentWidth, parentHeight);

  // A window itself has no control-level layout spec, so its children use the supplied logical
  // viewport. A real group uses its freshly recomputed bounds as the child coordinate space.
  float childWidth = m_responsiveLayoutSpec.enabled ? GetWidth() : parentWidth;
  float childHeight = m_responsiveLayoutSpec.enabled ? GetHeight() : parentHeight;
  if (childWidth <= 0.0f)
    childWidth = parentWidth;
  if (childHeight <= 0.0f)
    childHeight = parentHeight;

  bool childChanged = false;
  for (auto* control : m_children)
    childChanged |= control->ReflowResponsiveLayout(childWidth, childHeight);

  if (selfChanged || childChanged)
    MarkDirtyRegion(DIRTY_STATE_CHILD);
  return selfChanged || childChanged;
}

'''
    s=once(s,anchor,method+anchor,"GUIControlGroup recursive reflow")
    return s

def patch_factory_cpp(s):
    anchor='''CGUIControl* CGUIControlFactory::Create(int parentID,
'''
    helpers=r'''namespace
{
std::string InfinityResponsiveNodeText(const TiXmlNode* node, const char* tag)
{
  const TiXmlElement* value = node ? node->FirstChildElement(tag) : nullptr;
  return value && value->FirstChild() ? value->FirstChild()->ValueStr() : std::string();
}

std::string InfinityResponsiveAttribute(const TiXmlElement* element, const char* name)
{
  const char* value = element ? element->Attribute(name) : nullptr;
  return value ? std::string(value) : std::string();
}

GUIResponsiveAxisSpec InfinityResponsiveAxis(const TiXmlNode* node,
                                             const char* start,
                                             const char* end,
                                             const char* centerStart,
                                             const char* centerEnd,
                                             const char* size,
                                             const char* legacyPos)
{
  GUIResponsiveAxisSpec spec;
  spec.start = InfinityResponsiveNodeText(node, start);
  spec.end = InfinityResponsiveNodeText(node, end);
  spec.centerStart = InfinityResponsiveNodeText(node, centerStart);
  spec.centerEnd = InfinityResponsiveNodeText(node, centerEnd);
  spec.size = InfinityResponsiveNodeText(node, size);
  spec.legacyPos = InfinityResponsiveNodeText(node, legacyPos);
  const TiXmlElement* sizeNode = node ? node->FirstChildElement(size) : nullptr;
  spec.sizeMin = InfinityResponsiveAttribute(sizeNode, "min");
  spec.sizeMax = InfinityResponsiveAttribute(sizeNode, "max");
  return spec;
}

GUIResponsiveLayoutSpec InfinityResponsiveLayout(const TiXmlNode* node,
                                                 bool legacyPosXSubtractWidth)
{
  GUIResponsiveLayoutSpec spec;
  spec.horizontal =
      InfinityResponsiveAxis(node, "left", "right", "centerleft", "centerright", "width", "posx");
  spec.vertical =
      InfinityResponsiveAxis(node, "top", "bottom", "centertop", "centerbottom", "height", "posy");
  spec.legacyPosXSubtractWidth = legacyPosXSubtractWidth;
  spec.enabled = spec.horizontal.HasAny() || spec.vertical.HasAny();

  const TiXmlElement* hit = node ? node->FirstChildElement("hitrect") : nullptr;
  if (hit)
  {
    spec.hitRect.enabled = true;
    spec.hitRect.x = InfinityResponsiveAttribute(hit, "x");
    spec.hitRect.y = InfinityResponsiveAttribute(hit, "y");
    spec.hitRect.width = InfinityResponsiveAttribute(hit, "w");
    spec.hitRect.height = InfinityResponsiveAttribute(hit, "h");
    spec.hitRect.right = InfinityResponsiveAttribute(hit, "right");
    spec.hitRect.bottom = InfinityResponsiveAttribute(hit, "bottom");
  }
  return spec;
}
} // namespace

'''
    s=once(s,anchor,helpers+anchor,"GUIControlFactory responsive spec helpers")
    old='''  // things that apply to all controls
  if (control)
  {
    control->SetHitRect(hitRect, hitColor);
'''
    new='''  // things that apply to all controls
  if (control)
  {
    const bool legacyRightAlignedPosX =
        !insideContainer && type == CGUIControl::GUICONTROL_LABEL &&
        (labelInfo.align & XBFONT_RIGHT) && pControlNode->FirstChildElement("posx") &&
        !pControlNode->FirstChildElement("left") && !pControlNode->FirstChildElement("right") &&
        !pControlNode->FirstChildElement("centerleft") &&
        !pControlNode->FirstChildElement("centerright");
    control->SetResponsiveLayoutSpec(
        InfinityResponsiveLayout(pControlNode, legacyRightAlignedPosX));
    control->SetHitRect(hitRect, hitColor);
'''
    s=once(s,old,new,"GUIControlFactory attach responsive spec")
    return s

def patch_window_h(s):
    s=once(s,
'''  bool InfinityNativeResponsiveLayoutChanged(RESOLUTION_INFO* next = nullptr,
                                             std::string* path = nullptr) const;
  void InfinityReloadNativeResponsiveLayout();
  void InfinityPublishResponsiveProperties(const std::string& path);
''',
'''  bool InfinityNativeResponsiveLayoutChanged(RESOLUTION_INFO* next = nullptr,
                                             std::string* path = nullptr) const;
  void InfinityReloadNativeResponsiveLayout();
  void InfinityReflowRootGeometry();
  void InfinityPublishResponsiveProperties(const std::string& path);
''',"GUIWindow in-place helper declaration")
    return s

def patch_window_cpp(s):
    # Insert root-geometry updater before existing reload implementation.
    anchor='''void CGUIWindow::InfinityReloadNativeResponsiveLayout()
{
'''
    root_method=r'''void CGUIWindow::InfinityReflowRootGeometry()
{
  if (!m_windowXMLRootElement)
    return;

  CRect parentRect(0, 0, static_cast<float>(m_coordsRes.iWidth),
                   static_cast<float>(m_coordsRes.iHeight));
  m_hitRect.SetRect(parentRect.x1, parentRect.y1, parentRect.x2, parentRect.y2);
  CGUIControlFactory::GetHitRect(m_windowXMLRootElement.get(), m_hitRect, parentRect);

  const TiXmlElement* coordinates = m_windowXMLRootElement->FirstChildElement("coordinates");
  if (coordinates)
  {
    const auto readPosition = [coordinates](const char* tag, float parent, float& value)
    {
      const TiXmlElement* node = coordinates->FirstChildElement(tag);
      if (node && node->FirstChild())
        value = CGUIControlFactory::ParsePosition(node->FirstChild()->Value(), parent);
    };
    readPosition("posx", static_cast<float>(m_coordsRes.iWidth), m_posX);
    readPosition("posy", static_cast<float>(m_coordsRes.iHeight), m_posY);
    readPosition("left", static_cast<float>(m_coordsRes.iWidth), m_posX);
    readPosition("top", static_cast<float>(m_coordsRes.iHeight), m_posY);

    m_origins.clear();
    const TiXmlElement* originElement = coordinates->FirstChildElement("origin");
    while (originElement)
    {
      COrigin origin;
      origin.x = CGUIControlFactory::ParsePosition(
          originElement->Attribute("x"), static_cast<float>(m_coordsRes.iWidth));
      origin.y = CGUIControlFactory::ParsePosition(
          originElement->Attribute("y"), static_cast<float>(m_coordsRes.iHeight));
      if (originElement->FirstChild())
        origin.condition = CServiceBroker::GetGUI()->GetInfoManager().Register(
            originElement->FirstChild()->Value(), GetID());
      m_origins.push_back(origin);
      originElement = originElement->NextSiblingElement("origin");
    }
  }

  const TiXmlElement* camera = m_windowXMLRootElement->FirstChildElement("camera");
  if (camera)
  {
    m_camera.x = CGUIControlFactory::ParsePosition(
        camera->Attribute("x"), static_cast<float>(m_coordsRes.iWidth));
    m_camera.y = CGUIControlFactory::ParsePosition(
        camera->Attribute("y"), static_cast<float>(m_coordsRes.iHeight));
    m_hasCamera = true;
  }
}

'''
    s=once(s,anchor,root_method+anchor,"GUIWindow root in-place reflow")
    # Replace the 2103290 unload/reallocate body with in-place geometry recompute.
    start,end=method_span(s,"void CGUIWindow::InfinityReloadNativeResponsiveLayout()")
    old=s[start:end]
    new=r'''void CGUIWindow::InfinityReloadNativeResponsiveLayout()
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

  const int focusBefore = GetFocusedControlID();
  const std::string classBefore = m_coordsRes.strMode;
  const int widthBefore = m_coordsRes.iWidth;
  const int heightBefore = m_coordsRes.iHeight;

  // Cobra-like ownership: retain the live window/control objects. Kodi changes the logical
  // viewport and asks every existing control to recompute its original XML geometry in place.
  m_coordsRes = next;
  g_SkinInfo->RefreshNativeResponsiveIncludes();
  SetProperty("Infinity.NativeResponsive", true);
  SetProperty("Infinity.ResponsiveClass", g_SkinInfo->GetNativeResponsiveClass());
  SetProperty("Infinity.LogicalWidth", next.iWidth);
  SetProperty("Infinity.LogicalHeight", next.iHeight);
  SetProperty("Infinity.InPlaceReflow", true);
  SetProperty("Infinity.ResponsiveCandidateXML", resolved);
  InfinityReflowRootGeometry();

  m_width = 0.0f;
  m_height = 0.0f;
  CGUIControlGroup::ReflowResponsiveLayout(static_cast<float>(next.iWidth),
                                           static_cast<float>(next.iHeight));
  for (auto* child : m_children)
  {
    m_width = std::max(m_width, child->GetXPosition() + child->GetWidth());
    m_height = std::max(m_height, child->GetYPosition() + child->GetHeight());
  }

  // Let control-specific resize handlers refresh textures/list internals after the new bounds are
  // already authoritative. This does not unload, allocate, init or restore the window.
  CGUIMessage resize(GUI_MSG_WINDOW_RESIZE, GetID(), 0);
  CGUIControlGroup::OnMessage(resize);
  UpdateVisibility(nullptr);
  MarkDirtyRegion(DIRTY_STATE_CHILD);

  const int focusAfter = GetFocusedControlID();
  CLog::Log(LOGINFO,
            "Infinity in-place responsive reflow: id={} xml={} class={}->{} logical={}x{}->{}x{} "
            "focus={}->{} controls_reused=true window_reload=false path={}",
            GetID(), GetProperty("xmlfile").asString(), classBefore, next.strMode,
            widthBefore, heightBefore, next.iWidth, next.iHeight, focusBefore, focusAfter, resolved);
}
'''
    s=s[:start]+new+s[end:]

    # Responsive resize messages schedule the reflow and do not immediately fan out against old bounds.
    old='''        if (message.GetParam1() == GUI_MSG_WINDOW_RESIZE && g_SkinInfo &&
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
'''
    new='''        if (message.GetParam1() == GUI_MSG_WINDOW_RESIZE && g_SkinInfo &&
            g_SkinInfo->UsesNativeResponsiveLayout())
        {
          m_infinityResponsiveReloadPending = true;
          m_infinityResponsiveResizeAt = std::chrono::steady_clock::now();
          MarkDirtyRegion(DIRTY_STATE_CHILD);
          return true;
        }

        if (message.GetParam1() == GUI_MSG_PAGE_CHANGE ||
          message.GetParam1() == GUI_MSG_REFRESH_THUMBS ||
          message.GetParam1() == GUI_MSG_REFRESH_LIST ||
          message.GetParam1() == GUI_MSG_WINDOW_RESIZE)
'''
    s=once(s,old,new,"GUIWindow defer responsive resize fanout")
    return s

def verify(root):
    required={
      CONTROL_H:["GUIResponsiveLayoutSpec","ReflowResponsiveLayout(float parentWidth"],
      CONTROL_CPP:["InfinityResolveResponsiveAxis","CGUIControl::ReflowResponsiveLayout"],
      GROUP_H:["ReflowResponsiveLayout(float parentWidth, float parentHeight) override"],
      GROUP_CPP:["CGUIControlGroup::ReflowResponsiveLayout","control->ReflowResponsiveLayout"],
      FACTORY_CPP:["InfinityResponsiveLayout(pControlNode","SetResponsiveLayoutSpec"],
      WINDOW_H:["InfinityReflowRootGeometry"],
      WINDOW_CPP:["Infinity in-place responsive reflow:","controls_reused=true window_reload=false",
                  "CGUIControlGroup::ReflowResponsiveLayout","return true;"],
    }
    for p,tokens in required.items():
      text=(root/p).read_text()
      for token in tokens:
        if token not in text: raise RuntimeError(f"missing {token} in {p}")

    win=(root/WINDOW_CPP).read_text()
    a=win.index("void CGUIWindow::InfinityReloadNativeResponsiveLayout()")
    b=win.index("\n\nvoid CGUIWindow::DoProcess",a)
    method=win[a:b]
    for forbidden in ("FreeResources(true)", "AllocResources(true)", "SaveControlStates()",
                      "RestoreControlStates()", "RunLoadActions()", "RunUnloadActions()"):
      if forbidden in method:
        raise RuntimeError(f"in-place reflow illegally contains {forbidden}")

    # The control factory must retain original XML expressions rather than inventing device-specific math.
    factory=(root/FACTORY_CPP).read_text()
    for expression in ('"left"', '"right"', '"centerleft"', '"centerright"', '"width"', '"posx"',
                       '"top"', '"bottom"', '"centertop"', '"centerbottom"', '"height"', '"posy"'):
      if expression not in factory: raise RuntimeError("missing geometry expression capture "+expression)

    return {
      "schema":1,
      "build":2103291,
      "parent":"2103290-native-responsive-layout",
      "contract":"Infinity In-Place Responsive Reflow v1",
      "window_objects_reused":True,
      "controls_reused":True,
      "full_window_reload_on_resize":False,
      "focus_preserved_by_identity":True,
      "drawer_state_preserved_by_identity":True,
      "device_specific_routing_added":False,
      "resize_debounce_ms":90,
      "files":{str(p):sha(root/p) for p in required}
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["apply","verify"])
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args();root=a.source.resolve()
    if a.mode=="apply":
      for p,fn in [
        (CONTROL_H,patch_control_h),(CONTROL_CPP,patch_control_cpp),
        (GROUP_H,patch_group_h),(GROUP_CPP,patch_group_cpp),
        (FACTORY_CPP,patch_factory_cpp),(WINDOW_H,patch_window_h),(WINDOW_CPP,patch_window_cpp)
      ]:
        path=root/p;path.write_text(fn(path.read_text()),encoding="utf-8")
    result=verify(root)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("PASS: 2103291 in-place responsive reflow contract verified")

if __name__=="__main__":
    main()
