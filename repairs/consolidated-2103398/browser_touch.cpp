bool CGUIBaseContainer::OnInfinityAddonBrowserTouch(float x, float y, bool hold)
{
  auto& wm=CServiceBroker::GetGUI()->GetWindowManager();
  auto* browser=dynamic_cast<CGUIMediaWindow*>(wm.GetWindow(WINDOW_ADDON_BROWSER));
  if (!browser || wm.GetActiveWindow()!=WINDOW_ADDON_BROWSER ||
      (GetParentID()!=WINDOW_ADDON_BROWSER && GetParentID()!=WINDOW_DIALOG_FILE_BROWSER) ||
      !HasProcessed() || m_gestureActive)
    return false;
  const auto directory=browser->CurrentDirectory().GetPath();
  if (directory.rfind("addons://search",0)==0) return false;
  for(const CGUIControl* owner=this;owner;owner=owner->GetParentControl())
    if(!owner->IsVisible()||owner->IsDisabled())return false;
  CPoint point(x,y);m_cachedTransform.InverseTransformPosition(point.x,point.y);
  if(!CanFocusFromPoint(point))return false;
  const int previous=GetSelectedItem();
  if(!SelectItemFromPoint(point-CPoint(m_posX,m_posY)))return false;
  const int selected=GetSelectedItem();
  if(selected<0||selected>=static_cast<int>(m_items.size())||!m_items[selected]||!m_items[selected]->IsFileItem())
  {SelectItem(previous);return false;}
  const auto item=std::static_pointer_cast<CFileItem>(m_items[selected]);
  if(item->GetPath().rfind("addons://search",0)==0)return false;
  auto* window=wm.GetWindow(GetParentID());if(!window)return false;
  CGUIMessage focus(GUI_MSG_SETFOCUS,GetParentID(),GetID());window->OnMessage(focus);
  if(window->GetFocusedControlID()!=GetID()||GetSelectedItem()!=selected)return true;
  m_waitForScrollEnd=false;
  const auto now=std::chrono::steady_clock::now();
  const std::string key=directory+"\n"+std::to_string(GetParentID())+"\n"+
      std::to_string(selected)+"\n"+item->GetPath()+"\n"+
      std::to_string(reinterpret_cast<std::uintptr_t>(item.get()));
  const auto decision=InfinityTouchPress(this,key,previous==selected,hold,now);
  if(decision==InfinityTouchDecision::Context)
    window->OnAction(CAction(ACTION_CONTEXT_MENU));
  else if(decision==InfinityTouchDecision::Activate)
    OnClick(ACTION_SELECT_ITEM);
  return true;
}
