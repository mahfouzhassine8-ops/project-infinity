"""Route Kodi numeric text entry through the same mobile IME owner."""
from native_controls import once


def repair(s):
    s=once(s,'#include "GUIDialogNumeric.h"','''#include "GUIDialogNumeric.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/AndroidKeyboard.h"
#include "guilib/GUIKeyboardFactory.h"
#include <cstdio>
#endif''')
    def start(signature,body):
        nonlocal s
        anchor=signature+'\n{'
        s=once(s,anchor,anchor+'\n#if defined(TARGET_ANDROID)\n  if (CAndroidKeyboard::UseAndroidIME())\n  {\n'+body+'\n  }\n#endif')
    start('bool CGUIDialogNumeric::ShowAndGetSeconds(std::string &timeString, const std::string &heading)',
'''    CAndroidKeyboard::InputScope kind(5);
    std::string edited = StringUtils::SecondsToTimeString(StringUtils::TimeStringToSeconds(timeString), TIME_FORMAT_HH_MM_SS);
    if (!CGUIKeyboardFactory::ShowAndGetInput(edited, CVariant{heading}, false)) return false;
    timeString = StringUtils::SecondsToTimeString(StringUtils::TimeStringToSeconds(edited));
    return true;''')
    start('bool CGUIDialogNumeric::ShowAndGetTime(KODI::TIME::SystemTime& time, const std::string& heading)',
'''    CAndroidKeyboard::InputScope kind(3);
    std::string edited = StringUtils::Format("{:02}:{:02}", time.hour, time.minute);
    if (!CGUIKeyboardFactory::ShowAndGetInput(edited, CVariant{heading}, false)) return false;
    unsigned hour, minute;
    if (std::sscanf(edited.c_str(), "%u:%u", &hour, &minute) != 2 || hour > 23 || minute > 59) return false;
    time.hour = hour; time.minute = minute;
    return true;''')
    start('bool CGUIDialogNumeric::ShowAndGetDate(KODI::TIME::SystemTime& date, const std::string& heading)',
'''    CAndroidKeyboard::InputScope kind(4);
    std::string edited = StringUtils::Format("{:04}-{:02}-{:02}", date.year, date.month, date.day);
    if (!CGUIKeyboardFactory::ShowAndGetInput(edited, CVariant{heading}, false)) return false;
    unsigned year, month, day;
    if (std::sscanf(edited.c_str(), "%u-%u-%u", &year, &month, &day) != 3) return false;
    date.year = year; date.month = month; date.day = day;
    return true;''')
    start('bool CGUIDialogNumeric::ShowAndGetIPAddress(std::string &IPAddress, const std::string &heading)',
'''    CAndroidKeyboard::InputScope kind(2);
    return CGUIKeyboardFactory::ShowAndGetInput(IPAddress, CVariant{heading}, false);''')
    start('bool CGUIDialogNumeric::ShowAndGetNumber(std::string& strInput, const std::string &strHeading, unsigned int iAutoCloseTimeoutMs /* = 0 */, bool bSetHidden /* = false */)',
'''    CAndroidKeyboard::InputScope kind(1);
    return CGUIKeyboardFactory::ShowAndGetInput(strInput, CVariant{strHeading}, true, bSetHidden, iAutoCloseTimeoutMs);''')
    # Preserve the original digest/verification semantics; never prefill a digest
    # into an Android password field when Kodi is asking the user to verify it.
    old='''  // Prompt user for password input
  CGUIDialogNumeric *pDialog = CServiceBroker::GetGUI()->GetWindowManager().GetWindow<CGUIDialogNumeric>(WINDOW_DIALOG_NUMERIC);
  pDialog->SetHeading(dlgHeading);

  std::string strInput;
  if (!bVerifyInput)
    strInput = strToVerify;

  pDialog->SetMode(INPUT_PASSWORD, strInput);
  pDialog->Open();

  strInput = pDialog->GetOutputString();

  if (!pDialog->IsConfirmed() || pDialog->IsCanceled())'''
    new='''  std::string strInput = bVerifyInput ? "" : strToVerify;
  bool accepted = false;
#if defined(TARGET_ANDROID)
  if (CAndroidKeyboard::UseAndroidIME())
  {
    CAndroidKeyboard::InputScope kind(1);
    accepted = CGUIKeyboardFactory::ShowAndGetInput(strInput, CVariant{dlgHeading}, true, true);
  }
  else
#endif
  {
    auto* pDialog = CServiceBroker::GetGUI()->GetWindowManager().GetWindow<CGUIDialogNumeric>(WINDOW_DIALOG_NUMERIC);
    if (pDialog)
    {
      pDialog->SetHeading(dlgHeading);
      pDialog->SetMode(INPUT_PASSWORD, strInput);
      pDialog->Open();
      strInput = pDialog->GetOutputString();
      accepted = pDialog->IsConfirmed() && !pDialog->IsCanceled();
    }
  }
  if (!accepted)'''
    return once(s,old,new)
