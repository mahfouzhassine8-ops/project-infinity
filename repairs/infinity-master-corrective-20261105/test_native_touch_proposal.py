"""Review-only patch scope plus existing controller helper on the host."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

import prepare_touch_proposal as proposal


def region(raw,start,end):return raw[raw.index(start):raw.index(end,raw.index(start))]


class TouchProposal(unittest.TestCase):
    def setUp(self):self.before,self.after=proposal.proposed_sources()

    def test_only_two_native_files_are_proposed_and_neither_is_changed(self):
        self.assertEqual(set(self.after),{'xbmc/input/InputManager.cpp','xbmc/guilib/GUIBaseContainer.cpp'})
        for name,raw in self.before.items():self.assertEqual((proposal.NATIVE/name).read_text(),raw)

    def test_input_diff_is_only_existing_active_view_and_home_favorites_admission(self):
        name='xbmc/input/InputManager.cpp';raw=self.before[name]
        raw=raw.replace('if (wm.GetActiveWindow() == WINDOW_VIDEO_NAV) ids.push_back(owner->GetViewContainerID());','if (wm.GetActiveWindow() == WINDOW_VIDEO_NAV || wm.GetActiveWindow() == WINDOW_FAVOURITES)\n            ids.push_back(owner->GetViewContainerID());',1)
        raw=raw.replace('9201,9202};','9201,9202,8109,8609,8709,8809};',1)
        self.assertEqual(raw,self.after[name])
        self.assertLess(self.after[name].index('view->OnInfinityMediaTouch'),self.after[name].index('// Send a mouse motion event'))

    def test_only_six_container_methods_change_no_class_or_playback_change(self):
        name='xbmc/guilib/GUIBaseContainer.cpp'
        spans=[('bool CGUIBaseContainer::OnInfinityOptionBLongPress(', 'bool CGUIBaseContainer::OnInfinityFavouritesLongPress('),
               ('bool CGUIBaseContainer::OnInfinityFavouritesLongPress(', 'bool CGUIBaseContainer::OnInfinityRailLongPress('),
               ('bool CGUIBaseContainer::OnInfinityMediaTouch(', 'bool CGUIBaseContainer::OnInfinityAddonBrowserTouch('),
               ('bool CGUIBaseContainer::OnInfinityUiTouch(', 'bool CGUIBaseContainer::OnInfinityUiContextMenu('),
               ('bool CGUIBaseContainer::OnMessage(', 'void CGUIBaseContainer::OnUp('),
               ('void CGUIBaseContainer::Reset()', 'void CGUIBaseContainer::LoadLayout(')]
        a,b=self.before[name],self.after[name]
        for start,end in spans:
            a=a.replace(region(a,start,end),'ALLOWED_METHOD\n',1)
            b=b.replace(region(b,start,end),'ALLOWED_METHOD\n',1)
        self.assertEqual(a,b)
        before_focus=region(self.before[name],'void CGUIBaseContainer::SetFocus(', 'void CGUIBaseContainer::SaveStates(')
        self.assertEqual(before_focus,region(self.after[name],'void CGUIBaseContainer::SetFocus(', 'void CGUIBaseContainer::SaveStates('))

    def test_existing_hit_ownership_and_context_guards_survive(self):
        body=region(self.after['xbmc/guilib/GUIBaseContainer.cpp'],'bool CGUIBaseContainer::OnInfinityMediaTouch(', 'bool CGUIBaseContainer::OnInfinityAddonBrowserTouch(')
        for guard in ('!HasProcessed()', 'm_gestureActive', 'windows.GetActiveWindow() != GetParentID()',
                      'windows.GetTopmostModalDialog() != WINDOW_INVALID', 'skin.infinity.diggz',
                      'm_cachedTransform.InverseTransformPosition', '!CanFocusFromPoint(point)',
                      'window->GetFocusedControlID() != GetID()', 'InfinityTitleOwnerReady()',
                      'InfinityOpenTitlePopup(item)', 'OnClick(ACTION_CONTEXT_MENU)',
                      'OnClick(ACTION_SELECT_ITEM)', 'if (sharedHome || sharedBrowse) return reject()',
                      'if (item->IsParentFolder()) return reject(); // retain original one-tap Back navigation'):
            self.assertIn(guard,body)
        self.assertNotIn('elapsed <= std::chrono::seconds(5)',body)
        self.assertEqual(body.count('InfinityTouchPress('),2)
        # No button method, route construction, player mutation or keymap write.
        self.assertNotIn('executebuiltin',body)
        self.assertNotIn('PostMsg',body)

    def test_legacy_hold_contexts_remain_exact_except_shared_pair_suppression(self):
        n='xbmc/guilib/GUIBaseContainer.cpp'
        a,b=self.before[n],self.after[n]
        option_start='bool CGUIBaseContainer::OnInfinityOptionBLongPress('
        option_end='bool CGUIBaseContainer::OnInfinityFavouritesLongPress('
        option=region(b,option_start,option_end)
        hook='  InfinityTouchPress(this, "", false, true, std::chrono::steady_clock::now());\n'
        self.assertEqual(option.count(hook),1)
        self.assertEqual(option.replace(hook,'',1),region(a,option_start,option_end))
        self.assertLess(option.index('home->GetFocusedControlID() != GetID()'),option.index(hook))
        self.assertLess(option.index(hook),option.index('RunScript(script.infinity.uirepair,option-b,'))
        ui_start='bool CGUIBaseContainer::OnInfinityUiTouch('
        ui_end='bool CGUIBaseContainer::OnInfinityUiContextMenu('
        ui=region(b,ui_start,ui_end)
        hook='    if (resume)\n      InfinityTouchPress(this, "", false, true, std::chrono::steady_clock::now());\n'
        self.assertEqual(ui.count(hook),1)
        self.assertEqual(ui.replace(hook,'',1),region(a,ui_start,ui_end))
        self.assertLess(ui.index('(resume && kind != "resume")'),ui.index(hook))
        self.assertGreater(ui.index(hook),ui.index('  if (hold)\n  {'))

    def test_existing_helper_and_proposed_focus_hold_snippets_check_sixteen_cases(self):
        raw=self.before['xbmc/guilib/GUIBaseContainer.cpp']
        helper=raw[raw.index('enum class InfinityTouchDecision'):raw.index('} // No GUI, file I/O or callback')]
        framing=region(raw,'static void InfinitySelectionField(', 'bool CGUIBaseContainer::OnInfinityOptionBLongPress(')
        framing=framing[:framing.index('\n}')+2]  # exact helper, excluding surrounding native #endif
        focus=region(self.after['xbmc/guilib/GUIBaseContainer.cpp'],
            'bool CGUIBaseContainer::OnMessage(CGUIMessage& message)\n{',
            '\n  if (message.GetControlId() == GetID() )').split('{',1)[1]
        focus_fixture='''
constexpr int GUI_MSG_LOSTFOCUS = 1;
struct FocusMessage {
  int control, kind, target;
  int GetControlId() const { return control; }
  int GetMessage() const { return kind; }
  int GetParam1() const { return target; }
};
struct FocusControl {
  int GetID() const { return 50; }
  void Receive(FocusMessage& message) {
'''+focus+'''
  }
};
'''
        proposed=self.after['xbmc/guilib/GUIBaseContainer.cpp']
        option=region(proposed,'bool CGUIBaseContainer::OnInfinityOptionBLongPress(',
            'bool CGUIBaseContainer::OnInfinityFavouritesLongPress(')
        option_hook=option[option.index('  InfinityTouchPress(this, "", false, true,'):].splitlines()[0]
        resume=region(proposed,'bool CGUIBaseContainer::OnInfinityUiTouch(',
            'bool CGUIBaseContainer::OnInfinityUiContextMenu(')
        resume_hook=region(resume,'    if (resume)\n      InfinityTouchPress(', '    m_infinityUiTapKey = token;')
        legacy_fixture='''
struct LegacyHoldControl {
  void OptionHold() {
'''+option_hook+'''
  }
  void ResumeOrOtherHold(bool resume) {
'''+resume_hook+'''
  }
};
'''
        cpp='''#include <atomic>
#include <chrono>
#include <mutex>
#include <string>
#include <unordered_map>
#include <cassert>
#include <iostream>
'''+helper+framing+focus_fixture+legacy_fixture+r'''
int main() {
  using D=InfinityTouchDecision;
  using namespace std::chrono;
  int a=0,b=0;
  const auto epoch=steady_clock::time_point{};
  auto press=[&](const void* owner,const std::string& key,bool same,bool hold,int ms) {
    return InfinityTouchPress(owner,key,same,hold,epoch+milliseconds(ms));
  };
  InfinityTouchClearForAction(&a); InfinityTouchForget(&a);
  assert(gInfinityTouchStore.load()==nullptr); // 1: clearing never allocates
  assert(press(&a,"title",true,false,0)==D::SelectOnly); // 2: default focus is not a tap
  assert(press(&a,"title",true,false,10000)==D::Activate); // 3: no arbitrary 5s expiry
  assert(press(&a,"title",false,false,10001)==D::SelectOnly);
  assert(press(&a,"title",true,false,10002)==D::Activate); // 4: changed selection needs a pair
  assert(press(&a,"one",true,false,10003)==D::SelectOnly);
  assert(press(&a,"two",true,false,10004)==D::SelectOnly);
  assert(press(&a,"two",true,false,10005)==D::Activate); // 5: recycled target cannot inherit
  assert(press(&a,"hold",true,false,11000)==D::SelectOnly);
  assert(press(&a,"hold",true,true,11010)==D::Context);
  assert(press(&a,"hold",true,false,11100)==D::SelectOnly);
  assert(press(&a,"hold",true,false,11611)==D::SelectOnly);
  assert(press(&a,"hold",true,false,11612)==D::Activate); // 6: hold and ghost tap never activate
  assert(press(&a,"same",true,false,12000)==D::SelectOnly);
  assert(press(&b,"same",true,false,12001)==D::SelectOnly); // 7: owners are isolated
  InfinityTouchClearForAction(&a);
  assert(press(&a,"same",true,false,12002)==D::SelectOnly); // 8: rebind/focus clear starts unarmed
  InfinityTouchClearForAction(&a);
  assert(press(&a,"same",true,false,12003)==D::SelectOnly); // 9: remote action cannot arm touch
  InfinityTouchForget(&a);
  assert(press(&a,"same",true,false,12004)==D::SelectOnly); // 10: destroyed/reused owner has no pair
  assert(press(&a,"",true,false,12005)==D::SelectOnly);
  assert(press(&a,"",true,false,12006)==D::SelectOnly); // 11: empty identity never activates
  std::string x,y;
  for (const auto& f : {std::string("a\nb"),std::string("c")}) InfinitySelectionField(x,f);
  for (const auto& f : {std::string("a"),std::string("b\nc")}) InfinitySelectionField(y,f);
  assert(x!=y); // 12: field framing prevents separator collisions
  bool focused=false;
  auto refocusTap=[&](int ms) {
    if (!focused) InfinityTouchClearForAction(&a);
    focused=false; focused=true; // native GUI_MSG_SETFOCUS's same-control cycle
    return press(&a,"focus-sequence",true,false,ms);
  };
  assert(refocusTap(13000)==D::SelectOnly);
  assert(refocusTap(13001)==D::Activate);
  focused=false;
  assert(refocusTap(13002)==D::SelectOnly); // 13: genuine lost focus starts a new pair
  FocusControl view;
  assert(press(&view,"actual-focus-condition",true,false,14000)==D::SelectOnly);
  FocusMessage self{50,GUI_MSG_LOSTFOCUS,50}; view.Receive(self);
  assert(press(&view,"actual-focus-condition",true,false,14001)==D::Activate);
  assert(press(&view,"actual-focus-condition",true,false,14002)==D::SelectOnly);
  FocusMessage other{50,GUI_MSG_LOSTFOCUS,201}; view.Receive(other);
  assert(press(&view,"actual-focus-condition",true,false,14003)==D::SelectOnly); // 14: actual added condition
  LegacyHoldControl legacy;
  auto current=steady_clock::now();
  assert(InfinityTouchPress(&legacy,"legacy-title",true,false,current)==D::SelectOnly);
  legacy.OptionHold();
  assert(InfinityTouchPress(&legacy,"legacy-title",true,false,steady_clock::now())==D::SelectOnly);
  current=steady_clock::now()+milliseconds(601);
  assert(InfinityTouchPress(&legacy,"legacy-title",true,false,current)==D::SelectOnly); // 15: valid legacy context disarms prior tap
  InfinityTouchForget(&legacy);
  current=steady_clock::now();
  assert(InfinityTouchPress(&legacy,"legacy-resume",true,false,current)==D::SelectOnly);
  legacy.ResumeOrOtherHold(false);
  assert(InfinityTouchPress(&legacy,"legacy-resume",true,false,steady_clock::now())==D::Activate);
  assert(InfinityTouchPress(&legacy,"legacy-resume",true,false,steady_clock::now())==D::SelectOnly);
  legacy.ResumeOrOtherHold(true);
  assert(InfinityTouchPress(&legacy,"legacy-resume",true,false,steady_clock::now())==D::SelectOnly);
  current=steady_clock::now()+milliseconds(601);
  assert(InfinityTouchPress(&legacy,"legacy-resume",true,false,current)==D::SelectOnly); // 16: Resume hold suppresses; other UI contexts unchanged
  InfinityTouchForget(&legacy);
  InfinityTouchForget(&view);
  InfinityTouchForget(&a); InfinityTouchForget(&b);
  std::cout << "16 controller/focus/hold host cases PASS; full proposed GUI methods and native engine NOT COMPILED.\n";
}
'''
        with tempfile.TemporaryDirectory(prefix='infinity-touch-proposal-host-') as d:
            path=Path(d);(path/'touch.cpp').write_text(cpp)
            compile_=subprocess.run(['c++','-std=c++17','-pthread','-O0','-Wall','-Wextra','-Werror',str(path/'touch.cpp'),'-o',str(path/'touch')],capture_output=True,text=True)
            self.assertEqual(compile_.returncode,0,compile_.stderr)
            run=subprocess.run([str(path/'touch')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('16 controller/focus/hold host cases PASS',run.stdout)
            print(run.stdout.strip())


if __name__=='__main__':unittest.main(verbosity=2)
