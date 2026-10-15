/*
 *  Copyright (C) 2005-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "Skin.h"

#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityResponsiveness.h"
#endif

#include "FileItem.h"
#include "ServiceBroker.h"
#include "Util.h"
#include "addons/addoninfo/AddonType.h"
#include "dialogs/GUIDialogKaiToast.h"
#include "filesystem/Directory.h"
#include "filesystem/SpecialProtocol.h"
#include "guilib/GUIComponent.h"
#include "guilib/GUIWindowManager.h"
#include "guilib/LocalizeStrings.h"
#include "guilib/WindowIDs.h"
#include "messaging/ApplicationMessenger.h"
#include "messaging/helpers/DialogHelper.h"
#include "settings/Settings.h"
#include "settings/SettingsComponent.h"
#include "settings/lib/Setting.h"
#include "settings/lib/SettingDefinitions.h"
#include "threads/Timer.h"
#include "utils/FileUtils.h"
#include "utils/StringUtils.h"
#include "utils/URIUtils.h"
#include "utils/Variant.h"
#include "utils/XMLUtils.h"
#include "utils/log.h"

#include <charconv>
#include <cmath>
#include <memory>

#define XML_SETTINGS      "settings"
#define XML_SETTING       "setting"
#define XML_ATTR_TYPE     "type"
#define XML_ATTR_NAME     "name"
#define XML_ATTR_ID       "id"

using namespace XFILE;
using namespace KODI::MESSAGING;
using namespace std::chrono_literals;

using KODI::MESSAGING::HELPERS::DialogResponse;

std::shared_ptr<ADDON::CSkinInfo> g_SkinInfo;

namespace
{
constexpr auto DELAY = 500ms;
}

namespace ADDON
{

class CSkinSettingUpdateHandler : private ITimerCallback
{
public:
  CSkinSettingUpdateHandler(CAddon& addon)
  : m_addon(addon), m_timer(this) {}
  ~CSkinSettingUpdateHandler() override = default;

  void OnTimeout() override;
  void TriggerSave();
private:
  CAddon &m_addon;
  CTimer m_timer;
};

bool CSkinSetting::Serialize(TiXmlElement* parent) const
{
  if (parent == nullptr)
    return false;

  TiXmlElement setting(XML_SETTING);
  setting.SetAttribute(XML_ATTR_ID, name.c_str());
  setting.SetAttribute(XML_ATTR_TYPE, GetType());

  if (!SerializeSetting(&setting))
    return false;

  return parent->InsertEndChild(setting) != nullptr;
}

bool CSkinSetting::Deserialize(const TiXmlElement* element)
{
  if (element == nullptr)
    return false;

  name = XMLUtils::GetAttribute(element, XML_ATTR_ID);

  // backwards compatibility for guisettings.xml
  if (name.empty())
    name = XMLUtils::GetAttribute(element, XML_ATTR_NAME);

  return true;
}

bool CSkinSettingString::Deserialize(const TiXmlElement* element)
{
  value.clear();

  if (!CSkinSetting::Deserialize(element))
    return false;

  if (element->FirstChild() != nullptr)
    value = element->FirstChild()->Value();

  return true;
}

bool CSkinSettingString::SerializeSetting(TiXmlElement* element) const
{
  if (element == nullptr)
    return false;

  TiXmlText xmlValue(value);
  return element->InsertEndChild(xmlValue) != nullptr;
}

bool CSkinSettingBool::Deserialize(const TiXmlElement* element)
{
  value = false;

  if (!CSkinSetting::Deserialize(element))
    return false;

  if (element->FirstChild() != nullptr)
    value = StringUtils::EqualsNoCase(element->FirstChild()->ValueStr(), "true");

  return true;
}

bool CSkinSettingBool::SerializeSetting(TiXmlElement* element) const
{
  if (element == nullptr)
    return false;

  TiXmlText xmlValue(value ? "true" : "false");
  return element->InsertEndChild(xmlValue) != nullptr;
}

CSkinInfo::CSkinInfo(const AddonInfoPtr& addonInfo,
                     const RESOLUTION_INFO& resolution /* = RESOLUTION_INFO() */)
  : CAddon(addonInfo, AddonType::SKIN),
    m_defaultRes(resolution),
    m_effectsSlowDown(1.f),
    m_debugging(false)
{
  m_settingsUpdateHandler = std::make_unique<CSkinSettingUpdateHandler>(*this);
}

