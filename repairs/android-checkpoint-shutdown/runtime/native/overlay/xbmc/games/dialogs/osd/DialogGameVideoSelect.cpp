/*
 *  Copyright (C) 2017-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "DialogGameVideoSelect.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include <mutex>
#include <set>
#endif

#include "FileItem.h"
#include "ServiceBroker.h"
#include "cores/RetroPlayer/guibridge/GUIGameRenderManager.h"
#include "cores/RetroPlayer/guibridge/GUIGameVideoHandle.h"
#include "games/dialogs/DialogGameDefines.h"
#include "guilib/GUIBaseContainer.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIMessage.h"
#include "guilib/GUIWindowManager.h"
#include "input/actions/ActionIDs.h"
#include "settings/GameSettings.h"
#include "settings/MediaSettings.h"
#include "settings/Settings.h"
#include "settings/SettingsComponent.h"
#include "view/GUIViewControl.h"
#include "view/ViewState.h"
#include "windowing/GraphicContext.h"

using namespace KODI;
using namespace GAME;

#if defined(TARGET_ANDROID)
namespace
{
struct PendingGameOwners
{
  std::recursive_mutex mutex;
  std::set<CDialogGameVideoSelect*> dialogs;
  bool abandonedSettings{false};
};
PendingGameOwners& PendingGames()
{
  static auto* owners = new PendingGameOwners;
  return *owners;
}
} // namespace

bool InfinityAndroidCheckpoint::CheckpointPendingGameDialogs()
{
  if (!IsPersistingOnThisThread())
    return false;
  auto& owners = PendingGames();
  std::lock_guard<std::recursive_mutex> lock(owners.mutex);
  if (owners.abandonedSettings)
  {
    RecordFailure("deferred_dialog_state", "destroyed_game_dialog_save_failed");
    return false;
  }
  const auto dialogs = owners.dialogs;
  for (auto* dialog : dialogs)
    if (owners.dialogs.count(dialog) && !dialog->CheckpointPendingForAndroidExit())
      return false;
  return true;
}

bool CDialogGameVideoSelect::CheckpointPendingForAndroidExit()
{
  InfinityAndroidCheckpoint::CheckpointWriteGuard write("deferred_dialog_state");
  if (!write || !InfinityAndroidCheckpoint::IsPersistingOnThisThread())
    return false;
  std::lock_guard<std::recursive_mutex> ownerLock(PendingGames().mutex);
  // A closed dialog retries only its prior failed defaults save. It must not
  // copy an unrelated game's current settings merely because the object exists.
  return SaveSettingsChecked(IsDialogRunning());
}
#endif

CDialogGameVideoSelect::CDialogGameVideoSelect(int windowId)
  : CGUIDialog(windowId, "DialogSelect.xml"),
    m_viewControl(new CGUIViewControl),
    m_vecItems(new CFileItemList)
{
  // Initialize CGUIWindow
  m_loadType = KEEP_IN_MEMORY;
#if defined(TARGET_ANDROID)
  auto& owners = PendingGames();
  std::lock_guard<std::recursive_mutex> lock(owners.mutex);
  owners.dialogs.insert(this);
#endif
}

CDialogGameVideoSelect::~CDialogGameVideoSelect()
{
#if defined(TARGET_ANDROID)
  auto& owners = PendingGames();
  std::lock_guard<std::recursive_mutex> lock(owners.mutex);
  if (m_checkpointSettingsDirty)
    owners.abandonedSettings = true;
  owners.dialogs.erase(this);
#endif
}

bool CDialogGameVideoSelect::OnMessage(CGUIMessage& message)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard write("deferred_dialog_state");
  if (!write)
    return false;
#endif
  switch (message.GetMessage())
  {
    case GUI_MSG_WINDOW_INIT:
    {
      RegisterDialog();

      // Don't init this dialog if we aren't playing a game
      if (!m_gameVideoHandle || !m_gameVideoHandle->IsPlayingGame())
        return false;

      break;
    }
    case GUI_MSG_WINDOW_DEINIT:
    {
      UnregisterDialog();

      break;
    }
    case GUI_MSG_SETFOCUS:
    {
      const int controlId = message.GetControlId();
      if (m_viewControl->HasControl(controlId) && m_viewControl->GetCurrentControl() != controlId)
      {
        m_viewControl->SetFocused();
        return true;
      }
      break;
    }
    case GUI_MSG_CLICKED:
    {
      const int actionId = message.GetParam1();
      if (actionId == ACTION_SELECT_ITEM || actionId == ACTION_MOUSE_LEFT_CLICK)
      {
        const int controlId = message.GetSenderId();
        if (m_viewControl->HasControl(controlId))
        {
          if (OnClickAction())
            return true;
        }
      }
      else if (actionId == ACTION_CONTEXT_MENU || actionId == ACTION_MOUSE_RIGHT_CLICK)
      {
        const int controlId = message.GetSenderId();
        if (m_viewControl->HasControl(controlId))
        {
          if (OnMenuAction())
            return true;
        }
      }
      else if (actionId == ACTION_CREATE_BOOKMARK)
      {
        const int controlId = message.GetSenderId();
        if (m_viewControl->HasControl(controlId))
        {
          if (OnOverwriteAction())
            return true;
        }
      }
      else if (actionId == ACTION_RENAME_ITEM)
      {
        const int controlId = message.GetSenderId();
        if (m_viewControl->HasControl(controlId))
        {
          if (OnRenameAction())
            return true;
        }
      }
      else if (actionId == ACTION_DELETE_ITEM)
      {
        const int controlId = message.GetSenderId();
        if (m_viewControl->HasControl(controlId))
        {
          if (OnDeleteAction())
            return true;
        }
      }

      break;
    }
    case GUI_MSG_REFRESH_LIST:
    {
      RefreshList();
      break;
    }
    default:
      break;
  }

  return CGUIDialog::OnMessage(message);
}

void CDialogGameVideoSelect::FrameMove()
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard write("deferred_dialog_state");
  if (!write)
    return;
#endif
  CGUIBaseContainer* thumbs = dynamic_cast<CGUIBaseContainer*>(GetControl(CONTROL_VIDEO_THUMBS));
  if (thumbs != nullptr)
    OnItemFocus(thumbs->GetSelectedItem());

  CGUIDialog::FrameMove();
}

void CDialogGameVideoSelect::OnWindowLoaded()
{
  CGUIDialog::OnWindowLoaded();

  m_viewControl->SetParentWindow(GetID());
  m_viewControl->AddView(GetControl(CONTROL_VIDEO_THUMBS));
}

void CDialogGameVideoSelect::OnWindowUnload()
{
  m_viewControl->Reset();

  CGUIDialog::OnWindowUnload();
}

void CDialogGameVideoSelect::OnInitWindow()
{
  PreInit();

  CGUIDialog::OnInitWindow();

  Update();

  CGUIMessage msg(GUI_MSG_SETFOCUS, GetID(), CONTROL_VIDEO_THUMBS);
  OnMessage(msg);

  std::string heading = GetHeading();
  SET_CONTROL_LABEL(CONTROL_VIDEO_HEADING, heading);

  FrameMove();
}

void CDialogGameVideoSelect::OnDeinitWindow(int nextWindowID)
{
  Clear();

  CGUIDialog::OnDeinitWindow(nextWindowID);

  PostExit();

  SaveSettings();
}

void CDialogGameVideoSelect::Update()
{
  //! @todo
  // Lock our display, as this window is rendered from the player thread
  // CServiceBroker::GetWinSystem()->GetGfxContext().Lock();

  m_viewControl->SetCurrentView(DEFAULT_VIEW_ICONS);

  // Empty the list ready for population
  Clear();

  RefreshList();

  // CServiceBroker::GetWinSystem()->GetGfxContext().Unlock();
}

void CDialogGameVideoSelect::Clear()
{
  m_viewControl->Clear();
  m_vecItems->Clear();
}

void CDialogGameVideoSelect::RefreshList()
{
  m_vecItems->Clear();

  GetItems(*m_vecItems);

  m_viewControl->SetItems(*m_vecItems);

  auto focusedIndex = GetFocusedItem();
  m_viewControl->SetSelectedItem(focusedIndex);
  OnItemFocus(focusedIndex);

  // Refresh the panel container
  CGUIMessage message(GUI_MSG_REFRESH_THUMBS, GetID(), CONTROL_VIDEO_THUMBS);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(message, GetID());
}

void CDialogGameVideoSelect::SaveSettings()
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard write("deferred_dialog_state");
  if (!write)
    return;
#endif
  SaveSettingsChecked(true);
}

bool CDialogGameVideoSelect::SaveSettingsChecked(bool captureCurrent)
{
  CGameSettings& defaultSettings = CMediaSettings::GetInstance().GetDefaultGameSettings();
  CGameSettings& currentSettings = CMediaSettings::GetInstance().GetCurrentGameSettings();

  const bool changed = captureCurrent && defaultSettings != currentSettings;
  if (changed)
  {
    defaultSettings = currentSettings;
#if defined(TARGET_ANDROID)
    m_checkpointSettingsDirty = true;
#endif
  }
#if defined(TARGET_ANDROID)
  if (!m_checkpointSettingsDirty)
    return true;
#else
  if (!changed)
    return true;
#endif
  if (!CServiceBroker::GetSettingsComponent()->GetSettings()->Save())
  {
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::RecordFailure("deferred_dialog_state", "game_defaults_save_failed");
#endif
    return false;
  }
#if defined(TARGET_ANDROID)
  m_checkpointSettingsDirty = false;
#endif
  return true;
}

void CDialogGameVideoSelect::OnDescriptionChange(const std::string& description)
{
  CGUIMessage msg(GUI_MSG_LABEL_SET, GetID(), CONTROL_VIDEO_THUMBS);
  msg.SetLabel(description);
  CServiceBroker::GetGUI()->GetWindowManager().SendThreadMessage(msg, GetID());
}

void CDialogGameVideoSelect::RegisterDialog()
{
  m_gameVideoHandle = CServiceBroker::GetGameRenderManager().RegisterDialog(*this);
}

void CDialogGameVideoSelect::UnregisterDialog()
{
  m_gameVideoHandle.reset();
}
