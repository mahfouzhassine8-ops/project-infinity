"""Append an exact-owned CC35/UI18 resize bridge to the retained CC34 bridge."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('retained_information_native', HERE.parent / 'universal/information_native.py')
retained = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retained)
PATH = retained.PATH
ANCHOR = '#endif\n          return handled;'
EXTENSION = '''#endif
#if defined(TARGET_ANDROID)
          // New-version Infinity-owned dialogs only. The CC34 callback above
          // remains intact; older popup Python must not receive extra onInit.
          const std::string responsiveXML = ref(window)->GetProperty("xmlfile").asString();
          const std::string responsiveName = URIUtils::GetFileName(responsiveXML);
          const bool titleOptions = responsiveName == "InfinityItemOptions.xml";
          if (message.GetParam1() == GUI_MSG_WINDOW_RESIZE &&
              (titleOptions || responsiveName == "InfinityInformation.xml") &&
              g_SkinInfo && g_SkinInfo->ID() == "skin.infinity.diggz")
          {
            std::string callerRoot = m_scriptPath;
            URIUtils::RemoveSlashAtEnd(callerRoot);
            std::string ownerRoot;
            ADDON::AddonPtr responsiveOwner;
            if (CServiceBroker::GetAddonMgr().GetAddon("script.infinity.commandcenter", responsiveOwner,
                                                     ADDON::OnlyEnabled::CHOICE_YES) &&
                responsiveOwner->Version().asString() == "0.3.5.35")
            {
              std::string candidate = CSpecialProtocol::TranslatePath(responsiveOwner->Path());
              URIUtils::RemoveSlashAtEnd(candidate);
              if (candidate == callerRoot) ownerRoot = candidate;
            }
            if (ownerRoot.empty() && titleOptions &&
                CServiceBroker::GetAddonMgr().GetAddon("script.infinity.uirepair", responsiveOwner,
                                                     ADDON::OnlyEnabled::CHOICE_YES) &&
                responsiveOwner->Version().asString() == "0.1.18")
            {
              std::string candidate = CSpecialProtocol::TranslatePath(responsiveOwner->Path());
              URIUtils::RemoveSlashAtEnd(candidate);
              if (candidate == callerRoot) ownerRoot = candidate;
            }
            if (!ownerRoot.empty())
            {
              const std::string fallbackXML = URIUtils::AddFileToFolder(ownerRoot,
                  "resources/skins/Default/1080i/" + responsiveName);
              // WindowXML resolves this named active-skin XML before the
              // owner's fallback. No other skin file or caller opts in.
              const bool exactXML = responsiveXML == fallbackXML ||
                  (titleOptions && responsiveXML == URIUtils::AddFileToFolder(g_SkinInfo->Path(),
                      "unified/InfinityItemOptions.xml"));
              if (exactXML)
              {
                invokeCallback(new CallbackFunction<WindowXML>(this,&WindowXML::onInit));
                PulseActionEvent();
              }
            }
          }
#endif
          return handled;'''


def patch(raw, current):
    expected = retained.patch(raw)
    if current != expected:
        raise RuntimeError('New popup reflow requires exact retained CC34 resize bytes')
    text = current.decode()
    if text.count(ANCHOR) != 1:
        raise RuntimeError('Owned resize return boundary changed')
    updated = text.replace(ANCHOR, EXTENSION, 1).encode()
    if updated.decode().replace(EXTENSION, ANCHOR, 1).encode() != expected:
        raise RuntimeError('Nonowned WindowXML bytes changed')
    return updated


def apply(source, overlay):
    raw = (Path(source) / PATH).read_bytes()
    target = Path(overlay) / PATH
    updated = patch(raw, target.read_bytes())
    target.write_bytes(updated)
    return {PATH: dict(original_sha256=retained.BEFORE,
        final_sha256=hashlib.sha256(updated).hexdigest(),
        defect='Owned Information/Title Options need resize events without input polling',
        justification='Retained CC34 bridge plus exact CC35/UI18 caller, version, skin and owned XML guards; existing asynchronous onInit only; all other callbacks and base result unchanged')}