CSkinInfo::CSkinInfo(const AddonInfoPtr& addonInfo) : CAddon(addonInfo, AddonType::SKIN)
{
  for (const auto& values : Type(AddonType::SKIN)->GetValues())
  {
    if (values.first != "res")
      continue;

    int width = values.second.GetValue("res@width").asInteger();
    int height = values.second.GetValue("res@height").asInteger();
    bool defRes = values.second.GetValue("res@default").asBoolean();
    std::string folder = values.second.GetValue("res@folder").asString();
    std::string strAspect = values.second.GetValue("res@aspect").asString();
    float aspect = 0;

    std::vector<std::string> fracs = StringUtils::Split(strAspect, ':');
    if (fracs.size() == 2)
      aspect = (float)(atof(fracs[0].c_str()) / atof(fracs[1].c_str()));
    if (width > 0 && height > 0)
    {
      RESOLUTION_INFO res(width, height, aspect, folder);
      res.strId = strAspect; // for skin usage, store aspect string in strId
      if (defRes)
        m_defaultRes = res;
      m_resolutions.push_back(res);
    }
  }

  m_effectsSlowDown = Type(AddonType::SKIN)->GetValue("@effectslowdown").asFloat();
  if (m_effectsSlowDown == 0.0f)
    m_effectsSlowDown = 1.f;

  m_debugging = Type(AddonType::SKIN)->GetValue("@debugging").asBoolean();

  m_settingsUpdateHandler = std::make_unique<CSkinSettingUpdateHandler>(*this);
  LoadStartupWindows(addonInfo);
}

CSkinInfo::~CSkinInfo() = default;

namespace
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

