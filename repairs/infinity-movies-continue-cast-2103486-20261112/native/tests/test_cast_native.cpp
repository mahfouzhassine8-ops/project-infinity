#include <cassert>
#include <iostream>
#include <string>
#include "../overlay/xbmc/platform/android/activity/InfinityCastNative.cpp"

int main()
{
  JNIEnv env;
  const std::string token(32,'a'),other(32,'b');
  auto begin=[&](const std::string& op,const std::string& key,int64_t position=0) {
    return Java_com_projectinfinity_kodi_InfinityCastNative_request(&env,nullptr,&op,&key,position);
  };
  auto result=[&](jlong id) {
    auto bytes=Java_com_projectinfinity_kodi_InfinityCastNative_poll(&env,nullptr,id);
    assert(bytes); std::string text(bytes->begin(),bytes->end());delete bytes;return text;
  };
  auto contains=[](const std::string& text,const std::string& part) { assert(text.find(part)!=std::string::npos); };
  auto id=begin("pause",token);messenger.Drain();contains(result(id),"stale_session");
  assert(g_application.player->pauses==0);
  id=begin("capture",token);messenger.Drain();contains(result(id),"\"status\":\"ok\"");
  id=begin("pause",token);messenger.Drain();contains(result(id),"\"status\":\"ok\"");
  assert(g_application.player->paused && g_application.player->pauses==1);

  // Same URI replay is a DIFFERENT playing CFileItem. Old control must fail.
  id=begin("seek",token,258000);g_application.item=std::make_shared<CFileItem>();
  messenger.Drain();contains(result(id),"source_changed");assert(g_application.player->seeks==0);
  id=begin("capture",other);messenger.Drain();result(id);
  id=begin("release",token);messenger.Drain();contains(result(id),"stale_session");

  id=begin("resume",other);
  assert(Java_com_projectinfinity_kodi_InfinityCastNative_cancel(&env,nullptr,id)==JNI_TRUE);
  messenger.Drain();assert(g_application.player->paused && g_application.player->pauses==1);

  id=begin("seek",other,258000);
  { auto& state=Store();std::lock_guard<std::mutex> lock(state.mutex);
    for(auto& slot:state.slots) if(slot.id==static_cast<uint64_t>(id))slot.deadline=Clock::now()-std::chrono::milliseconds(1); }
  messenger.Drain();contains(result(id),"cancelled");assert(g_application.player->seeks==0);

  InfinityAndroidCheckpoint::active=true;
  id=begin("resume",other);messenger.Drain();contains(result(id),"closing");
  assert(g_application.player->pauses==1);InfinityAndroidCheckpoint::active=false;
  settings.skin="some.other.skin";
  id=begin("capture",token);messenger.Drain();contains(result(id),"not_infinity");
  settings.skin="skin.infinity.diggz";
  g_application.player->playing=false;
  id=begin("capture",token);messenger.Drain();contains(result(id),"no_video");
  g_application.player->playing=true;

  // Capacity is bounded. Cancelled queued slots cannot be recycled until their
  // original callback is processed, so an old callback cannot run new work.
  std::vector<jlong> queued;
  for(size_t i=0;i<Capacity;++i){auto next=begin("snapshot",other);assert(next);queued.push_back(next);}
  assert(begin("snapshot",other)==0);
  for(auto queuedId:queued) assert(Java_com_projectinfinity_kodi_InfinityCastNative_cancel(&env,nullptr,queuedId)==JNI_TRUE);
  assert(begin("snapshot",other)==0);messenger.Drain();
  id=begin("snapshot",other);assert(id);messenger.Drain();contains(result(id),"\"status\":\"ok\"");
  std::cout<<"PASS_CAST_NATIVE_HOST_MOCK_BACKENDS_NOT_ANDROID_OR_FOLD\n";
}
