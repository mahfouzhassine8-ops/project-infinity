#include "InfinityModuleManifest.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <memory>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <sstream>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace InfinityModuleManifest
{
namespace
{
constexpr size_t MANIFEST_LIMIT = 128 * 1024;
constexpr size_t SOURCE_LIMIT = 4 * 1024 * 1024;
constexpr size_t TOTAL_LIMIT = 32 * 1024 * 1024;
constexpr size_t FILE_LIMIT = 256;
constexpr char MANIFEST[] = "script.infinity.commandcenter/INFINITY-MODULES.v1";

class Descriptor
{
public:
  explicit Descriptor(int value = -1) : m_value(value) {}
  ~Descriptor() { if (m_value >= 0) close(m_value); }
  Descriptor(const Descriptor&) = delete;
  Descriptor& operator=(const Descriptor&) = delete;
  int Get() const { return m_value; }
  void Replace(int value)
  {
    if (m_value >= 0) close(m_value);
    m_value = value;
  }
private:
  int m_value;
};

bool AllowedAddon(const std::string& id)
{
  return id == "script.infinity.commandcenter" || id == "script.infinity.uirepair" ||
         id == "script.infinity.watchedbridge" || id == "script.infinity.rails";
}

bool SafePath(const std::string& value)
{
  if (value.empty() || value.size() > 240 || value.front() == '/' || value.back() == '/')
    return false;
  std::string lower;
  for (unsigned char c : value)
  {
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
          (c >= '0' && c <= '9') || c == '/' || c == '.' || c == '_' || c == '-'))
      return false;
    lower.push_back(static_cast<char>(std::tolower(c)));
  }
  if (lower.find("cobra") != std::string::npos)
    return false;
  std::istringstream parts(value);
  std::string component;
  while (std::getline(parts, component, '/'))
    if (component.empty() || component == "." || component == "..")
      return false;
  const auto slash = value.find('/');
  return slash != std::string::npos && AllowedAddon(value.substr(0, slash));
}

bool SameFile(const struct stat& before, const struct stat& after)
{
  return before.st_dev == after.st_dev && before.st_ino == after.st_ino &&
         before.st_size == after.st_size && before.st_mtim.tv_sec == after.st_mtim.tv_sec &&
         before.st_mtim.tv_nsec == after.st_mtim.tv_nsec &&
         before.st_ctim.tv_sec == after.st_ctim.tv_sec &&
         before.st_ctim.tv_nsec == after.st_ctim.tv_nsec;
}