bool CSkinInfo::UsesNativeWindowAdaptation() const
{
  if (UsesNativeResponsiveLayout())
    return true;
#if defined(TARGET_ANDROID)
  // Kodi's traditional skin resolver is landscape-centric and its GUI scaler may stretch X/Y
  // independently when an Android window becomes tall/narrow. On Android, keep one uniform
  // logical-to-physical scale even for ordinary legacy skins. No device-model routing.
  return true;
#else
  return false;
#endif
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

RESOLUTION_INFO CSkinInfo::GetNativeWindowResolution(const RESOLUTION_INFO& source) const
{
  if (UsesNativeResponsiveLayout())
    return GetNativeResponsiveResolution();

#if defined(TARGET_ANDROID)
  const RESOLUTION_INFO target = CServiceBroker::GetWinSystem()->GetGfxContext().GetResInfo();
  float usableWidth = 1.0f, usableHeight = 1.0f;
  InfinityUsableSize(target, usableWidth, usableHeight);
  const float targetRatio = usableWidth / usableHeight;
  const float sourceRatio =
      source.iWidth > 0 && source.iHeight > 0 ? static_cast<float>(source.iWidth) / source.iHeight
                                             : targetRatio;
  const float mismatch = std::max(targetRatio / std::max(0.01f, sourceRatio),
                                  sourceRatio / std::max(0.01f, targetRatio));
  if (mismatch <= 1.03f)
    return source;

  // Preserve the skin profile's logical area while matching the live Android window aspect.
  // This avoids skinny/tall or wide/flat distortion without assuming a specific phone/Fold model.
  const double area = std::max(1.0, static_cast<double>(source.iWidth) * source.iHeight);
  const double targetRatioD = static_cast<double>(targetRatio);
  int width = std::max(1, static_cast<int>(std::lround(std::sqrt(area * targetRatioD))));
  int height = std::max(1, static_cast<int>(std::lround(std::sqrt(area / targetRatioD))));
  width = std::max(8, ((width + 4) / 8) * 8);
  height = std::max(8, ((height + 4) / 8) * 8);

  RESOLUTION_INFO result = source;
  result.iWidth = width;
  result.iHeight = height;
  result.iScreenWidth = width;
  result.iScreenHeight = height;
  result.iSubtitles = height;
  result.fPixelRatio = 1.0f;
  result.strId = "infinity-android-adaptive";
  // Keep source.strMode unchanged: presentation still comes from the skin's own selected folder.
  return result;
#else
  return source;
#endif
}

void CSkinInfo::RefreshNativeResponsiveIncludes()
{
  if (!UsesNativeResponsiveLayout())
    return;
  const std::string current = GetNativeResponsiveClass();
  if (current == m_nativeResponsiveIncludesClass)
    return;
  // Keep Skin.AspectRatio / current-aspect consumers aligned with Kodi's responsive class.
  m_currentAspect = current;
  LoadIncludes();
}

struct closestRes
{
  explicit closestRes(const RESOLUTION_INFO &target) : m_target(target) { };
  bool operator()(const RESOLUTION_INFO &i, const RESOLUTION_INFO &j)
  {
    float diff = fabs(i.DisplayRatio() - m_target.DisplayRatio()) - fabs(j.DisplayRatio() - m_target.DisplayRatio());
    if (diff < 0) return true;
    if (diff > 0) return false;
    diff = fabs((float)i.iHeight - m_target.iHeight) - fabs((float)j.iHeight - m_target.iHeight);
    if (diff < 0) return true;
    if (diff > 0) return false;
    return fabs((float)i.iWidth - m_target.iWidth) < fabs((float)j.iWidth - m_target.iWidth);
  }
  RESOLUTION_INFO m_target;
};

void CSkinInfo::Start()
{
#if defined(TARGET_ANDROID)
  ++InfinityHealth::skinGeneration;
#endif
  if (!LoadUserSettings())
    CLog::Log(LOGWARNING, "CSkinInfo: failed to load skin settings");

  if (!m_resolutions.size())
  { // try falling back to whatever resolutions exist in the directory
    CFileItemList items;
    CDirectory::GetDirectory(Path(), items, "", DIR_FLAG_NO_FILE_DIRS);
    for (int i = 0; i < items.Size(); i++)
    {
      RESOLUTION_INFO res;
      if (items[i]->m_bIsFolder && TranslateResolution(items[i]->GetLabel(), res))
        m_resolutions.push_back(res);
    }
  }

  if (UsesNativeResponsiveLayout())
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
}

std::string CSkinInfo::GetSkinPath(const std::string& strFile, RESOLUTION_INFO *res,
                                  const std::string& strBaseDir /* = "" */,
                                  bool adaptWindow /* = true */) const
{
  if (m_resolutions.empty())
    return ""; // invalid skin

  std::string strPathToUse = Path();
  if (!strBaseDir.empty())
    strPathToUse = strBaseDir;

  // if the caller doesn't care about the resolution just use a temporary
  RESOLUTION_INFO tempRes;
  if (!res)
    res = &tempRes;

  // INFINITY_PROVIDER_COORDS_V1: a fallback XML owns its declared canvas.
  if (adaptWindow && UsesNativeResponsiveLayout())
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
  *res = *std::min_element(m_resolutions.begin(), m_resolutions.end(), closestRes(target));

  std::string strPath = URIUtils::AddFileToFolder(strPathToUse, res->strMode, strFile);
  if (CFileUtils::Exists(strPath))
  {
    if (adaptWindow && UsesNativeWindowAdaptation())
      *res = GetNativeWindowResolution(*res);
    return strPath;
  }

  // use the default resolution
  *res = m_defaultRes;
  const std::string defaultPath = URIUtils::AddFileToFolder(strPathToUse, res->strMode, strFile);
  if (adaptWindow && UsesNativeWindowAdaptation())
    *res = GetNativeWindowResolution(*res);
  return defaultPath;
}

bool CSkinInfo::HasSkinFile(const std::string &strFile) const
{
  return CFileUtils::Exists(GetSkinPath(strFile));
}

void CSkinInfo::LoadIncludes()
{
  std::string includesPath =
      CSpecialProtocol::TranslatePathConvertCase(GetSkinPath("Includes.xml"));
  CLog::Log(LOGINFO, "Loading skin includes from {}", includesPath);
  m_includes.Clear();
  m_includes.Load(includesPath);
  if (UsesNativeResponsiveLayout())
    m_nativeResponsiveIncludesClass = GetNativeResponsiveClass();
}

void CSkinInfo::LoadTimers()
{
  m_skinTimerManager =
      std::make_unique<CSkinTimerManager>(CServiceBroker::GetGUI()->GetInfoManager());
  const std::string timersPath =
      CSpecialProtocol::TranslatePathConvertCase(GetSkinPath("Timers.xml"));
  CLog::LogF(LOGINFO, "Trying to load skin timers from {}", timersPath);
  m_skinTimerManager->LoadTimers(timersPath);
}

void CSkinInfo::ProcessTimers()
{
  m_skinTimerManager->Process();
}
void CSkinInfo::ResolveIncludes(TiXmlElement* node,
                                std::map<INFO::InfoPtr, bool>* xmlIncludeConditions /* = nullptr */)
{
  if(xmlIncludeConditions)
    xmlIncludeConditions->clear();

  m_includes.Resolve(node, xmlIncludeConditions);
}

int CSkinInfo::GetStartWindow() const
{
  int windowID = CServiceBroker::GetSettingsComponent()->GetSettings()->GetInt(CSettings::SETTING_LOOKANDFEEL_STARTUPWINDOW);
  assert(m_startupWindows.size());
  for (std::vector<CStartupWindow>::const_iterator it = m_startupWindows.begin(); it != m_startupWindows.end(); ++it)
  {
    if (windowID == (*it).m_id)
      return windowID;
  }
  // return our first one
  return m_startupWindows[0].m_id;
}

bool CSkinInfo::LoadStartupWindows(const AddonInfoPtr& addonInfo)
{
  m_startupWindows.clear();
  m_startupWindows.emplace_back(WINDOW_HOME, "513");
  m_startupWindows.emplace_back(WINDOW_TV_CHANNELS, "19180");
  m_startupWindows.emplace_back(WINDOW_TV_GUIDE, "19273");
  m_startupWindows.emplace_back(WINDOW_RADIO_CHANNELS, "19183");
  m_startupWindows.emplace_back(WINDOW_RADIO_GUIDE, "19274");
  m_startupWindows.emplace_back(WINDOW_PROGRAMS, "0");
  m_startupWindows.emplace_back(WINDOW_PICTURES, "1");
  m_startupWindows.emplace_back(WINDOW_MUSIC_NAV, "2");
  m_startupWindows.emplace_back(WINDOW_VIDEO_NAV, "3");
  m_startupWindows.emplace_back(WINDOW_FILES, "7");
  m_startupWindows.emplace_back(WINDOW_SETTINGS_MENU, "5");
  m_startupWindows.emplace_back(WINDOW_WEATHER, "8");
  m_startupWindows.emplace_back(WINDOW_FAVOURITES, "1036");
  return true;
}

void CSkinInfo::GetSkinPaths(std::vector<std::string> &paths) const
{
  if (UsesNativeResponsiveLayout())
  {
    const std::string responsiveRoot = URIUtils::AddFileToFolder(Path(), "responsive");
    // Every Infinity responsive class is a complete XML universe. Scan only the active class for
    // custom windows; adding responsive/base here would register the same custom window IDs twice.
    // Per-file GetSkinPath() still has responsive/base as a corruption/missing-file safety fallback.
    paths.push_back(URIUtils::AddFileToFolder(responsiveRoot, GetNativeResponsiveClass()));
    return;
  }

  RESOLUTION_INFO res;
  GetSkinPath("Home.xml", &res);
  if (!res.strMode.empty())
    paths.push_back(URIUtils::AddFileToFolder(Path(), res.strMode));
  if (res.strMode != m_defaultRes.strMode)
    paths.push_back(URIUtils::AddFileToFolder(Path(), m_defaultRes.strMode));
}

bool CSkinInfo::TranslateResolution(const std::string &name, RESOLUTION_INFO &res)
{
  std::string lower(name); StringUtils::ToLower(lower);
  if (lower == "pal")
    res = RESOLUTION_INFO(720, 576, 4.0f/3, "pal");
  else if (lower == "pal16x9")
    res = RESOLUTION_INFO(720, 576, 16.0f/9, "pal16x9");
  else if (lower == "ntsc")
    res = RESOLUTION_INFO(720, 480, 4.0f/3, "ntsc");
  else if (lower == "ntsc16x9")
    res = RESOLUTION_INFO(720, 480, 16.0f/9, "ntsc16x9");
  else if (lower == "720p")
    res = RESOLUTION_INFO(1280, 720, 0, "720p");
  else if (lower == "1080i")
    res = RESOLUTION_INFO(1920, 1080, 0, "1080i");
  else
    return false;
  return true;
}

int CSkinInfo::GetFirstWindow() const
{
  int startWindow = GetStartWindow();
  if (HasSkinFile("Startup.xml"))
    startWindow = WINDOW_STARTUP_ANIM;
  return startWindow;
}

bool CSkinInfo::IsInUse() const
{
  // Could extend this to prompt for reverting to the standard skin perhaps
  return CServiceBroker::GetSettingsComponent()->GetSettings()->GetString(CSettings::SETTING_LOOKANDFEEL_SKIN) == ID();
}

const INFO::CSkinVariableString* CSkinInfo::CreateSkinVariable(const std::string& name, int context)
{
  return m_includes.CreateSkinVariable(name, context);
}

void CSkinInfo::OnPreInstall()
{
  bool skinLoaded = g_SkinInfo != nullptr;
  if (IsInUse() && skinLoaded)
    CServiceBroker::GetAppMessenger()->SendMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
                                               "UnloadSkin");
}

