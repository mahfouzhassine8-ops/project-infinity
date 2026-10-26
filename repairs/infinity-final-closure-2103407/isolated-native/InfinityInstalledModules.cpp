#include "InfinityInstalledModules.h"
#include "InfinityModuleManifest.h"

#include "filesystem/SpecialProtocol.h"

#include <array>
#include <cstring>
#include <map>
#include <mutex>
#include <sys/stat.h>

namespace
{
const char* const CC = "script.infinity.commandcenter";

// Extracted from the verified signed407 certificate. Certificate SHA256:
// d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7.
// Only this immutable key is used in production; never load trust from profile.
const char PUBLIC_KEY[] = R"INFINITY_KEY(-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA3L9A6UT4BZ1iaSNqnEAr
XCH1kPhFDnwbzJZHOumV60X6+GKjfX5WHPcRQVNxdNhW7eWaISZXNKv/ioZ0JMam
rzobr6j0iZMH6kMp8d/C6DEpTSWWLQhavHApMlfIe4G/fcuAsZLwBjonROFW1cVA
prHwFMVpxSxfM8pvk/gtopYEA/+/pzcjj8UjStnRBpaqsXeubGO1BDJ5ctv1z9fz
rusW2mIu2la+IY72RDJMwUYT92CnXldS8OH7ar7JdaTwchaNKpm1QvCmoF/52pKM
ScaKciJTI28I3N/Eks4AgUCoDfBLFMNlrfiBdYuUQkekSkMr+Sd0TYwqqHxYvxDL
N24q8UIAOVw+FSv2BbAeyQtIJ9LavORhM8DAeuZexHYqxyn0imoWZEO0azRFTA+z
jYUPCl8Fwf1FUY0dGUjM/qJff1chGHz5KXAzx8o9i222JL2W8l68ikXc1x1uPz5z
G0RZfVLDEODv2SrWWjBI2yCoitfYoE3QW9RdBsa1mv0v/PMHK68ZYI3IhFA3ok2x
f9z/u9SO+aEEGm81SjrWCTp072FKVGba7JWdrrJv0SVVMu7HZeoE3aXC6MvlLYEv
zDnLp2/qmUUHPNAiwiapSSyzPrl3k0mQfzHJ7rIgMVqddFD96tefJSXHBATfMlAE
3j2duWW3YMrCjXi1VU2Yb70CAwEAAQ==
-----END PUBLIC KEY-----
)INFINITY_KEY";

struct Stamp
{
  dev_t device{};
  ino_t inode{};
  off_t size{};
  timespec modified{};
  timespec changed{};
};

bool ReadStamp(const std::string& path, Stamp& result)
{
  struct stat value{};
  if (lstat(path.c_str(), &value) != 0 || !S_ISREG(value.st_mode)) return false;
  result = {value.st_dev, value.st_ino, value.st_size, value.st_mtim, value.st_ctim};
  return true;
}

bool Same(const Stamp& a, const Stamp& b)
{
  return a.device == b.device && a.inode == b.inode && a.size == b.size &&
         a.modified.tv_sec == b.modified.tv_sec && a.modified.tv_nsec == b.modified.tv_nsec &&
         a.changed.tv_sec == b.changed.tv_sec && a.changed.tv_nsec == b.changed.tv_nsec;
}

bool OwnedAddon(const std::string& addon)
{
  return addon == CC || addon == "script.infinity.uirepair" ||
         addon == "script.infinity.watchedbridge" || addon == "script.infinity.rails";
}

std::string WithoutSlash(std::string path)
{
  if (!path.empty() && path.back() == '/') path.pop_back();
  return path;
}

std::array<std::string, 2> Roots()
{
  return {{WithoutSlash(CSpecialProtocol::TranslatePath("special://home/addons/")),
           WithoutSlash(CSpecialProtocol::TranslatePath("special://xbmc/addons/"))}};
}

struct Cached
{
  InfinityModuleManifest::Verified bundle;
  Stamp payload, signature;
};
std::mutex g_mutex;
std::map<std::string, Cached> g_cache;

bool VerifyRoot(const std::string& root, InfinityModuleManifest::Verified& bundle)
{
  const std::string base = root + "/" + CC + "/INFINITY-MODULES.v1";
  Stamp beforePayload, beforeSignature, afterPayload, afterSignature;
  std::string failure;
  const bool valid = ReadStamp(base, beforePayload) && ReadStamp(base + ".sig", beforeSignature) &&
      InfinityModuleManifest::Verify(root, PUBLIC_KEY, bundle, failure) &&
      ReadStamp(base, afterPayload) && ReadStamp(base + ".sig", afterSignature) &&
      Same(beforePayload, afterPayload) && Same(beforeSignature, afterSignature);
  std::lock_guard<std::mutex> lock(g_mutex);
  if (!valid)
  {
    g_cache.erase(root);
    bundle = {};
    return false;
  }
  // There are only two native-resolved roots; callers cannot grow this map.
  g_cache[root] = {bundle, afterPayload, afterSignature};
  return true;
}
} // namespace

