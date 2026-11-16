/*
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#pragma once

#include <condition_variable>
#include <cstdint>
#include <mutex>
#include <utility>

namespace
{
// Private to the JNI implementation. The factory retains exclusive ownership;
// these leases only keep that owner alive while an Infinity observer is running.
template<class Owner>
class InfinityActivityObserver
{
public:
  class Lease
  {
  public:
    Lease() = default;
    Lease(const Lease&) = delete;
    Lease& operator=(const Lease&) = delete;
    Lease& operator=(Lease&&) = delete;
    Lease(Lease&& other) noexcept
      : m_gate(std::exchange(other.m_gate, nullptr)), m_owner(other.m_owner)
    {
    }
    ~Lease()
    {
      if (m_gate)
        m_gate->Release();
    }
    Owner* Get() const { return m_owner; }
    explicit operator bool() const { return m_gate != nullptr; }
    Owner* operator->() const { return m_owner; }

  private:
    friend class InfinityActivityObserver;
    Lease(InfinityActivityObserver* gate, Owner* owner) : m_gate(gate), m_owner(owner) {}
    InfinityActivityObserver* m_gate{nullptr};
    Owner* m_owner{nullptr};
  };

  bool Publish(Owner* owner)
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (!owner || m_owner || m_retiring)
      return false;
    m_owner = owner;
    ++m_generation;
    return true;
  }

  Lease Acquire()
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (!m_owner || m_retiring)
      return {};
    ++m_readers;
    return Lease(this, m_owner);
  }

  // Called only by the native factory, before reset/delete, never by an observer
  // or a destructor. New observer calls fail immediately while readers drain.
  void Retire(Owner* expected)
  {
    std::unique_lock<std::mutex> lock(m_mutex);
    if (!expected || m_owner != expected)
      return;
    const auto generation = m_generation;
    m_retiring = true;
    m_drained.wait(lock, [this, generation] {
      return m_readers == 0 || m_generation != generation;
    });
    if (m_owner == expected && m_generation == generation)
    {
      m_owner = nullptr;
      m_retiring = false;
    }
  }

private:
  void Release()
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (--m_readers == 0)
      m_drained.notify_all();
  }

  std::mutex m_mutex;
  std::condition_variable m_drained;
  Owner* m_owner{nullptr};
  std::size_t m_readers{0};
  std::uint64_t m_generation{0};
  bool m_retiring{false};
};
} // namespace
