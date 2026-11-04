#include "contract.hpp"
#include <iostream>
#include <thread>
using namespace retirement_proof;
#define CHECK(x) do{if(!(x))throw std::runtime_error("assertion at line "+std::to_string(__LINE__)+": " #x);}while(false)
Owner Make(Registry& r,const std::string& path="synthetic-path",Coverage c=Coverage::CertifiedSynthetic){return r.Create(path,c);}
void Value(Registry& r,const Owner& o,int value){r.Mutate(o,[=](int& v){v=value;});}
bool Save(Registry& r,const Owner& o){auto t=r.TryBegin(o);CHECK(t);auto s=r.Capture(*t);CHECK(r.Write(*t,s));return r.Confirm(*t,s);}

void Run(const std::string& name){
  Registry r;
  if(name=="snapshot_bound_confirmation"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));
    CHECK(r.Confirmed(a->id)==r.Revision(a->id)&&r.Disk("synthetic-path")==1);
    CHECK(r.Receipt("synthetic-path").requiresDurability); // no durable-save acknowledgement
  }else if(name=="stale_confirmation_rejected"){
    auto a=Make(r);Value(r,a,1);auto t=r.TryBegin(a);auto s=r.Capture(*t);CHECK(r.Write(*t,s));
    Value(r,a,2);CHECK(!r.Confirm(*t,s));CHECK(r.Confirmed(a->id)==0&&r.Read(a)==2);
    const auto id=a->id;t.reset();a.reset();auto b=Make(r);Value(r,b,3);CHECK(Save(r,b));
    CHECK(r.Retire()==0&&r.Pinned(id));
  }else if(name=="mutation_before_capture"){
    auto a=Make(r);Value(r,a,1);auto t=r.TryBegin(a);Value(r,a,2);auto s=r.Capture(*t);
    CHECK(s.revision==r.Revision(a->id)&&s.value==2);CHECK(r.Write(*t,s)&&r.Confirm(*t,s));
  }else if(name=="duplicate_confirmation_rejected"){
    auto a=Make(r);Value(r,a,1);auto t=r.TryBegin(a);auto s=r.Capture(*t);CHECK(r.Write(*t,s)&&r.Confirm(*t,s));
    auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));auto latest=r.Receipt("synthetic-path");
    CHECK(!r.Confirm(*t,s));CHECK(r.Receipt("synthetic-path").snapshot==latest.snapshot&&r.Disk("synthetic-path")==2);
  }else if(name=="foreign_snapshot_rejected"){
    auto a=Make(r),b=Make(r);Value(r,a,1);auto t=r.TryBegin(a);auto s=r.Capture(*t);auto foreign=s;foreign.owner=b->id;
    CHECK(!r.Write(*t,foreign));CHECK(r.Write(*t,s));CHECK(!r.Confirm(*t,foreign));
    CHECK(r.Confirmed(a->id)==0);CHECK(r.Confirm(*t,s));
  }else if(name=="same_path_ordering"){
    auto a=Make(r),b=Make(r);Value(r,a,1);Value(r,b,2);auto ta=r.TryBegin(a);auto sa=r.Capture(*ta);
    std::atomic<bool> excluded{false};std::thread contender([&]{auto tb=r.TryBegin(b);excluded=!tb;});contender.join();
    CHECK(excluded);CHECK(r.Write(*ta,sa)&&r.Confirm(*ta,sa));
    CHECK(Save(r,b));CHECK(!r.Confirm(*ta,sa));CHECK(r.Disk("synthetic-path")==2&&r.Receipt("synthetic-path").snapshot.owner==b->id);
  }else if(name=="different_paths_independent"){
    auto a=Make(r,"p1"),b=Make(r,"p2");Value(r,a,1);Value(r,b,2);auto ta=r.TryBegin(a),tb=r.TryBegin(b);CHECK(ta&&tb);
    auto sa=r.Capture(*ta),sb=r.Capture(*tb);CHECK(r.Write(*ta,sa)&&r.Write(*tb,sb));CHECK(r.Confirm(*tb,sb)&&r.Confirm(*ta,sa));
  }else if(name=="failed_save_blocks_retirement"){
    auto a=Make(r);Value(r,a,1);auto t=r.TryBegin(a);auto s=r.Capture(*t);CHECK(!r.Write(*t,s,false));CHECK(!r.Confirm(*t,s));
    auto id=a->id;t.reset();a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));CHECK(r.Retire()==0&&r.Pinned(id));
  }else if(name=="pending_token_blocks_retirement"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));auto id=a->id;a.reset();auto b=Make(r);Value(r,b,2);auto t=r.TryBegin(b);auto s=r.Capture(*t);
    CHECK(r.Retire()==0&&r.Pinned(id));CHECK(r.Write(*t,s)&&r.Confirm(*t,s));CHECK(r.Retire()==1);
  }else if(name=="conflicting_revision_blocks_retirement"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));Value(r,a,9);auto id=a->id;a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));
    CHECK(r.Retire()==0&&r.Pinned(id));
  }else if(name=="durability_failure_blocks_retirement"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));auto id=a->id;a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));r.DurabilityFailed("synthetic-path");
    CHECK(r.Retire()==0&&r.Pinned(id)&&r.Receipt("synthetic-path").requiresDurability);
  }else if(name=="missing_replacement_blocks_retirement"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));auto id=a->id;a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));r.DropReceiptForTest("synthetic-path");
    CHECK(r.Retire()==0&&r.Pinned(id));
  }else if(name=="unknown_coverage_blocks_retirement"){
    auto a=Make(r,"synthetic-path",Coverage::Unknown);Value(r,a,1);CHECK(Save(r,a));auto id=a->id;a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));
    CHECK(r.Retire()==0&&r.Pinned(id));
  }else if(name=="mutation_guard_categories"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));
    for(int kind=1;kind<=4;++kind){
      auto t=r.TryBegin(a);auto before=r.Capture(*t);CHECK(r.Write(*t,before));
      if(kind==1)Value(r,a,2);
      if(kind==2)r.Default(a,3);
      if(kind==3)r.Insert(a,4,5);
      if(kind==4)r.Erase(a,4);
      CHECK(r.Revision(a->id)>before.revision&&!r.Confirm(*t,before));
      CHECK(Save(r,a));auto after=r.Receipt("synthetic-path").snapshot;
      if(kind==1)CHECK(after.value!=before.value);
      if(kind==2)CHECK(after.defaultValue!=before.defaultValue);
      if(kind==3||kind==4)CHECK(after.items!=before.items);
    }
    // Complete for this encapsulated payload, not a native mutation-coverage certificate.
  }else if(name=="retirement_destruction_outside_lock"){
    bool destroyed=false,reentered=false;auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));
    a->onDestroy=[&]{CHECK(!r.LockedForTest());reentered=r.Count()==2;destroyed=true;};
    std::weak_ptr<Object> weak=a;a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));
    auto pending=r.Receipt("synthetic-path");CHECK(r.Retire()==1&&weak.expired()&&destroyed&&reentered);
    CHECK(r.Receipt("synthetic-path").snapshot==pending.snapshot&&r.Receipt("synthetic-path").requiresDurability);
  }else if(name=="external_lease_preserved"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));CHECK(r.Retire()==0&&r.Pinned(a->id));
    a.reset();CHECK(r.Retire()==1);
  }else if(name=="weak_reacquisition_repins"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));auto id=a->id;a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));Owner acquired;
    CHECK(r.Retire([&](std::weak_ptr<Object> w){acquired=w.lock();})==1);CHECK(acquired&&!r.Pinned(id));
    Value(r,acquired,3);CHECK(r.Pinned(id));acquired.reset();CHECK(r.Retire()==0);
  }else if(name=="abandoned_token_retains_obligation"){
    auto a=Make(r);Value(r,a,1);{auto t=r.TryBegin(a);r.Capture(*t);}auto id=a->id;a.reset();auto b=Make(r);Value(r,b,2);CHECK(Save(r,b));
    CHECK(r.Retire()==0&&r.Pinned(id));
  }else if(name=="revision_overflow_fails_closed"){
    auto a=Make(r);Value(r,a,1);CHECK(Save(r,a));r.RevisionAtLimitForTest(a->id);Value(r,a,2);CHECK(Save(r,a));auto id=a->id;a.reset();
    auto b=Make(r);Value(r,b,3);CHECK(Save(r,b));CHECK(r.Retire()==0&&r.Pinned(id));
  }else throw std::runtime_error("unselected case");
}
int main(int argc,char** argv){try{CHECK(argc==2);Run(argv[1]);std::cout<<"{\"case\":\""<<argv[1]<<"\",\"expected_result_observed\":true,\"scope\":\"synthetic_contract_only\"}\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
