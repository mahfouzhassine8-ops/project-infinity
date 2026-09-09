#!/usr/bin/env python3
"""Apply the narrow Infinity 1.0.6 native/source correction after bridge v4.

This intentionally changes only:
- Android version progression for the update chain.
- Both Kodi native splash paths from fill/crop to contain/keep.
- Kodi's font loader so the optional System fontset can resolve Android's current
  generic system font at runtime on API 29+, with a deterministic Infinity fallback.

Run this only after scripts/infinity71.py source has applied the pinned v4 bridge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def patch_text(path: Path, transform) -> None:
    before = path.read_text()
    after = transform(before)
    if after == before:
        raise RuntimeError(f'No change produced for {path}')
    path.write_text(after)


def patch_gradle(text: str) -> str:
    text = replace_once(text, 'versionCode 2103100', 'versionCode 2103106', 'versionCode')
    text = replace_once(text, 'versionName "21.3-Infinity-Android-First"',
                        'versionName "21.3-Infinity-1.0.6"', 'versionName')
    return text


def patch_render_system(text: str) -> str:
    return replace_once(text,
        'm_splashImage->SetAspectRatio(CAspectRatio::AR_SCALE);',
        'm_splashImage->SetAspectRatio(CAspectRatio::AR_KEEP);',
        'RenderSystem native splash aspect')


def patch_window_splash(text: str) -> str:
    return replace_once(text,
        'm_image->SetAspectRatio(CAspectRatio::AR_SCALE);',
        'm_image->SetAspectRatio(CAspectRatio::AR_KEEP);',
        'GUIWindowSplash native splash aspect')


FONT_HELPER = r'''
#if defined(TARGET_ANDROID)
// Resolve the current Android generic family without linking API-29 symbols into
// Infinity's min-SDK-21 binary. On older Android versions or OEMs where the
// matcher is unavailable, the caller falls back to Infinity's bundled Noto font.
std::string InfinityResolveAndroidSystemFont(const std::string& requested, int style)
{
  const bool mono = StringUtils::EqualsNoCase(requested, "InfinitySystem-Mono.ttf");
  if (!mono && !StringUtils::EqualsNoCase(requested, "InfinitySystem.ttf"))
    return {};

  void* lib = dlopen("libandroid.so", RTLD_NOW | RTLD_LOCAL);
  if (!lib)
    return {};

  using MatcherCreate = void* (*)();
  using MatcherDestroy = void (*)(void*);
  using MatcherSetStyle = void (*)(void*, uint16_t, bool);
  using MatcherMatch = void* (*)(const void*, const char*, const uint16_t*, uint32_t, uint32_t*);
  using FontGetPath = const char* (*)(const void*);
  using FontClose = void (*)(void*);

  const auto create = reinterpret_cast<MatcherCreate>(dlsym(lib, "AFontMatcher_create"));
  const auto destroy = reinterpret_cast<MatcherDestroy>(dlsym(lib, "AFontMatcher_destroy"));
  const auto setStyle = reinterpret_cast<MatcherSetStyle>(dlsym(lib, "AFontMatcher_setStyle"));
  const auto match = reinterpret_cast<MatcherMatch>(dlsym(lib, "AFontMatcher_match"));
  const auto getPath = reinterpret_cast<FontGetPath>(dlsym(lib, "AFont_getFontFilePath"));
  const auto closeFont = reinterpret_cast<FontClose>(dlsym(lib, "AFont_close"));

  std::string path;
  if (create && destroy && setStyle && match && getPath && closeFont)
  {
    void* matcher = create();
    if (matcher)
    {
      const uint16_t weight = (style & FONT_STYLE_BOLD) ? 700 :
                              (style & FONT_STYLE_LIGHT) ? 300 : 400;
      const bool italic = (style & FONT_STYLE_ITALICS) != 0;
      setStyle(matcher, weight, italic);
      const uint16_t sample = static_cast<uint16_t>('A');
      uint32_t runLength = 0;
      void* font = match(matcher, mono ? "monospace" : "sans-serif",
                         &sample, 1, &runLength);
      if (font)
      {
        const char* resolved = getPath(font);
        if (resolved && resolved[0] != '\0')
          path = resolved;
        closeFont(font);
      }
      destroy(matcher);
    }
  }
  dlclose(lib);
  return path;
}
#endif
'''


def patch_font_manager(text: str) -> str:
    include_anchor = '#include <algorithm>\n#include <set>\n'
    include_repl = '#include <algorithm>\n#include <cstdint>\n#include <set>\n#if defined(TARGET_ANDROID)\n#include <dlfcn.h>\n#endif\n'
    text = replace_once(text, include_anchor, include_repl, 'GUIFontManager includes')

    helper_anchor = 'constexpr const char* XML_FONTCACHE_FILENAME = "fontcache.xml";\n'
    text = replace_once(text, helper_anchor, helper_anchor + FONT_HELPER,
                        'GUIFontManager system-font helper')

    start = text.index('CGUIFont* GUIFontManager::LoadTTF(')
    end = text.index('\nbool GUIFontManager::OnMessage(', start)
    body = text[start:end]
    body = replace_once(body, '  float originalAspect = aspect;\n', '''  float originalAspect = aspect;\n\n  std::string effectiveFilename = strFilename;\n#if defined(TARGET_ANDROID)\n  const bool infinitySystemFont =\n      StringUtils::EqualsNoCase(strFilename, "InfinitySystem.ttf") ||\n      StringUtils::EqualsNoCase(strFilename, "InfinitySystem-Mono.ttf");\n  if (infinitySystemFont)\n  {\n    const std::string resolved = InfinityResolveAndroidSystemFont(strFilename, iStyle);\n    if (!resolved.empty())\n      effectiveFilename = resolved;\n    else\n      effectiveFilename = StringUtils::EqualsNoCase(strFilename, "InfinitySystem-Mono.ttf")\n                              ? "NotoMono-Regular.ttf" : "NotoSans-Regular.ttf";\n  }\n#endif\n''', 'LoadTTF system-font selection')

    replacements = [
        ('CURL::IsFullPath(strFilename)', 'CURL::IsFullPath(effectiveFilename)'),
        ('context.GetMediaDir(), "fonts", strFilename', 'context.GetMediaDir(), "fonts", effectiveFilename'),
        ('strPath = strFilename;', 'strPath = effectiveFilename;'),
        ('URIUtils::GetFileName(strFilename)', 'URIUtils::GetFileName(effectiveFilename)'),
        ('StringUtils::Format("{}_{:f}_{:f}{}", strFilename,', 'StringUtils::Format("{}_{:f}_{:f}{}", effectiveFilename,'),
        ('if (strFilename != "arial.ttf")', 'if (effectiveFilename != "arial.ttf")'),
        ('strFontName, strFilename);', 'strFontName, effectiveFilename);'),
        ('fontInfo.fileName = strFilename;', 'fontInfo.fileName = effectiveFilename;'),
    ]
    for old, new in replacements:
        if old not in body:
            raise RuntimeError('LoadTTF expected fragment missing: ' + old)
        body = body.replace(old, new)

    text = text[:start] + body + text[end:]
    return text


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--receipt', type=Path)
    a = p.parse_args()
    src = a.source.resolve()

    files = {
        'gradle': src / 'tools/android/packaging/xbmc/build.gradle.in',
        'render': src / 'xbmc/rendering/RenderSystem.cpp',
        'window_splash': src / 'xbmc/windows/GUIWindowSplash.cpp',
        'font_manager': src / 'xbmc/guilib/GUIFontManager.cpp',
    }
    for path in files.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    before = {name: sha256(path) for name, path in files.items()}
    patch_text(files['gradle'], patch_gradle)
    patch_text(files['render'], patch_render_system)
    patch_text(files['window_splash'], patch_window_splash)
    patch_text(files['font_manager'], patch_font_manager)
    after = {name: sha256(path) for name, path in files.items()}

    # Explicit release gates: this is a contained startup/font-loader change, not
    # a playback/PiP redesign.
    assert 'versionCode 2103106' in files['gradle'].read_text()
    assert 'CAspectRatio::AR_SCALE' not in '\n'.join([
        line for line in files['render'].read_text().splitlines() if 'm_splashImage->SetAspectRatio' in line])
    assert 'CAspectRatio::AR_SCALE' not in '\n'.join([
        line for line in files['window_splash'].read_text().splitlines() if 'm_image->SetAspectRatio' in line])
    assert 'InfinityResolveAndroidSystemFont' in files['font_manager'].read_text()

    if a.receipt:
        a.receipt.parent.mkdir(parents=True, exist_ok=True)
        a.receipt.write_text(json.dumps({
            'release': '1.0.6-consolidated',
            'versionCode': 2103106,
            'versionName': '21.3-Infinity-1.0.6',
            'native_splash': 'AR_KEEP in RenderSystem and GUIWindowSplash',
            'system_font': 'optional Android generic family via runtime API-29 matcher; bundled Noto fallback',
            'changed_source_files': {k: {'before': before[k], 'after': after[k]} for k in files},
            'playback_or_pip_source_changed_by_this_step': False,
        }, indent=2) + '\n')

    print('Infinity 1.0.6 narrow native/source correction applied.')


if __name__ == '__main__':
    main()
