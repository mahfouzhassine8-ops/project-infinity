/*
 *  Copyright (C) 2012-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "PVREventLogJob.h"

#include "ServiceBroker.h"
#include "dialogs/GUIDialogKaiToast.h"
#include "events/EventLog.h"
#include "events/NotificationEvent.h"

#include <typeinfo>

namespace PVR
{

CJob::CheckpointResponsibility CPVREventLogJob::GetCheckpointResponsibility(
    const IJobCallback* callback) const
{
  // The exact implementation only queues a toast and appends in-memory event
  // objects. It does not update PVR state or call a recording/backend owner.
  // A different callback or subclass requires its own persistence contract.
  return typeid(*this) == typeid(CPVREventLogJob) && callback == nullptr
             ? CheckpointResponsibility::NonPersistent
             : CheckpointResponsibility::Unknown;
}

CPVREventLogJob::CPVREventLogJob(bool bNotifyUser,
                                 EventLevel eLevel,
                                 const std::string& label,
                                 const std::string& msg,
                                 const std::string& icon)
{
  AddEvent(bNotifyUser, eLevel, label, msg, icon);
}

void CPVREventLogJob::AddEvent(bool bNotifyUser,
                               EventLevel eLevel,
                               const std::string& label,
                               const std::string& msg,
                               const std::string& icon)
{
  m_events.emplace_back(bNotifyUser, eLevel, label, msg, icon);
}

bool CPVREventLogJob::DoWork()
{
  for (const auto& event : m_events)
  {
    if (event.m_bNotifyUser)
      CGUIDialogKaiToast::QueueNotification(event.m_eLevel == EventLevel::Error
                                                ? CGUIDialogKaiToast::Error
                                                : CGUIDialogKaiToast::Info,
                                            event.m_label, event.m_msg, 5000, true);

    // Write event log entry.
    auto eventLog = CServiceBroker::GetEventLog();
    if (eventLog)
      eventLog->Add(std::make_shared<CNotificationEvent>(event.m_label, event.m_msg, event.m_icon,
                                                         event.m_eLevel));
  }
  return true;
}

} // namespace PVR
