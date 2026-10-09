#include "InfinityAndroidCheckpoint.h"

#include "Util.h"
#include "filesystem/SpecialProtocol.h"
#include "utils/Digest.h"

#include <cstdlib>
#include <string>
#include <utility>
#include <vector>

namespace InfinityAndroidCheckpoint
{
namespace
{
struct Contract
{
  const char* script;
  const char* addon;
  const char* owner;
  std::vector<std::pair<const char*, const char*>> source;
};
const std::vector<Contract>& Contracts()
{
  // Generated from the reviewed matching runtime add-on sources. Every pin is
  // checked at invocation admission AND at checkpoint. IDs/basenames alone
  // never grant persistent-writer exclusion. Arbitrary user overrides fail closed.
  static const auto* contracts = new std::vector<Contract>{
    {"script.infinity.commandcenter/service.py", "script.infinity.commandcenter", "command_center", {
      {"script.infinity.commandcenter/checkpoint_runtime.py", "d69c4da55c53fe9759e2797c28aaacea28596096d2ad98bebe6f173c66441c73"},
      {"script.infinity.commandcenter/common.py", "ce70fd11d979862ea8ceca9b5fc426c5bb4be42f060621baed53d788df5a3c31"},
      {"script.infinity.commandcenter/default.py", "182d9bb1aeb1b0b21138bb2488357b4ae179f242a86739f40f552c471079bc09"},
      {"script.infinity.commandcenter/experience.py", "5c9da1aab8a9de3db578f8a589230a9de7e96e3e3678923c98bfc2314d4cbd5a"},
      {"script.infinity.commandcenter/persistence_participant.py", "7658db0f21c20853f272f61832e720df02b2b4b9ebaeba83ca1c7ba8758e1b9b"},
      {"script.infinity.commandcenter/plugin.py", "57c300c96c9385222da35e3e3507749f5d1614be0911f8c5ec3402fe1fd3621a"},
      {"script.infinity.commandcenter/resume_hub.py", "93b9c6796dc364793e4bad8dd45e07d3c231dacd01303ca609687bacd9f8e696"},
      {"script.infinity.commandcenter/service.py", "094cef3d11d1293573bba0e4f543cfcae81995df1f7730dd0f1f2731050d8da2"},
      {"script.infinity.commandcenter/skin_upgrade.py", "044aa0dc3e6d22f1cc585e503c482cb1d5ba58fb6734298449480ca02c53e1f8"},
      {"script.infinity.commandcenter/view_mode.py", "5f5583e9c36e32e970a0341ca353d32dd92e48d41079aaabaf7a113c66ddfc71"},
      {"script.infinity.commandcenter/addon.xml", "c274318b59563e0febb07538e5abe7de0df02b61cadd0c4ab39f066261a5f191"},
    }},
    {"script.infinity.commandcenter/plugin.py", "script.infinity.commandcenter", "command_center_client", {
      {"script.infinity.commandcenter/checkpoint_runtime.py", "d69c4da55c53fe9759e2797c28aaacea28596096d2ad98bebe6f173c66441c73"},
      {"script.infinity.commandcenter/common.py", "ce70fd11d979862ea8ceca9b5fc426c5bb4be42f060621baed53d788df5a3c31"},
      {"script.infinity.commandcenter/default.py", "182d9bb1aeb1b0b21138bb2488357b4ae179f242a86739f40f552c471079bc09"},
      {"script.infinity.commandcenter/experience.py", "5c9da1aab8a9de3db578f8a589230a9de7e96e3e3678923c98bfc2314d4cbd5a"},
      {"script.infinity.commandcenter/persistence_participant.py", "7658db0f21c20853f272f61832e720df02b2b4b9ebaeba83ca1c7ba8758e1b9b"},
      {"script.infinity.commandcenter/plugin.py", "57c300c96c9385222da35e3e3507749f5d1614be0911f8c5ec3402fe1fd3621a"},
      {"script.infinity.commandcenter/resume_hub.py", "93b9c6796dc364793e4bad8dd45e07d3c231dacd01303ca609687bacd9f8e696"},
      {"script.infinity.commandcenter/service.py", "094cef3d11d1293573bba0e4f543cfcae81995df1f7730dd0f1f2731050d8da2"},
      {"script.infinity.commandcenter/skin_upgrade.py", "044aa0dc3e6d22f1cc585e503c482cb1d5ba58fb6734298449480ca02c53e1f8"},
      {"script.infinity.commandcenter/view_mode.py", "5f5583e9c36e32e970a0341ca353d32dd92e48d41079aaabaf7a113c66ddfc71"},
      {"script.infinity.commandcenter/addon.xml", "c274318b59563e0febb07538e5abe7de0df02b61cadd0c4ab39f066261a5f191"},
    }},
    {"service.infinity.compat/service.py", "service.infinity.compat", "compat", {
      {"service.infinity.compat/service.py", "bacdf368a8ec77d48ddfa34279e64a445d2f9ae048b1a7bec15eca48d86b7c4d"},
      {"service.infinity.compat/compat_runtime.py", "ba14d7b3e0fb9d3b9f557ebf7d59decc014668a69219543a93d66dd0f4aa6a6e"},
      {"service.infinity.compat/checkpoint_runtime.py", "82785f254ac6ec1746b22a092a949e8209701be2d06bd26252ffc05479e249fd"},
    }},
    {"service.infinity.compat/layout_service.py", "service.infinity.compat", "nonpersistent:layout-properties", {
      {"service.infinity.compat/layout_service.py", "1f1da17d8d9f2fbbdc8b2c3bbe9ee00b078939fe2589a34029374156f06319cb"},
    }},
    {"service.infinity.compat/theme_contract.py", "service.infinity.compat", "reconstructible-cache:theme-revision", {
      {"service.infinity.compat/theme_contract.py", "93320b9c0bfdb3ea87b1d76d2aae1a39bef715015977326a74740f3490410735"},
    }},
    {"service.infinity.refresh/service.py", "service.infinity.refresh", "reconstructible-cache:refresh-policy", {
      {"service.infinity.refresh/service.py", "e3dbabd16fb1fbc1825c5bca73b5d142e75d9d2b4465bfb1b49d439c518daac3"},
    }},
    {"script.infinity.commandcenter/service.py", "script.infinity.commandcenter", "command_center", {
      {"script.infinity.commandcenter/addon.xml", "23320bab6c3a1d661987ee30533dc7a8890ca67ed4ff87b2fc6e6014e2e5b69a"},
      {"script.infinity.commandcenter/checkpoint_runtime.py", "30fb11385186d9ee78c7c0485f0de7cd41ab2df52794f4ceda7cd0a7d724ce3b"},
      {"script.infinity.commandcenter/common.py", "0e2077a694a060bec1b37e70f59fbfd71ef7fd39f0b392838feacdd8155bd44e"},
      {"script.infinity.commandcenter/default.py", "fa6c1827385b2ed4e704775d10a23dc7bb4b2fd5df2e26aa44fcaaa510254d67"},
      {"script.infinity.commandcenter/experience.py", "7c7ea57451894d3b1310235837c09ca715bc5754111ded0a0c028f1edff57dfc"},
      {"script.infinity.commandcenter/persistence_participant.py", "7658db0f21c20853f272f61832e720df02b2b4b9ebaeba83ca1c7ba8758e1b9b"},
      {"script.infinity.commandcenter/plugin.py", "57c300c96c9385222da35e3e3507749f5d1614be0911f8c5ec3402fe1fd3621a"},
      {"script.infinity.commandcenter/resume_hub.py", "93b9c6796dc364793e4bad8dd45e07d3c231dacd01303ca609687bacd9f8e696"},
      {"script.infinity.commandcenter/runtime_visibility.py", "11a985fc544fdb37c906f2575516b78c6141ed2b68e95b6c390d824f4386560a"},
      {"script.infinity.commandcenter/service.py", "a92dedcf1608c9881b0356b7fed9fce10c1c07524df8898f7d6d99df09a462a1"},
      {"script.infinity.commandcenter/skin_upgrade.py", "044aa0dc3e6d22f1cc585e503c482cb1d5ba58fb6734298449480ca02c53e1f8"},
      {"script.infinity.commandcenter/view_mode.py", "5f5583e9c36e32e970a0341ca353d32dd92e48d41079aaabaf7a113c66ddfc71"},
    }},
    {"script.infinity.commandcenter/plugin.py", "script.infinity.commandcenter", "command_center_client", {
      {"script.infinity.commandcenter/addon.xml", "23320bab6c3a1d661987ee30533dc7a8890ca67ed4ff87b2fc6e6014e2e5b69a"},
      {"script.infinity.commandcenter/checkpoint_runtime.py", "30fb11385186d9ee78c7c0485f0de7cd41ab2df52794f4ceda7cd0a7d724ce3b"},
      {"script.infinity.commandcenter/common.py", "0e2077a694a060bec1b37e70f59fbfd71ef7fd39f0b392838feacdd8155bd44e"},
      {"script.infinity.commandcenter/default.py", "fa6c1827385b2ed4e704775d10a23dc7bb4b2fd5df2e26aa44fcaaa510254d67"},
      {"script.infinity.commandcenter/experience.py", "7c7ea57451894d3b1310235837c09ca715bc5754111ded0a0c028f1edff57dfc"},
      {"script.infinity.commandcenter/persistence_participant.py", "7658db0f21c20853f272f61832e720df02b2b4b9ebaeba83ca1c7ba8758e1b9b"},
      {"script.infinity.commandcenter/plugin.py", "57c300c96c9385222da35e3e3507749f5d1614be0911f8c5ec3402fe1fd3621a"},
      {"script.infinity.commandcenter/resume_hub.py", "93b9c6796dc364793e4bad8dd45e07d3c231dacd01303ca609687bacd9f8e696"},
      {"script.infinity.commandcenter/runtime_visibility.py", "11a985fc544fdb37c906f2575516b78c6141ed2b68e95b6c390d824f4386560a"},
      {"script.infinity.commandcenter/service.py", "a92dedcf1608c9881b0356b7fed9fce10c1c07524df8898f7d6d99df09a462a1"},
      {"script.infinity.commandcenter/skin_upgrade.py", "044aa0dc3e6d22f1cc585e503c482cb1d5ba58fb6734298449480ca02c53e1f8"},
      {"script.infinity.commandcenter/view_mode.py", "5f5583e9c36e32e970a0341ca353d32dd92e48d41079aaabaf7a113c66ddfc71"},
    }},
    {"service.infinity.compat/runtime_service.py", "service.infinity.compat", "compat", {
      {"service.infinity.compat/addon.xml", "6105af7bbb1d179f32326c82c323c9b2a6d2f7935b4f82f91f06614041bb3720"},
      {"service.infinity.compat/checkpoint_runtime.py", "eb07f7cac8e773b5edc770d853618ca12a21c6279224fcfb04e23801c90077be"},
      {"service.infinity.compat/compat_runtime.py", "f70cc391f88a4ccad1327c7bea36378e5a615549da0ca31fc077347decff4878"},
      {"service.infinity.compat/layout_service.py", "227cf88d71febf61fe46b5dce5d8c131a31f0bfa11bc66d1bd4b02176582abdf"},
      {"service.infinity.compat/runtime_service.py", "657d75dee8f04d5cbdb1307893eed55efe05f32a1cefc0fa11c5213395080dca"},
      {"service.infinity.compat/theme_contract.py", "93320b9c0bfdb3ea87b1d76d2aae1a39bef715015977326a74740f3490410735"},
    }},
    {"service.infinity.compat/layout_service.py", "service.infinity.compat", "nonpersistent:layout-properties", {
      {"service.infinity.compat/layout_service.py", "227cf88d71febf61fe46b5dce5d8c131a31f0bfa11bc66d1bd4b02176582abdf"},
    }},
    {"service.infinity.compat/theme_contract.py", "service.infinity.compat", "reconstructible-cache:theme-revision", {
      {"service.infinity.compat/theme_contract.py", "93320b9c0bfdb3ea87b1d76d2aae1a39bef715015977326a74740f3490410735"},
    }},
  };
  return *contracts;
}
}

std::string ClassifyScript(const std::string& script, const std::string& addon)
{
  try
  {
    const std::string actual = CSpecialProtocol::TranslatePath(script);
    // Home RunScript has no add-on object. Only these reviewed skin sources and
    // the exact APK-owned native image implement this memory-only contract.
    // Same basenames, unknown source revisions and user-supplied libraries fail closed.
    if (addon.empty() || addon == "skin.infinity.diggz")
    {
      for (const char* root : {"special://home/addons/", "special://xbmc/addons/"})
      {
        const std::string ambient = std::string(root) +
            "skin.infinity.diggz/resources/lib/infinity_native_ambient.py";
        if (actual != CSpecialProtocol::TranslatePath(ambient))
          continue;
        const auto digest = CUtil::GetFileDigest(ambient, KODI::UTILITY::CDigest::Type::SHA256);
        const char* libraries = std::getenv("KODI_ANDROID_LIBS");
        if ((digest == "3e33144282d81aa727466f530fd3d37deaee8357c5973c0c7b932bbcc3db1f5f" ||
             digest == "de30a5114302a303638c589342024b348d3070c5aa76ba4a360d2506dd4402f7") &&
            libraries && libraries[0] == '/' &&
            CUtil::GetFileDigest(std::string(libraries) + "/libinfinityambient.so",
                                KODI::UTILITY::CDigest::Type::SHA256) ==
                "a876a76abe4faea63046953579899b0b7a67572722c2ed92331e41fcd1475684")
          return "nonpersistent:ambient-glass";
      }
    }
    for (const auto& contract : Contracts())
    {
      if (addon != contract.addon)
        continue;
      for (const char* root : {"special://home/addons/", "special://xbmc/addons/"})
      {
        if (actual != CSpecialProtocol::TranslatePath(std::string(root) + contract.script))
          continue;
        bool exact = true;
        for (const auto& pin : contract.source)
        {
          const auto digest = CUtil::GetFileDigest(std::string(root) + pin.first,
                                                  KODI::UTILITY::CDigest::Type::SHA256);
          if (digest != pin.second)
          {
            exact = false;
            break;
          }
        }
        if (exact)
          return contract.owner;
      }
    }
  }
  catch (...)
  {
    // A missing/unreadable/unsupported file never receives a clean classification.
  }
  return {};
}
} // namespace InfinityAndroidCheckpoint
