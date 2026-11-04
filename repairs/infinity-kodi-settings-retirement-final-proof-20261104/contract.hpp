#pragma once
// ISOLATED PROTOCOL PROTOTYPE. Not native Kodi code and not a production patch.
// Numeric synthetic payloads; real mutex/shared ownership, simulated write receipts.
#include <atomic>
#include <cstdint>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace retirement_proof {
class Registry;
struct Object {
  const uint64_t id;
  std::function<void()> onDestroy;
  explicit Object(uint64_t n):id(n){}
  ~Object(){if(onDestroy)onDestroy();}
private:
  friend class Registry;
  std::mutex mutationGate;
  int value{0};
  int defaultValue{0};
  std::map<int,int> items;
};
using Owner=std::shared_ptr<Object>;
enum class Coverage { Unknown, CertifiedSynthetic };
struct Snapshot {
  uint64_t token,owner,revision;
  int value;
  int defaultValue;
  std::map<int,int> items;
  bool operator==(const Snapshot& b)const{return token==b.token&&owner==b.owner&&revision==b.revision&&value==b.value&&defaultValue==b.defaultValue&&items==b.items;}
};
struct Pending {
  Snapshot snapshot;
  uint64_t sequence{0};
  bool confirmed{false};
  bool requiresDurability{true};
};
struct Path {
  std::mutex gate;
  uint64_t activeToken{0},sequence{0};
  bool unresolvedFailure{false};
  int simulatedDisk{0};
  std::optional<Pending> pending;
};
struct Token {
  Registry* registry;
  const uint64_t id;
  Owner owner;
  std::shared_ptr<Path> path;
  std::unique_lock<std::mutex> lease;
  std::optional<Snapshot> snapshot;
  bool wrote{false},closed{false};
  Token(Registry* r,uint64_t n,Owner o,std::shared_ptr<Path> p,std::unique_lock<std::mutex> l)
    :registry(r),id(n),owner(std::move(o)),path(std::move(p)),lease(std::move(l)){}
  ~Token();
  Token(const Token&)=delete;
};
class Registry {
  struct Entry {
    std::weak_ptr<Object> weak;
    Owner pin;
    std::shared_ptr<Path> path;
    uint64_t revision{0},confirmedRevision{0},sequence{0},activeSave{0};
    unsigned mutations{0};
    bool failed{false};
    Coverage coverage{Coverage::Unknown};
  };
  mutable std::mutex mutex;
  std::atomic<bool> locked{false};
  std::map<uint64_t,Entry> entries;
  std::map<std::string,std::shared_ptr<Path>> paths;
  uint64_t nextOwner{0},nextToken{0};
  struct Guard {
    Registry& registry;
    std::unique_lock<std::mutex> lease;
    explicit Guard(Registry& r):registry(r),lease(r.mutex){r.locked=true;}
    ~Guard(){registry.locked=false;}
  };
  Entry& entry(const Owner& o){auto& e=entries.at(o->id);if(e.weak.lock()!=o)throw std::logic_error("foreign owner");return e;}
  bool active(const Token& t){return !t.closed&&t.lease.owns_lock()&&t.path->activeToken==t.id&&entry(t.owner).activeSave==t.id;}
  void closeLocked(Token& t,bool failure){auto& e=entry(t.owner);if(failure){e.failed=true;t.path->unresolvedFailure=true;}e.activeSave=0;t.path->activeToken=0;t.closed=true;}
public:
  Owner Create(const std::string& path,Coverage coverage=Coverage::Unknown){
    Guard guard(*this);
    auto& p=paths[path];if(!p)p=std::make_shared<Path>();
    auto o=std::make_shared<Object>(++nextOwner);
    Entry e;e.weak=o;e.path=p;e.coverage=coverage;entries.emplace(o->id,std::move(e));return o;
  }
  void MutateState(const Owner& o,const std::function<void(Object&)>& change){
    std::unique_lock<std::mutex> ownerLock(o->mutationGate);
    {
      Guard guard(*this);auto& e=entry(o);e.pin=o;++e.mutations;
      if(e.revision==std::numeric_limits<uint64_t>::max()){e.coverage=Coverage::Unknown;e.failed=true;}
      else ++e.revision;
    }
    try {change(*o);}catch(...){Guard guard(*this);auto& e=entry(o);--e.mutations;e.failed=true;throw;}
    Guard guard(*this);--entry(o).mutations;
  }
  void Mutate(const Owner& o,const std::function<void(int&)>& change){MutateState(o,[&](Object& state){change(state.value);});}
  void Default(const Owner& o,int value){MutateState(o,[=](Object& state){state.defaultValue=value;});}
  void Insert(const Owner& o,int key,int value){MutateState(o,[=](Object& state){state.items[key]=value;});}
  void Erase(const Owner& o,int key){MutateState(o,[=](Object& state){state.items.erase(key);});}
  int Read(const Owner& o){std::lock_guard<std::mutex> lock(o->mutationGate);return o->value;}
  std::unique_ptr<Token> TryBegin(const Owner& o){
    std::shared_ptr<Path> p;
    {Guard guard(*this);p=entry(o).path;}
    // A failed lease is explicit deferral, never a completed/dropped native request.
    std::unique_lock<std::mutex> lease(p->gate,std::try_to_lock);
    if(!lease)return {};
    Guard guard(*this);auto& e=entry(o);
    if(nextToken==std::numeric_limits<uint64_t>::max()){e.failed=true;return {};}
    const auto id=++nextToken;e.activeSave=id;e.pin=o;p->activeToken=id;
    return std::make_unique<Token>(this,id,o,p,std::move(lease));
  }
  Snapshot Capture(Token& t){
    std::unique_lock<std::mutex> ownerLock(t.owner->mutationGate);
    Guard guard(*this);if(!active(t)||t.snapshot)throw std::logic_error("invalid capture");
    const auto& e=entry(t.owner);if(e.mutations)throw std::logic_error("active mutation");
    Snapshot s{t.id,t.owner->id,e.revision,t.owner->value,t.owner->defaultValue,t.owner->items};t.snapshot=s;
    t.path->pending=Pending{s};return s;
  }
  bool Write(Token& t,const Snapshot& s,bool ioSuccess=true){
    Guard guard(*this);
    if(!active(t)||!t.snapshot||!(*t.snapshot==s))return false;
    if(!ioSuccess){entry(t.owner).failed=true;t.path->unresolvedFailure=true;return false;}
    t.path->simulatedDisk=s.value;t.wrote=true;return true;
  }
  bool Confirm(Token& t,const Snapshot& s){
    bool success=false;
    {
      Guard guard(*this);
      if(!active(t)||!t.snapshot||!(*t.snapshot==s))return false;
      auto& e=entry(t.owner);
      success=t.wrote&&!e.mutations&&e.revision==s.revision&&t.path->sequence!=std::numeric_limits<uint64_t>::max();
      if(success){
        const auto sequence=++t.path->sequence;e.confirmedRevision=s.revision;e.sequence=sequence;
        t.path->pending=Pending{s,sequence,true,true};
      }
      closeLocked(t,!success);
    }
    t.lease.unlock();return success;
  }
  void Abandon(Token& t){
    {Guard guard(*this);if(!t.closed&&active(t))closeLocked(t,true);}
    if(t.lease.owns_lock())t.lease.unlock();
    // Token's owner is destroyed after the body, outside registry/path locks.
  }
  size_t Retire(const std::function<void(std::weak_ptr<Object>)>& testWeakAcquire={}){
    std::vector<Owner> releaseOutside;
    {
      Guard guard(*this);
      for(auto& item:entries){auto& e=item.second;auto& p=*e.path;
        if(!e.pin||e.pin.use_count()!=1||e.coverage!=Coverage::CertifiedSynthetic||e.failed||e.mutations||e.activeSave||
           e.sequence==0||e.revision!=e.confirmedRevision||p.activeToken||p.unresolvedFailure||!p.pending||
           !p.pending->confirmed||!p.pending->requiresDurability||p.pending->snapshot.owner==item.first||p.pending->sequence<=e.sequence)
          continue;
        // Test-only acquisition seam proves a still-live weak registration is not erased.
        if(testWeakAcquire)testWeakAcquire(e.weak);
        releaseOutside.push_back(std::move(e.pin));
      }
    }
    const auto n=releaseOutside.size();releaseOutside.clear();return n;
  }
  bool Pinned(uint64_t id){Guard guard(*this);return bool(entries.at(id).pin);}
  uint64_t Revision(uint64_t id){Guard guard(*this);return entries.at(id).revision;}
  uint64_t Confirmed(uint64_t id){Guard guard(*this);return entries.at(id).confirmedRevision;}
  Pending Receipt(const std::string& p){Guard guard(*this);return paths.at(p)->pending.value();}
  int Disk(const std::string& p){Guard guard(*this);return paths.at(p)->simulatedDisk;}
  size_t Count(){Guard guard(*this);return entries.size();}
  bool LockedForTest()const{return locked.load();}
  void DurabilityFailed(const std::string& p){Guard guard(*this);paths.at(p)->unresolvedFailure=true;}
  void DropReceiptForTest(const std::string& p){Guard guard(*this);paths.at(p)->pending.reset();}
  void RevisionAtLimitForTest(uint64_t id){Guard guard(*this);entries.at(id).revision=std::numeric_limits<uint64_t>::max();}
};
inline Token::~Token(){if(registry)registry->Abandon(*this);}
} // namespace retirement_proof
