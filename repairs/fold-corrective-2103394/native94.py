#!/usr/bin/env python3
"""Cause-based 2103394 overlays, after the unchanged verified 2103393 binder.

No protected-writer exception is excused. Every source preimage is checked
against the complete compiled 2103393 source map before applying this layer.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE93_SHA256 = '3101b59ae974d0c8ad83ebbdc0569543dd403fb50325d8eaf686b14a709e1c86'
WINDOW = 'xbmc/interfaces/legacy/Window.cpp'
OBSERVER = 'xbmc/interfaces/python/InfinityPythonPersistenceSource.h'


def require(value, reason):
    if not value:
        raise ValueError('2103394 native correction refused: ' + reason)


def once(raw, old, new):
    require(raw.count(old) == 1, 'missing or ambiguous source anchor: ' + repr(old[:100]))
    return raw.replace(old, new, 1)


def window_language_hook(raw):
    """Preserve a wrapped control's actual window/interpreter ownership.

    SWIG sets the thread-local hook for constructors and free functions, but
    not ordinary member methods. Window.getControl creates ControlList wrappers
    from a member call. Without its parent hook, the wrapper later enters
    GuiLock with no hook and retains the GIL while acquiring the frame guard.
    The observed ControlList.getSelectedItem waiter closes the captured cycle.
    """
    raw = once(raw, b'#include "Window.h"',
               b'#include "Window.h"\n#if defined(TARGET_ANDROID)\n'
               b'#include "interfaces/legacy/ModuleXbmc.h"\n#endif')
    old = b'''    Control* Window::getControl(int iControlId)
    {
      XBMC_TRACE;
      DelayedCallGuard dg(languageHook);
      return GetControlById(iControlId,&CServiceBroker::GetWinSystem()->GetGfxContext());
    }'''
    new = b'''    Control* Window::getControl(int iControlId)
    {
      XBMC_TRACE;
      // INFINITY_2103394_CONTROL_LANGUAGE_HOOK: a wrapper created by this
      // member call must inherit the same interpreter hook as its real window.
      // Later ControlList GUI calls can then release their GIL before taking
      // frame/graphics locks. Do not change Cobra or other skins' paths.
#if defined(TARGET_ANDROID)
      std::unique_ptr<XBMCAddon::SetLanguageHookGuard> infinityControlHook;
      if (XBMCAddon::xbmc::getSkinDir() == "skin.infinity.diggz" &&
          languageHook != nullptr && XBMCAddon::LanguageHook::GetLanguageHook() == nullptr)
        infinityControlHook = std::make_unique<XBMCAddon::SetLanguageHookGuard>(languageHook);
#endif
      DelayedCallGuard dg(languageHook);
      return GetControlById(iControlId,&CServiceBroker::GetWinSystem()->GetGfxContext());
    }'''
    return once(raw, old, new)


def observer_detail(raw):
    """Add bounded exception facts to the original sticky native failure.

    Do not include exception messages, SQL, arguments, media titles or full
    paths. Build the traceback from objects already in memory: no imports,
    files, network, background recorder, or new persistence owner is needed.
    """
    old = b"        if target is not None and self.protect is not None and operation in (\n"
    new = b'''        # INFINITY_2103394_FAILURE_CONTEXT: preserve the original exception
        # and all native admission failures; diagnostic gaps never grant safety.
        try:
            error = sys.exc_info()[1]
            if error is not None:
                facts = ['exception=' + type(error).__name__[:80]]
                for field in ('errno', 'sqlite_errorcode'):
                    value = getattr(error, field, None)
                    if type(value) is int:
                        facts.append(field + '=' + str(value))
                frames, tb = [], error.__traceback__
                while tb is not None:
                    code = tb.tb_frame.f_code
                    # Keep only module basenames and identifier-shaped symbols.
                    # No locals, message, URL, title, SQL or private directory.
                    name = str(code.co_filename).replace('\\\\', '/').rsplit('/', 1)[-1]
                    name = name if name.endswith('.py') and all(
                        c.isalnum() or c in '_.-' for c in name) else '<observer>'
                    symbol = str(code.co_name)
                    symbol = symbol if all(c.isalnum() or c == '_' for c in symbol) else '<call>'
                    frames.append(name[:80] + ':' + str(tb.tb_lineno) + ':' + symbol[:80])
                    tb = tb.tb_next
                facts.append('stack=' + ('>'.join(frames[-8:]) if frames else '<missing>'))
                detail = (detail + ';' if detail else '') + ';'.join(facts)
        except Exception:
            detail = (detail + ';' if detail else '') + 'exception_detail_unavailable'
        detail = detail[:1600]
''' + old
    return once(raw, old, new)


def checked_sources(root, expected):
    require(len(expected) == 9404 and hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(',',':')).encode()).hexdigest() == SOURCE93_SHA256, 'the exact complete signed-baseline source map is mandatory')
    for name, pin in expected.items():
        path = Path(root) / name
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == pin,
                'protected native source drift: ' + name)