bool ReadAt(int root, const std::string& path, size_t limit, std::vector<unsigned char>& bytes)
{
  if (!SafePath(path)) return false;
  Descriptor directory(fcntl(root, F_DUPFD_CLOEXEC, 0));
  if (directory.Get() < 0) return false;
  std::istringstream parts(path);
  std::vector<std::string> names;
  std::string name;
  while (std::getline(parts, name, '/')) names.push_back(name);
  for (size_t i = 0; i + 1 < names.size(); ++i)
  {
    const int next = openat(directory.Get(), names[i].c_str(),
                            O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (next < 0) return false;
    directory.Replace(next);
  }
  Descriptor source(openat(directory.Get(), names.back().c_str(),
                           O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK));
  struct stat before{}, after{};
  if (source.Get() < 0 || fstat(source.Get(), &before) != 0 || !S_ISREG(before.st_mode) ||
      before.st_size < 0 || static_cast<unsigned long long>(before.st_size) > limit)
    return false;
  bytes.clear();
  bytes.reserve(static_cast<size_t>(before.st_size));
  std::array<unsigned char, 8192> buffer{};
  while (true)
  {
    const auto size = read(source.Get(), buffer.data(), buffer.size());
    if (size < 0 && errno == EINTR) continue;
    if (size < 0) return false;
    if (size == 0) break;
    if (bytes.size() + static_cast<size_t>(size) > limit) return false;
    bytes.insert(bytes.end(), buffer.begin(), buffer.begin() + size);
  }
  return fstat(source.Get(), &after) == 0 && SameFile(before, after) &&
         bytes.size() == static_cast<size_t>(before.st_size);
}

std::string Sha256(const std::vector<unsigned char>& bytes)
{
  std::array<unsigned char, EVP_MAX_MD_SIZE> digest{};
  unsigned int size = 0;
  if (EVP_Digest(bytes.data(), bytes.size(), digest.data(), &size, EVP_sha256(), nullptr) != 1 || size != 32)
    return {};
  static const char hex[] = "0123456789abcdef";
  std::string value;
  value.reserve(64);
  for (unsigned int i = 0; i < size; ++i)
  {
    value.push_back(hex[digest[i] >> 4]);
    value.push_back(hex[digest[i] & 15]);
  }
  return value;
}

bool Signature(const std::vector<unsigned char>& payload,
               const std::vector<unsigned char>& signature,
               const std::string& trustedPem)
{
  if (trustedPem.empty() || trustedPem.size() > 8192) return false;
  std::unique_ptr<BIO, decltype(&BIO_free)> bio(
      BIO_new_mem_buf(trustedPem.data(), static_cast<int>(trustedPem.size())), &BIO_free);
  if (!bio) return false;
  std::unique_ptr<EVP_PKEY, decltype(&EVP_PKEY_free)> key(
      PEM_read_bio_PUBKEY(bio.get(), nullptr, nullptr, nullptr), &EVP_PKEY_free);
  if (!key || EVP_PKEY_base_id(key.get()) != EVP_PKEY_RSA ||
      EVP_PKEY_bits(key.get()) < 2048 || EVP_PKEY_bits(key.get()) > 4096 ||
      signature.size() != static_cast<size_t>(EVP_PKEY_size(key.get())))
    return false;
  std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)> context(EVP_MD_CTX_new(), &EVP_MD_CTX_free);
  return context && EVP_DigestVerifyInit(context.get(), nullptr, EVP_sha256(), nullptr, key.get()) == 1 &&
         EVP_DigestVerifyUpdate(context.get(), payload.data(), payload.size()) == 1 &&
         EVP_DigestVerifyFinal(context.get(), signature.data(), signature.size()) == 1;
}

bool Version(const std::string& value)
{
  if (value.empty() || value.size() > 48 || value.front() == '.' || value.back() == '.') return false;
  bool digit = false;
  unsigned int parts = 0;
  for (char c : value)
  {
    if (c >= '0' && c <= '9') digit = true;
    else if (c == '.' && digit) { digit = false; ++parts; }
    else return false;
  }
  return digit && parts >= 2 && parts <= 3;
}

std::vector<std::string> Fields(const std::string& line)
{
  std::vector<std::string> result;
  std::istringstream source(line);
  std::string field;
  while (std::getline(source, field, '\t')) result.push_back(field);
  if (!line.empty() && line.back() == '\t') result.push_back("");
  return result;
}

