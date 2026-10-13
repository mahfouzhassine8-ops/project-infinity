#pragma once
// Included after Python.h. Only exact loaded entry bytes receive this repair.
#include "utils/Digest.h"
#include <cstdio>
#include <string>
#include <utility>

namespace InfinityServiceStartupWait
{
struct Contract
{
  const char* addon;
  const char* digest;
  const char* indent;
  const char* continuation;
};
inline constexpr Contract CONTRACTS[] = {
  {"plugin.video.pov", "afcef67ec3552bf1aea81fa40825801dd8726f6ac9ec3c940fded868add215ce", "\t\t\t", "\t__import__('entry').SettingsMonitor()()"},
  {"plugin.video.redlight", "fbb605fa8d891f73d511b4da85e01bf87abd55e8188267a5d7996a0a8c75a1d8", "\t\t\t", nullptr},
  {"plugin.video.thecrew", "dd19417bfef7c5918efa59e671e6b17812dd019970ae6a21fcd8ad5185b7a238", "        ", "_crew_addon = xbmcaddon.Addon('script.module.thecrew')"},
  {"plugin.video.themoviedb.helper", "b7d4398ed66a748a87bd0658529c046f03b72a740ce820205815a243dac3c1c9", "            ", "    ServiceMonitor().run()"}
};
inline const Contract* Find(const std::string& addon)
{
  for (const auto& contract : CONTRACTS)
    if (addon == contract.addon)
      return &contract;
  return nullptr;
}
inline bool ReplaceOnce(std::string& value, const std::string& before,
                        const std::string& after)
{
  const auto position = value.find(before);
  if (position == std::string::npos || value.find(before, position + before.size()) != std::string::npos)
    return false;
  value.replace(position, before.size(), after);
  return true;
}
inline bool Transform(const std::string& addon, const std::string& input, std::string& output)
{
  const auto* contract = Find(addon);
  if (!contract || KODI::UTILITY::CDigest::Calculate(
      KODI::UTILITY::CDigest::Type::SHA256, input) != contract->digest)
    return false;
  const std::string newline = input.find("\r\n") == std::string::npos ? "\n" : "\r\n";
  const std::string indent = contract->indent;
  std::string candidate = input;
  if (!ReplaceOnce(candidate, "while waited < timeout:",
      "while waited < timeout and not __import__('xbmc').Monitor().abortRequested():"))
    return false;
  // This exact function only reads readiness settings and waits. Its original
  // False outcome already handles an unavailable Account Manager. The rest of
  // each add-on, pending writes, observer and interpreter retirement stay owned.
  if (!ReplaceOnce(candidate, indent + "xbmc.sleep(1000)",
      indent + "if __import__('xbmc').Monitor().waitForAbort(1):" + newline +
      indent + (indent[0] == '\t' ? "\t" : "    ") + "return False"))
    return false;
  if (contract->continuation)
  {
    const std::string marker = contract->continuation;
    const auto begin = candidate.find(marker);
    if (begin == std::string::npos || candidate.find(marker, begin + marker.size()) != std::string::npos)
      return false;
    const std::string outerIndent = addon == "plugin.video.thecrew" ? "" :
      addon == "plugin.video.pov" ? "\t" : "    ";
    const std::string extraIndent = addon == "plugin.video.pov" ? "\t" : "    ";
    const std::string tail = candidate.substr(begin);
    std::string guarded = outerIndent + "if not __import__('xbmc').Monitor().abortRequested():" + newline;
    std::size_t position = 0;
    while (position < tail.size())
    {
      auto end = tail.find(newline, position);
      if (end == std::string::npos) end = tail.size();
      guarded += extraIndent + tail.substr(position, end - position);
      if (end < tail.size()) guarded += newline;
      position = end + newline.size();
    }
    candidate.replace(begin, candidate.size() - begin, guarded);
  }
  output = std::move(candidate);
  return true;
}
inline bool TryExecute(FILE* file, const std::string& script, const std::string& addon,
                       PyObject* globals)
{
  if (!Find(addon)) return false;
  // ftell/fseek are available in the pinned API 21 Bionic configuration;
  // fgetpos/fsetpos are not declared there with its large-file build flags.
  const long position = ::ftell(file);
  if (position < 0) return false;
  std::string source;
  char buffer[4096];
  while (source.size() <= 65536)
  {
    const auto count = ::fread(buffer, 1, sizeof(buffer), file);
    source.append(buffer, count);
    if (count < sizeof(buffer)) break;
  }
  const bool readError = ::ferror(file) != 0;
  ::clearerr(file);
  if (::fseek(file, position, SEEK_SET) != 0)
  {
    // This stream cannot safely resume the original loader. Report a real
    // Python failure; never execute a partially consumed script or waive data.
    ::fclose(file);
    PyErr_SetFromErrno(PyExc_OSError);
    return true;
  }
  if (readError || source.size() > 65536 || source.find('\0') != std::string::npos)
    return false;
  std::string patched;
  if (!Transform(addon, source, patched)) return false;
  ::fclose(file);
  PyObject* code = Py_CompileString(patched.c_str(), script.c_str(), Py_file_input);
  if (!code) return true;
  PyObject* result = PyEval_EvalCode(code, globals, globals);
  Py_XDECREF(result);
  Py_DECREF(code);
  return true;
}
} // namespace InfinityServiceStartupWait