void CSkinInfo::OnPostInstall(bool update, bool modal)
{
  if (!g_SkinInfo)
    return;

  if (IsInUse() || (!update && !modal &&
                    HELPERS::ShowYesNoDialogText(CVariant{Name()}, CVariant{24099}) ==
                        DialogResponse::CHOICE_YES))
  {
    CGUIDialogKaiToast *toast = CServiceBroker::GetGUI()->GetWindowManager().GetWindow<CGUIDialogKaiToast>(WINDOW_DIALOG_KAI_TOAST);
    if (toast)
    {
      toast->ResetTimer();
      toast->Close(true);
    }
    if (CServiceBroker::GetSettingsComponent()->GetSettings()->GetString(CSettings::SETTING_LOOKANDFEEL_SKIN) == ID())
      CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
                                                 "ReloadSkin");
    else
      CServiceBroker::GetSettingsComponent()->GetSettings()->SetString(CSettings::SETTING_LOOKANDFEEL_SKIN, ID());
  }
}

void CSkinInfo::Unload()
{
  m_skinTimerManager->Stop();
}

bool CSkinInfo::TimerIsRunning(const std::string& timer) const
{
  return m_skinTimerManager->TimerIsRunning(timer);
}

float CSkinInfo::GetTimerElapsedSeconds(const std::string& timer) const
{
  return m_skinTimerManager->GetTimerElapsedSeconds(timer);
}

