bool CGUIButtonControl::OnInfinityAddonActionTouch(float x,float y,bool hold)
{
  auto& wm=CServiceBroker::GetGUI()->GetWindowManager();
  if(GetParentID()!=WINDOW_DIALOG_ADDON_INFO || wm.GetActiveWindow()!=WINDOW_ADDON_BROWSER ||
      wm.GetTopmostModalDialog()!=WINDOW_DIALOG_ADDON_INFO)return false;
  auto* browser=wm.GetWindow(WINDOW_ADDON_BROWSER);
  if(!browser || browser->GetProperty("Infinity.AddonBrowser.SearchScope").asBoolean())return false;
  auto* owner=wm.GetWindow(WINDOW_DIALOG_ADDON_INFO);if(!owner)return false;
  const auto identity=owner->GetProperty("Infinity.AddonBrowser.ActionIdentity").asString();
  if(identity.empty())return false;
  for(const CGUIControl* c=this;c;c=c->GetParentControl())if(!c->IsVisible()||c->IsDisabled())return false;
  CPoint point(x,y);m_cachedTransform.InverseTransformPosition(point.x,point.y);
  if(!CanFocusFromPoint(point))return false;
  const int previous=owner->GetFocusedControlID();
  CGUIMessage focus(GUI_MSG_SETFOCUS,GetParentID(),GetID());owner->OnMessage(focus);
  const auto now=std::chrono::steady_clock::now();
  if(hold){m_infinityAddonActionKey.clear();m_infinityAddonActionSuppressUntil=now+std::chrono::milliseconds(600);return true;}
  if(now<m_infinityAddonActionSuppressUntil)return true;
  if(previous==GetID() && m_infinityAddonActionKey==identity)
  {m_infinityAddonActionKey.clear();OnAction(CAction(ACTION_SELECT_ITEM));}
  else m_infinityAddonActionKey=identity;
  return true;
}