namespace InfinityInstalledModules
{
std::string Classify(const std::string& absoluteScript, const std::string& addonId)
{
  if (!OwnedAddon(addonId)) return {};
  try
  {
    for (const auto& root : Roots())
    {
      const std::string prefix = root + "/" + addonId + "/";
      if (absoluteScript.compare(0, prefix.size(), prefix) != 0) continue;
      InfinityModuleManifest::Verified bundle;
      if (!VerifyRoot(root, bundle)) continue;
      const auto owner = InfinityModuleManifest::EntryOwner(bundle,
          absoluteScript.substr(root.size() + 1), addonId);
      if (!owner.empty()) return owner;
    }
  }
  catch (...) { return {}; }
  return {};
}

bool Participant(const std::string& packageVersion, unsigned int protocolApi,
                 const std::string& manifestSha256)
{
  if (protocolApi != InfinityModuleManifest::PROTOCOL_API || manifestSha256.size() != 64)
    return false;
  try
  {
    for (const auto& root : Roots())
    {
      InfinityModuleManifest::Verified bundle;
      if (VerifyRoot(root, bundle) && bundle.packageVersion == packageVersion &&
          bundle.protocolApi == protocolApi && bundle.manifestSha256 == manifestSha256 &&
          bundle.capabilities.count("checkpoint-v1") == 1 &&
          InfinityModuleManifest::EntryOwner(bundle, std::string(CC) + "/service.py", CC) == "command_center")
        return true;
    }
  }
  catch (...) { return false; }
  return false;
}

bool CapabilityReady(const std::string& addonId, const std::string& addonRoot,
                     const std::string& capability)
{
  if (!OwnedAddon(addonId) || (capability != "title-actions-v1" && capability != "dialog-reflow-v1"))
    return false;
  try
  {
    const auto requested = WithoutSlash(addonRoot);
    for (const auto& root : Roots())
    {
      if (requested != root + "/" + addonId) continue;
      // Do not hash a bundle or wait for a worker on the GUI thread. These two
      // stamps invalidate an updated manifest; Classify always revalidates all
      // actual source bytes before any corresponding script is admitted.
      Stamp payload, signature;
      const auto base = root + "/" + CC + "/INFINITY-MODULES.v1";
      if (!ReadStamp(base, payload) || !ReadStamp(base + ".sig", signature)) return false;
      std::lock_guard<std::mutex> lock(g_mutex);
      const auto cached = g_cache.find(root);
      if (cached == g_cache.end() || cached->second.bundle.files.count(addonId + "/addon.xml") != 1)
        return false;
      bool signedEntry = false;
      for (const auto& entry : cached->second.bundle.entries)
        if (entry.first.compare(0, addonId.size() + 1, addonId + "/") == 0)
          signedEntry = true;
      return signedEntry && Same(payload, cached->second.payload) &&
             Same(signature, cached->second.signature) &&
             cached->second.bundle.capabilities.count(capability) == 1;
    }
  }
  catch (...) { return false; }
  return false;
}
} // namespace InfinityInstalledModules

extern "C" int InfinityCommandCenterIdentityV1(const char* commandCenterRoot,
    char* packageVersion, size_t versionCapacity, char* manifestSha256, size_t hashCapacity,
    unsigned int* protocolApi)
{
  if (!commandCenterRoot || !packageVersion || versionCapacity < 49 ||
      !manifestSha256 || hashCapacity < 65 || !protocolApi) return 0;
  if (strnlen(commandCenterRoot, 4097) > 4096) return 0;
  packageVersion[0] = manifestSha256[0] = '\0';
  *protocolApi = 0;
  try
  {
    const std::string requested = WithoutSlash(commandCenterRoot);
    for (const auto& root : Roots())
    {
      if (requested != root + "/" + CC) continue;
      InfinityModuleManifest::Verified bundle;
      if (!VerifyRoot(root, bundle)) return 0;
      if (bundle.packageVersion.size() >= versionCapacity || bundle.manifestSha256.size() >= hashCapacity)
        return 0;
      std::memcpy(packageVersion, bundle.packageVersion.c_str(), bundle.packageVersion.size() + 1);
      std::memcpy(manifestSha256, bundle.manifestSha256.c_str(), bundle.manifestSha256.size() + 1);
      *protocolApi = bundle.protocolApi;
      return 1;
    }
  }
  catch (...) { return 0; }
  return 0;
}