void CSkinInfo::TimerStart(const std::string& timer) const
{
  m_skinTimerManager->TimerStart(timer);
}

void CSkinInfo::TimerStop(const std::string& timer) const
{
  m_skinTimerManager->TimerStop(timer);
}

void CSkinInfo::SettingOptionsSkinColorsFiller(const SettingConstPtr& setting,
                                               std::vector<StringSettingOption>& list,
                                               std::string& current,
                                               void* data)
{
  if (!g_SkinInfo)
    return;

  std::string settingValue = std::static_pointer_cast<const CSettingString>(setting)->GetValue();
  // Remove the .xml extension from the Themes
  if (URIUtils::HasExtension(settingValue, ".xml"))
    URIUtils::RemoveExtension(settingValue);
  current = "SKINDEFAULT";

  // There is a default theme (just defaults.xml)
  // any other *.xml files are additional color themes on top of this one.

  // add the default label
  list.emplace_back(g_localizeStrings.Get(15109), "SKINDEFAULT"); // the standard defaults.xml will be used!

  // Search for colors in the Current skin!
  std::vector<std::string> vecColors;
  std::string strPath = URIUtils::AddFileToFolder(g_SkinInfo->Path(), "colors");

  CFileItemList items;
  CDirectory::GetDirectory(CSpecialProtocol::TranslatePathConvertCase(strPath), items, ".xml", DIR_FLAG_DEFAULTS);
  // Search for Themes in the Current skin!
  for (int i = 0; i < items.Size(); ++i)
  {
    CFileItemPtr pItem = items[i];
    if (!pItem->m_bIsFolder && !StringUtils::EqualsNoCase(pItem->GetLabel(), "defaults.xml"))
    { // not the default one
      vecColors.push_back(pItem->GetLabel().substr(0, pItem->GetLabel().size() - 4));
    }
  }
  sort(vecColors.begin(), vecColors.end(), sortstringbyname());
  for (int i = 0; i < (int) vecColors.size(); ++i)
    list.emplace_back(vecColors[i], vecColors[i]);

  // try to find the best matching value
  for (const auto& elem : list)
  {
    if (StringUtils::EqualsNoCase(elem.value, settingValue))
      current = settingValue;
  }
}

namespace
{
void GetFontsetsFromFile(const std::string& fontsetFilePath,
                         std::vector<StringSettingOption>& list,
                         const std::string& settingValue,
                         bool* currentValueSet)
{
  CXBMCTinyXML xmlDoc;
  if (xmlDoc.LoadFile(fontsetFilePath))
  {
    TiXmlElement* rootElement = xmlDoc.RootElement();
    g_SkinInfo->ResolveIncludes(rootElement);
    if (rootElement && (rootElement->ValueStr() == "fonts"))
    {
      const TiXmlElement* fontsetElement = rootElement->FirstChildElement("fontset");
      while (fontsetElement)
      {
        const char* idAttr = fontsetElement->Attribute("id");
        const char* idLocAttr = fontsetElement->Attribute("idloc");
        if (idAttr)
        {
          if (idLocAttr)
            list.emplace_back(g_localizeStrings.Get(atoi(idLocAttr)), idAttr);
          else
            list.emplace_back(idAttr, idAttr);

          if (StringUtils::EqualsNoCase(idAttr, settingValue))
            *currentValueSet = true;
        }
        fontsetElement = fontsetElement->NextSiblingElement("fontset");
      }
    }
  }
}
} // unnamed namespace

void CSkinInfo::SettingOptionsSkinFontsFiller(const SettingConstPtr& setting,
                                              std::vector<StringSettingOption>& list,
                                              std::string& current,
                                              void* data)
{
  if (!g_SkinInfo)
    return;

  const std::string settingValue =
      std::static_pointer_cast<const CSettingString>(setting)->GetValue();
  bool currentValueSet = false;

  // Look for fontsets that are defined in the skin's Font.xml file
  const std::string fontsetFilePath = g_SkinInfo->GetSkinPath("Font.xml");
  GetFontsetsFromFile(fontsetFilePath, list, settingValue, &currentValueSet);

  // Look for additional fontsets that are defined in .xml files in the skin's fonts directory
  CFileItemList xmlFileItems;
  CDirectory::GetDirectory(CSpecialProtocol::TranslatePath("special://skin/fonts"), xmlFileItems,
                           ".xml", DIR_FLAG_DEFAULTS);
  for (int i = 0; i < xmlFileItems.Size(); i++)
    GetFontsetsFromFile(xmlFileItems[i]->GetPath(), list, settingValue, &currentValueSet);

  if (list.empty())
  { // Since no fontset is defined, there is no selection of a fontset, so disable the component
    CLog::LogF(LOGERROR, "No fontsets found");
    list.emplace_back(g_localizeStrings.Get(13278), "");
    current = "";
    currentValueSet = true;
  }

  if (!currentValueSet)
    current = list[0].value;
}

