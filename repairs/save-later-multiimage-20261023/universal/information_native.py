"""Exact Infinity Information resize bridge; all other XML dialogs unchanged."""
from __future__ import annotations

import hashlib
from pathlib import Path


PATH = 'xbmc/interfaces/legacy/WindowXML.cpp'
BEFORE = '2640f4ca6e034667bbc08383b77421cc37c5c87872da710c9e5b30e77da6d54d'
ORIGINAL = '''        if (message.GetParam1() == GUI_MSG_PAGE_CHANGE || message.GetParam1() == GUI_MSG_WINDOW_RESIZE)
          return A(CGUIMediaWindow::OnMessage(message));'''
REPLACEMENT = '''        if (message.GetParam1() == GUI_MSG_PAGE_CHANGE || message.GetParam1() == GUI_MSG_WINDOW_RESIZE)
        {
          const bool handled = A(CGUIMediaWindow::OnMessage(message));
#if defined(TARGET_ANDROID)
          // Only the newly owned Information dialog requests this callback.
          // Existing provider, native and Cobra dialogs retain their exact
          // message result and receive no callback, resource load or mutation.
          const std::string informationXML = ref(window)->GetProperty("xmlfile").asString();
          if (message.GetParam1() == GUI_MSG_WINDOW_RESIZE &&
              URIUtils::GetFileName(informationXML) == "InfinityInformation.xml" &&
              g_SkinInfo && g_SkinInfo->ID() == "skin.infinity.diggz")
          {
            ADDON::AddonPtr informationOwner;
            if (CServiceBroker::GetAddonMgr().GetAddon("script.infinity.commandcenter", informationOwner,
                                                     ADDON::OnlyEnabled::CHOICE_YES) &&
                informationOwner->Version().asString() == "0.3.5.34")
            {
              std::string informationRoot = CSpecialProtocol::TranslatePath(informationOwner->Path());
              URIUtils::RemoveSlashAtEnd(informationRoot);
              std::string callerRoot = m_scriptPath;
              URIUtils::RemoveSlashAtEnd(callerRoot);
              const std::string expectedXML = URIUtils::AddFileToFolder(informationRoot,
                  "resources/skins/Default/1080i/InfinityInformation.xml");
              if (callerRoot == informationRoot && informationXML == expectedXML)
              {
                // Use Kodi's existing asynchronous Python callback queue.
                // No GUI-thread wait, Python evaluation or layout polling.
                invokeCallback(new CallbackFunction<WindowXML>(this,&WindowXML::onInit));
                PulseActionEvent();
              }
            }
          }
#endif
          return handled;
        }'''


def patch(raw):
    if hashlib.sha256(raw).hexdigest() != BEFORE:
        raise RuntimeError('Information resize requires exact signed WindowXML source')
    text = raw.decode()
    changes = (
        ('#include "addons/Addon.h"', '#include "addons/Addon.h"\n#include "addons/AddonManager.h"\n#include "filesystem/SpecialProtocol.h"'),
        (ORIGINAL, REPLACEMENT),
    )
    for before, after in changes:
        if text.count(before) != 1:
            raise RuntimeError('Information resize source anchor changed')
        text = text.replace(before, after, 1)
    return text.encode()


def apply(source, overlay):
    raw = (Path(source) / PATH).read_bytes()
    updated = patch(raw)
    target = Path(overlay) / PATH
    if target.exists():
        raise RuntimeError('Overlapping native Information correction')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(updated)
    return {PATH: dict(original_sha256=BEFORE,
                      final_sha256=hashlib.sha256(updated).hexdigest(),
                      defect='Explicit Infinity Information modal does not receive resize callbacks',
                      justification='Android, exact Infinity skin, enabled CC34, exact owner path and exact owned XML guard; existing asynchronous onInit callback reflows without resetting text, scroll or focus; every other dialog retains original behavior')}
