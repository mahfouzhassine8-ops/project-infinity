#pragma once

// UI result correlation only. This state never grants persistence admission,
// finishes a writer, certifies durability or changes a provider's result.
#include <chrono>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

namespace InfinitySavedNavigation
{
struct Ticket
{
  std::string token, key, originalPath, path, reason, bucket;
  std::vector<std::string> attempted;
  double resume{0.0};
  bool folder{false}, cancelled{false}, failed{false}, recovering{false}, succeeded{false};
  std::chrono::steady_clock::time_point created;
};

class Correlation
{
public:
  void Begin(Ticket ticket)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    ticket.created = std::chrono::steady_clock::now();
    m_current = std::move(ticket);
  }
  std::optional<Ticket> Read()
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    Expire();
    return m_current;
  }
  bool Next(const std::string& token, const std::string& path, const std::string& provider)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    Expire();
    if (!m_current || m_current->token != token || !m_current->failed ||
        m_current->attempted.size() >= 8 || path == m_current->path)
      return false;
    for (const auto& previous : m_current->attempted)
      if (previous == provider) return false;
    m_current->path = path;
    m_current->attempted.push_back(provider);
    m_current->cancelled = false;
    m_current->failed = false;
    m_current->reason.clear();
    m_current->recovering = true;
    return true;
  }
  void Cancelled(const std::string& token)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_current && m_current->token == token) m_current->cancelled = true;
  }
  std::optional<Ticket> Finish(const std::string& token, const std::string& path,
                               bool success, const char* reason)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    Expire();
    if (!m_current || m_current->token != token || m_current->path != path || m_current->failed)
      return {};
    if (success || m_current->cancelled)
    {
      auto finished = m_current;
      m_current.reset();
      if (success && !finished->cancelled && finished->recovering)
      {
        finished->succeeded = true;
        return finished;
      }
      return {};
    }
    m_current->failed = true;
    m_current->reason = reason;
    return m_current;
  }
  void Clear(const std::string& token)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_current && m_current->token == token) m_current.reset();
  }
private:
  void Expire()
  {
    if (m_current && std::chrono::steady_clock::now() - m_current->created > std::chrono::minutes(5))
      m_current.reset();
  }
  std::mutex m_mutex;
  std::optional<Ticket> m_current;
};
} // namespace InfinitySavedNavigation