void CSkinInfo::SettingOptionsSkinThemesFiller(const SettingConstPtr& setting,
                                               std::vector<StringSettingOption>& list,
                                               std::string& current,
                                               void* data)
{
  // get the chosen theme and remove the extension from the current theme (backward compat)
  std::string settingValue = std::static_pointer_cast<const CSettingString>(setting)->GetValue();
  URIUtils::RemoveExtension(settingValue);
  current = "SKINDEFAULT";

  // there is a default theme (just Textures.xbt)
  // any other *.xbt files are additional themes on top of this one.

  // add the default Label
  list.emplace_back(g_localizeStrings.Get(15109), "SKINDEFAULT"); // the standard Textures.xbt will be used

  // search for themes in the current skin!
  std::vector<std::string> vecTheme;
  CUtil::GetSkinThemes(vecTheme);

  // sort the themes for GUI and list them
  for (int i = 0; i < (int) vecTheme.size(); ++i)
    list.emplace_back(vecTheme[i], vecTheme[i]);

  // try to find the best matching value
  for (const auto& elem : list)
  {
    if (StringUtils::EqualsNoCase(elem.value, settingValue))
      current = settingValue;
  }
}

void CSkinInfo::SettingOptionsStartupWindowsFiller(const SettingConstPtr& setting,
                                                   std::vector<IntegerSettingOption>& list,
                                                   int& current,
                                                   void* data)
{
  if (!g_SkinInfo)
    return;

  int settingValue = std::static_pointer_cast<const CSettingInt>(setting)->GetValue();
  current = -1;

  const std::vector<CStartupWindow> &startupWindows = g_SkinInfo->GetStartupWindows();

  for (std::vector<CStartupWindow>::const_iterator it = startupWindows.begin(); it != startupWindows.end(); ++it)
  {
    std::string windowName = it->m_name;
    if (StringUtils::IsNaturalNumber(windowName))
      windowName = g_localizeStrings.Get(atoi(windowName.c_str()));
    int windowID = it->m_id;

    list.emplace_back(windowName, windowID);

    if (settingValue == windowID)
      current = settingValue;
  }

  // if the current value hasn't been properly set, set it to the first window in the list
  if (current < 0)
    current = list[0].value;
}

void CSkinInfo::ToggleDebug()
{
  m_debugging = !m_debugging;
}

int CSkinInfo::TranslateString(const std::string &setting)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite)
    return -1;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  // run through and see if we have this setting
  for (const auto& it : m_strings)
  {
    if (StringUtils::EqualsNoCase(setting, it.second->name))
      return it.first;
  }

  // didn't find it - insert it
  CSkinSettingStringPtr skinString(new CSkinSettingString());
  skinString->name = setting;

  int number = m_bools.size() + m_strings.size();
  m_strings.insert(std::pair<int, CSkinSettingStringPtr>(number, skinString));
#if defined(TARGET_ANDROID)
  m_checkpointDirty = true;
#endif

  return number;
}

int CSkinInfo::GetInt(int setting) const
{
  const std::string settingValue = GetString(setting);
  if (settingValue.empty())
  {
    return -1;
  }
  int settingValueInt{-1};
  std::from_chars(settingValue.data(), settingValue.data() + settingValue.size(), settingValueInt);
  return settingValueInt;
}

const std::string& CSkinInfo::GetString(int setting) const
{
  const auto& it = m_strings.find(setting);
  if (it != m_strings.end())
    return it->second->value;

  return StringUtils::Empty;
}

void CSkinInfo::SetString(int setting, const std::string &label)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite)
    return;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  auto&& it = m_strings.find(setting);
  if (it != m_strings.end())
  {
#if defined(TARGET_ANDROID)
    if (it->second->value != label)
      m_checkpointDirty = true;
#endif
    it->second->value = label;
#if defined(TARGET_ANDROID)
    settingsLock.unlock(); // Timer restart can join a callback which saves these settings.
#endif
    m_settingsUpdateHandler->TriggerSave();
    return;
  }

  CLog::Log(LOGFATAL, "{}: unknown setting ({}) requested", __FUNCTION__, setting);
  assert(false);
}

int CSkinInfo::TranslateBool(const std::string &setting)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite)
    return -1;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  // run through and see if we have this setting
  for (const auto& it : m_bools)
  {
    if (StringUtils::EqualsNoCase(setting, it.second->name))
      return it.first;
  }

  // didn't find it - insert it
  CSkinSettingBoolPtr skinBool(new CSkinSettingBool());
  skinBool->name = setting;

  int number = m_bools.size() + m_strings.size();
  m_bools.insert(std::pair<int, CSkinSettingBoolPtr>(number, skinBool));
