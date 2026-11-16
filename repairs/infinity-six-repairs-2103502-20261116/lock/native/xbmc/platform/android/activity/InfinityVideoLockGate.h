#pragma once

#include <atomic>
#include <cstdint>
#include <limits>

namespace InfinityVideoLock
{
// One atomic word is the sole native input authority. High32 binds the playback
// lock session; low32 is a never-reused generation and its grant bit. A revoke or
// new request changes the entire word. Commit cannot clear a newer generation.
class Gate
{
public:
  using Word = std::uint64_t;
  static constexpr std::uint32_t MAX_SESSION = 0x7fffffff;
  static constexpr std::uint32_t MAX_GENERATION = 0x7fffffff;
  static_assert(std::atomic<Word>::is_always_lock_free, "ARM64 lock requires lock-free word CAS");

  Word Value() const { return m_word.load(std::memory_order_acquire); }
  static std::uint32_t Session(Word value) { return static_cast<std::uint32_t>(value >> 32); }

  // Only Kodi's process thread issues session/generation values.
  bool Begin(std::uint32_t session, std::uint32_t initialGeneration = 1)
  {
    if (!session || session > MAX_SESSION || !initialGeneration ||
        initialGeneration > MAX_GENERATION || Value())
      return false;
    m_word.store(Pack(session, initialGeneration, false), std::memory_order_release);
    return true;
  }

  Word Advance(std::uint32_t session, bool grant)
  {
    Word previous = Value();
    while (Session(previous) == session && previous)
    {
      const auto generation = static_cast<std::uint32_t>(previous) >> 1;
      if (generation == MAX_GENERATION)
      {
        // Keep the barrier, but invalidate any last grant. Never wrap.
        const Word exhausted = previous & ~Word{1};
        if (m_word.compare_exchange_weak(previous, exhausted, std::memory_order_acq_rel))
          return 0;
        continue;
      }
      const Word next = Pack(session, generation + 1, grant);
      if (m_word.compare_exchange_weak(previous, next, std::memory_order_acq_rel))
        return next;
    }
    return 0; // Already committed or belongs to a different lock.
  }

  // JNI's final commit performs only this CAS. No GUI, callback, allocation or wait.
  bool Commit(std::uint32_t session, Word grant)
  {
    if (!session || Session(grant) != session || !(grant & 1))
      return false;
    return m_word.compare_exchange_strong(grant, 0, std::memory_order_acq_rel);
  }

  bool Retire(std::uint32_t session)
  {
    Word value = Value();
    while (value && Session(value) == session)
      if (m_word.compare_exchange_weak(value, 0, std::memory_order_acq_rel))
        return true;
    return false;
  }

private:
  static constexpr Word Pack(std::uint32_t session, std::uint32_t generation, bool grant)
  {
    return (Word{session} << 32) | (Word{generation} << 1) | (grant ? 1 : 0);
  }
  std::atomic<Word> m_word{0};
};
} // namespace InfinityVideoLock