bool Parse(const std::vector<unsigned char>& payload, Verified& result)
{
  if (payload.empty() || payload.back() != '\n') return false;
  for (unsigned char c : payload)
    if ((c < 32 && c != '\n' && c != '\t') || c >= 127) return false;
  const std::string data(payload.begin(), payload.end());
  std::istringstream lines(data);
  std::string line;
  if (!std::getline(lines, line) || line != "INFINITY-MODULES/1") return false;
  if (!std::getline(lines, line)) return false;
  auto fields = Fields(line);
  if (fields.size() != 2 || fields[0] != "package" || !Version(fields[1])) return false;
  result.packageVersion = fields[1];
  if (!std::getline(lines, line) || line != "protocol\t1") return false;
  result.protocolApi = PROTOCOL_API;
  int phase = 0;
  std::string previousCapability, previousFile, previousEntry;
  while (std::getline(lines, line))
  {
    if (line.empty() || line.size() > 512) return false;
    fields = Fields(line);
    if (fields.size() == 2 && fields[0] == "capability")
    {
      if (phase != 0 || fields[1] <= previousCapability ||
          (fields[1] != "checkpoint-v1" && fields[1] != "title-actions-v1" &&
           fields[1] != "dialog-reflow-v1" && fields[1] != "first-party-modules-v1")) return false;
      result.capabilities.insert(fields[1]);
      previousCapability = fields[1];
    }
    else if (fields.size() == 3 && fields[0] == "file")
    {
      if (phase > 1 || fields[2] <= previousFile || !SafePath(fields[2]) ||
          fields[1].size() != 64 || !std::all_of(fields[1].begin(), fields[1].end(),
              [](char c) { return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'); })) return false;
      phase = 1;
      result.files.emplace(fields[2], fields[1]);
      previousFile = fields[2];
      if (result.files.size() > FILE_LIMIT) return false;
    }
    else if (fields.size() == 3 && fields[0] == "entry")
    {
      if (phase < 1 || fields[2] <= previousEntry || !SafePath(fields[2]) ||
          result.files.count(fields[2]) != 1 ||
          (fields[1] != "command_center" && fields[1] != "command_center_client")) return false;
      phase = 2;
      if ((fields[1] == "command_center") != (fields[2] == "script.infinity.commandcenter/service.py")) return false;
      result.entries.emplace(fields[2], fields[1]);
      previousEntry = fields[2];
      if (result.entries.size() > 16) return false;
    }
    else return false;
  }
  for (const char* path : {"addon.xml", "checkpoint_runtime.py", "common.py", "context.py", "default.py",
                           "module_contract.py", "persistence_participant.py", "plugin.py", "service.py"})
    if (result.files.count(std::string("script.infinity.commandcenter/") + path) != 1) return false;
  return result.capabilities.count("checkpoint-v1") == 1 &&
         result.capabilities.count("first-party-modules-v1") == 1 &&
         result.entries.count("script.infinity.commandcenter/service.py") == 1;
}
} // namespace

bool Verify(const std::string& addonsRoot, const std::string& trustedPublicKeyPem,
            Verified& result, std::string& failure)
{
  result = {};
  failure = "unavailable";
  if (addonsRoot.empty() || addonsRoot.front() != '/') return false;
  Descriptor root(open(addonsRoot.c_str(), O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC));
  std::vector<unsigned char> payload, signature;
  if (root.Get() < 0 || !ReadAt(root.Get(), MANIFEST, MANIFEST_LIMIT, payload) ||
      !ReadAt(root.Get(), std::string(MANIFEST) + ".sig", 512, signature)) return false;
  failure = "signature_rejected";
  if (!Signature(payload, signature, trustedPublicKeyPem)) return false;
  Verified candidate;
  failure = "contract_rejected";
  if (!Parse(payload, candidate)) return false;
  candidate.manifestSha256 = Sha256(payload);
  if (candidate.manifestSha256.size() != 64) return false;
  failure = "source_rejected";
  size_t total = 0;
  for (const auto& file : candidate.files)
  {
    std::vector<unsigned char> bytes;
    if (!ReadAt(root.Get(), file.first, SOURCE_LIMIT, bytes) ||
        bytes.size() > TOTAL_LIMIT - total || Sha256(bytes) != file.second) return false;
    total += bytes.size();
  }
  // Re-read the signed pair after source validation. Never publish a mixed
  // bundle if a coherent Command Center update replaced its manifest meanwhile.
  std::vector<unsigned char> finalPayload, finalSignature;
  if (!ReadAt(root.Get(), MANIFEST, MANIFEST_LIMIT, finalPayload) ||
      !ReadAt(root.Get(), std::string(MANIFEST) + ".sig", 512, finalSignature) ||
      payload != finalPayload || signature != finalSignature) return false;
  result = std::move(candidate);
  failure.clear();
  return true;
}

std::string EntryOwner(const Verified& bundle, const std::string& relativeScript, const std::string& addonId)
{
  if (!SafePath(relativeScript) || !AllowedAddon(addonId) ||
      relativeScript.compare(0, addonId.size() + 1, addonId + "/") != 0) return {};
  const auto entry = bundle.entries.find(relativeScript);
  return entry == bundle.entries.end() ? std::string{} : entry->second;
}
} // namespace InfinityModuleManifest