#if defined(TARGET_ANDROID)
  m_checkpointDirty = true;
#endif
#if defined(TARGET_ANDROID)
  settingsLock.unlock(); // Timer restart can join a callback which saves these settings.
#endif
  m_settingsUpdateHandler->TriggerSave();

  return number;
}

bool CSkinInfo::GetBool(int setting) const
{
  const auto& it = m_bools.find(setting);
  if (it != m_bools.end())
    return it->second->value;

  // default is to return false
  return false;
}

void CSkinInfo::SetBool(int setting, bool set)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite)
    return;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  auto&& it = m_bools.find(setting);
  if (it != m_bools.end())
  {
#if defined(TARGET_ANDROID)
    if (it->second->value != set)
      m_checkpointDirty = true;
#endif
    it->second->value = set;
#if defined(TARGET_ANDROID)
    settingsLock.unlock(); // Timer restart can join a callback which saves these settings.
#endif
    m_settingsUpdateHandler->TriggerSave();
    return;
  }

  CLog::Log(LOGFATAL, "{}: unknown setting ({}) requested", __FUNCTION__, setting);
  assert(false);
}

std::set<CSkinSettingPtr> CSkinInfo::GetSkinSettings() const
{
  std::set<CSkinSettingPtr> settings;

  for (const auto& setting : m_settings)
    settings.insert(setting.second);

  return settings;
}

CSkinSettingPtr CSkinInfo::GetSkinSetting(const std::string& settingId)
{
  const auto& it = m_settings.find(settingId);
  if (it != m_settings.end())
    return it->second;

  return nullptr;
}

std::shared_ptr<const CSkinSetting> CSkinInfo::GetSkinSetting(const std::string& settingId) const
{
  const auto& it = m_settings.find(settingId);
  if (it != m_settings.end())
    return it->second;

  return nullptr;
}

void CSkinInfo::Reset(const std::string &setting)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite)
    return;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  // run through and see if we have this setting as a string
  for (auto& it : m_strings)
  {
    if (StringUtils::EqualsNoCase(setting, it.second->name))
    {
#if defined(TARGET_ANDROID)
      if (!it.second->value.empty())
        m_checkpointDirty = true;
#endif
      it.second->value.clear();
#if defined(TARGET_ANDROID)
      settingsLock.unlock(); // Timer restart can join a callback which saves these settings.
#endif
      m_settingsUpdateHandler->TriggerSave();
      return;
    }
  }

  // and now check for the skin bool
  for (auto& it : m_bools)
  {
    if (StringUtils::EqualsNoCase(setting, it.second->name))
    {
#if defined(TARGET_ANDROID)
      if (it.second->value)
        m_checkpointDirty = true;
#endif
      it.second->value = false;
#if defined(TARGET_ANDROID)
      settingsLock.unlock(); // Timer restart can join a callback which saves these settings.
#endif
      m_settingsUpdateHandler->TriggerSave();
      return;
    }
  }
}

void CSkinInfo::Reset()
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite)
    return;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  // clear all the settings and strings from this skin.
  for (auto& it : m_bools)
  {
#if defined(TARGET_ANDROID)
    m_checkpointDirty = m_checkpointDirty || it.second->value;
#endif
    it.second->value = false;
  }

  for (auto& it : m_strings)
  {
#if defined(TARGET_ANDROID)
    m_checkpointDirty = m_checkpointDirty || !it.second->value.empty();
#endif
    it.second->value.clear();
  }

#if defined(TARGET_ANDROID)
  settingsLock.unlock(); // Timer restart can join a callback which saves these settings.
#endif
  m_settingsUpdateHandler->TriggerSave();
}

std::set<CSkinSettingPtr> CSkinInfo::ParseSettings(const TiXmlElement* rootElement)
{
  std::set<CSkinSettingPtr> settings;
  if (rootElement == nullptr)
    return settings;

  const TiXmlElement *settingElement = rootElement->FirstChildElement(XML_SETTING);
  while (settingElement != nullptr)
  {
    CSkinSettingPtr setting = ParseSetting(settingElement);
    if (setting != nullptr)
      settings.insert(setting);

    settingElement = settingElement->NextSiblingElement(XML_SETTING);
  }

  return settings;
}

CSkinSettingPtr CSkinInfo::ParseSetting(const TiXmlElement* element)
{
  if (element == nullptr)
    return CSkinSettingPtr();

  std::string settingType = XMLUtils::GetAttribute(element, XML_ATTR_TYPE);
  CSkinSettingPtr setting;
  if (settingType == "string")
    setting = CSkinSettingPtr(new CSkinSettingString());
  else if (settingType == "bool")
    setting = CSkinSettingPtr(new CSkinSettingBool());
  else
    return CSkinSettingPtr();

  if (setting == nullptr)
    return CSkinSettingPtr();

  if (!setting->Deserialize(element))
    return CSkinSettingPtr();

  return setting;
}

bool CSkinInfo::SettingsLoaded(AddonInstanceId id /* = ADDON_SETTINGS_ID */) const
{
  if (id != ADDON_SETTINGS_ID)
    return false;

  return !m_strings.empty() || !m_bools.empty();
}

bool CSkinInfo::SettingsFromXML(const CXBMCTinyXML& doc,
                                bool loadDefaults,
                                AddonInstanceId id /* = ADDON_SETTINGS_ID */)
{
#if defined(TARGET_ANDROID)
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite)
    return false;
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  const TiXmlElement *rootElement = doc.RootElement();
  if (rootElement == nullptr || rootElement->ValueStr().compare(XML_SETTINGS) != 0)
  {
    CLog::Log(LOGWARNING, "CSkinInfo: no <settings> tag found");
    return false;
  }

  m_settings.clear();
  m_strings.clear();
  m_bools.clear();

  int number = 0;
  std::set<CSkinSettingPtr> settings = ParseSettings(rootElement);
  for (const auto& setting : settings)
  {
    if (setting->GetType() == "string")
    {
      m_settings.insert(std::make_pair(setting->name, setting));
      m_strings.insert(
          std::make_pair(number++, std::dynamic_pointer_cast<CSkinSettingString>(setting)));
    }
    else if (setting->GetType() == "bool")
    {
      m_settings.insert(std::make_pair(setting->name, setting));
      m_bools.insert(
          std::make_pair(number++, std::dynamic_pointer_cast<CSkinSettingBool>(setting)));
    }
    else
      CLog::Log(LOGWARNING, "CSkinInfo: ignoring setting of unknown type \"{}\"",
                setting->GetType());
  }

  return true;
}

bool CSkinInfo::SettingsToXML(CXBMCTinyXML& doc, AddonInstanceId id /* = ADDON_SETTINGS_ID */) const
{
#if defined(TARGET_ANDROID)
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
#endif
  // add the <skinsettings> tag
  TiXmlElement rootElement(XML_SETTINGS);
  TiXmlNode *settingsNode = doc.InsertEndChild(rootElement);
  if (settingsNode == nullptr)
  {
    CLog::Log(LOGWARNING, "CSkinInfo: could not create <settings> tag");
#if defined(TARGET_ANDROID)
    InfinityAndroidCheckpoint::RecordFailure("skin_settings", "create_settings_node");
#endif
    return false;
  }

  TiXmlElement* settingsElement = settingsNode->ToElement();
  for (const auto& it : m_bools)
  {
    if (!it.second->Serialize(settingsElement))
    {
      CLog::Log(LOGWARNING, "CSkinInfo: failed to save string setting \"{}\"", it.second->name);
#if defined(TARGET_ANDROID)
      InfinityAndroidCheckpoint::RecordFailure("skin_settings", "serialize_bool");
#endif
      return false;
    }
  }

  for (const auto& it : m_strings)
  {
    if (!it.second->Serialize(settingsElement))
    {
      CLog::Log(LOGWARNING, "CSkinInfo: failed to save bool setting \"{}\"", it.second->name);
#if defined(TARGET_ANDROID)
      InfinityAndroidCheckpoint::RecordFailure("skin_settings", "serialize_string");
#endif
      return false;
    }
  }

  return true;
}

#if defined(TARGET_ANDROID)
bool CSkinInfo::CheckpointForAndroidExit()
{
  InfinityAndroidCheckpoint::CheckpointWriteGuard checkpointWrite("skin_settings");
  if (!checkpointWrite || !InfinityAndroidCheckpoint::IsPersistingOnThisThread())
  {
    InfinityAndroidCheckpoint::RecordFailure("skin_settings", "unauthorized_checkpoint");
    return false;
  }
  std::unique_lock<CCriticalSection> settingsLock(m_checkpointSettingsMutex);
  if (!m_checkpointDirty)
    return true;
  if (!SaveSettings())
  {
    InfinityAndroidCheckpoint::RecordFailure("skin_settings", "save_dirty_skin");
    return false;
  }
  m_checkpointDirty = false;
  return true;
}
#endif

void CSkinSettingUpdateHandler::OnTimeout()
{
  m_addon.SaveSettings();
}

void CSkinSettingUpdateHandler::TriggerSave()
{
  if (m_timer.IsRunning())
    m_timer.Restart();
  else
    m_timer.Start(DELAY);
}

} /*namespace ADDON*/

#if defined(TARGET_ANDROID)
bool InfinityAndroidCheckpoint::CheckpointSkinSettings()
{
  if (!g_SkinInfo)
  {
    RecordFailure("skin_settings", "active_skin_unavailable");
    return false;
  }
  return g_SkinInfo->CheckpointForAndroidExit();
}
#endif
