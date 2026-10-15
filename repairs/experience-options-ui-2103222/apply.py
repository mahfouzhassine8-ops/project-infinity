#!/usr/bin/env python3
"""2103222: presentation-only repair for BOTH Choose Your Experience gear menus.

Parent: locked 2103221 Drawer Owner + UI Restore.
Authorized delta:
- Splash.showExperienceCardSettings(String) presentation only.
- Build identity 2103221 -> 2103222.

The option labels, callbacks, routing, drawer ownership, Smart Return, playback,
providers, Health Center behavior, native engine and every unrelated screen are
preserved exactly.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION = 2103222
OLD_VERSION = 2103221
OLD_NAME = '1.0.9-Cobra-Drawer-Owner-UI-Restore-RC1'
NEW_NAME = '1.0.9-Experience-Options-UI-RC1'
SOURCE = 'tools/android/packaging/xbmc/src/'
NATIVE = 'db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b): return hashlib.sha256(b).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v, m):
    if not v:
        raise RuntimeError(m)
def once(s, a, b, label):
    req(s.count(a) == 1, f'{label} anchor drift ({s.count(a)})')
    return s.replace(a, b, 1)
def method_range(s, sig):
    i = s.find(sig); req(i >= 0, 'Missing ' + sig)
    b = s.find('{', i); req(b >= 0, 'Missing method body ' + sig)
    d = 0
    for j in range(b, len(s)):
        if s[j] == '{': d += 1
        elif s[j] == '}':
            d -= 1
            if d == 0:
                return i, j + 1
    raise RuntimeError('Unbalanced ' + sig)
def method(s, sig):
    a, b = method_range(s, sig)
    return s[a:b]
def replace_method(s, sig, new):
    a, b = method_range(s, sig)
    return s[:a] + new.rstrip() + s[b:]

TARGET = 'private void showExperienceCardSettings(String experience)'
PROTECTED_SPLASH = [
    'private void showInfinityExperienceChooser()',
    'private void showStyledInfinityExperienceChooser(ExperienceTheme theme)',
    'private boolean showVisualExperienceScene(ExperienceTheme theme)',
    'private void launchInfinityExperience(String experience)',
]
def method_hashes(s, names):
    return {n: hb(method(s, n).encode()) for n in names}

def patch_splash(path: Path):
    s = path.read_text()
    before_file = hb(s.encode())
    before_target = method(s, TARGET)
    protected_before = method_hashes(s, PROTECTED_SPLASH)

    for token in (
        '"Remember & launch " + label',
        '"Launch " + label + " just this time"',
        '"Ask every time"',
        '"Infinity Health Center"',
        '"Cobra Recovery"',
        'launchInfinityExperience(experience);',
        'showInfinityHealthCenter();',
        'showCobraRecovery();',
        '.remove(INFINITY_EXPERIENCE_DEFAULT).apply();',
    ):
        req(token in before_target, '2103221 chooser contract missing: ' + token)
    req('Smart Return' not in before_target and 'cobra_smart_return' not in before_target,
        'Smart Return unexpectedly present in chooser options')

    replacement = r'''  private void showExperienceCardSettings(String experience)
  {
    final boolean cobra = "live".equals(experience);
    final String title = cobra ? "Cobra options" : "Infinity options";
    final String label = cobra ? "Cobra" : "Infinity";
    final String[] options = cobra ? new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Infinity Health Center",
        "Cobra Recovery"
    } : new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Infinity Health Center"
    };

    // This menu is intentionally self-contained so fixing it cannot restyle any
    // other Cobra/Infinity dialog. Infinity uses the chooser gold accent; Cobra
    // uses the chooser cyan accent. Behavior below is unchanged from 2103221.
    final int accent = cobra ? 0xff35c7d9 : 0xffb59a5a;
    final int text = 0xfff5f7fb;
    final int panelTop = cobra ? 0xff0d1720 : 0xff15130f;
    final int panelBottom = 0xff080d14;

    android.widget.ArrayAdapter<String> adapter =
        new android.widget.ArrayAdapter<String>(this, android.R.layout.simple_list_item_1, options)
        {
          @Override
          public android.view.View getView(int position, android.view.View convertView,
                                           android.view.ViewGroup parent)
          {
            android.widget.TextView row =
                (android.widget.TextView)super.getView(position, convertView, parent);
            row.setTag("experience_options_ui_row");
            row.setTextColor(text);
            row.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 16);
            row.setTypeface(android.graphics.Typeface.create(
                "sans-serif", android.graphics.Typeface.NORMAL));
            row.setLetterSpacing(0.01f);
            row.setIncludeFontPadding(false);
            row.setGravity(android.view.Gravity.CENTER_VERTICAL);
            row.setMinHeight(chooserDp(54));
            row.setPadding(chooserDp(18), chooserDp(2), chooserDp(18), chooserDp(2));

            int focusFill = (accent & 0x00ffffff) | 0x24000000;
            int focusLine = (accent & 0x00ffffff) | 0xb8000000;
            android.graphics.drawable.GradientDrawable normal =
                new android.graphics.drawable.GradientDrawable();
            normal.setColor(android.graphics.Color.TRANSPARENT);
            normal.setCornerRadius(chooserDp(14));
            android.graphics.drawable.GradientDrawable focused =
                new android.graphics.drawable.GradientDrawable();
            focused.setColor(focusFill);
            focused.setCornerRadius(chooserDp(14));
            focused.setStroke(Math.max(1, chooserDp(1)), focusLine);
            android.graphics.drawable.StateListDrawable states =
                new android.graphics.drawable.StateListDrawable();
            states.addState(new int[]{android.R.attr.state_pressed}, focused);
            states.addState(new int[]{android.R.attr.state_focused}, focused);
            states.addState(new int[]{android.R.attr.state_selected}, focused);
            states.addState(new int[]{}, normal);
            row.setBackground(states);
            return row;
          }
        };

    final android.app.AlertDialog dialog =
        new android.app.AlertDialog.Builder(this, android.R.style.Theme_Material_Dialog_Alert)
        .setTitle(title)
        .setAdapter(adapter, (dialogInterface, which) -> {
          if (which == 0)
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .putString(INFINITY_EXPERIENCE_DEFAULT, experience).apply();
            launchInfinityExperience(experience);
          }
          else if (which == 1)
          {
            launchInfinityExperience(experience);
          }
          else if (which == 2)
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .remove(INFINITY_EXPERIENCE_DEFAULT).apply();
            android.widget.Toast.makeText(this,
                "Infinity will ask which experience to open next time.",
                android.widget.Toast.LENGTH_SHORT).show();
          }
          else if (which == 3)
          {
            showInfinityHealthCenter();
          }
          else if (which == 4 && cobra)
          {
            showCobraRecovery();
          }
        })
        .setNegativeButton("Cancel", null)
        .create();

    dialog.setOnShowListener(ignored -> {
      android.view.Window window = dialog.getWindow();
      if (window != null)
      {
        window.getDecorView().setTag("experience_options_ui_dialog");
        android.graphics.drawable.GradientDrawable surface =
            new android.graphics.drawable.GradientDrawable(
                android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{panelTop, panelBottom});
        surface.setCornerRadius(chooserDp(24));
        surface.setStroke(Math.max(1, chooserDp(1)),
            (accent & 0x00ffffff) | 0x8f000000);
        window.setBackgroundDrawable(surface);
        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_DIM_BEHIND);
        window.setDimAmount(0.48f);
        int available = getResources().getDisplayMetrics().widthPixels - chooserDp(32);
        window.setLayout(Math.min(available, chooserDp(460)),
            android.view.WindowManager.LayoutParams.WRAP_CONTENT);
      }

      int titleId = getResources().getIdentifier("alertTitle", "id", "android");
      android.view.View titleView = dialog.findViewById(titleId);
      if (titleView instanceof android.widget.TextView)
      {
        android.widget.TextView heading = (android.widget.TextView)titleView;
        heading.setTextColor(text);
        heading.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 20);
        heading.setTypeface(android.graphics.Typeface.create(
            "sans-serif-medium", android.graphics.Typeface.NORMAL));
        heading.setLetterSpacing(0.015f);
      }

      android.widget.ListView list = dialog.getListView();
      if (list != null)
      {
        list.setDivider(new android.graphics.drawable.ColorDrawable(
            android.graphics.Color.TRANSPARENT));
        list.setDividerHeight(chooserDp(4));
        list.setPadding(chooserDp(10), chooserDp(4), chooserDp(10), chooserDp(4));
        list.setClipToPadding(false);
        list.setSelector(new android.graphics.drawable.ColorDrawable(
            android.graphics.Color.TRANSPARENT));
      }

      android.widget.Button cancel =
          dialog.getButton(android.app.AlertDialog.BUTTON_NEGATIVE);
      if (cancel != null)
      {
        cancel.setTextColor(accent);
        cancel.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 14);
        cancel.setTypeface(android.graphics.Typeface.create(
            "sans-serif-medium", android.graphics.Typeface.NORMAL));
        cancel.setLetterSpacing(0.04f);
      }
    });
    dialog.show();
  }'''

    for token in (
        '"Remember & launch " + label',
        '"Launch " + label + " just this time"',
        '"Ask every time"',
        '"Infinity Health Center"',
        '"Cobra Recovery"',
        'launchInfinityExperience(experience);',
        'showInfinityHealthCenter();',
        'showCobraRecovery();',
        '.remove(INFINITY_EXPERIENCE_DEFAULT).apply();',
    ):
        req(token in replacement, 'replacement behavior drift: ' + token)
    req('Smart Return' not in replacement and 'cobra_smart_return' not in replacement,
        'Smart Return leaked into chooser options replacement')

    s = replace_method(s, TARGET, replacement)
    req(method_hashes(s, PROTECTED_SPLASH) == protected_before,
        'Protected chooser/routing methods changed')
    path.write_text(s)
    return {
        'splash_before_sha256': before_file,
        'splash_after_sha256': sha(path),
        'options_method_before_sha256': hb(before_target.encode()),
        'options_method_after_sha256': hb(method(s, TARGET).encode()),
        'protected_splash_methods_sha256': protected_before,
    }

def patch_identity(shell: Path):
    gradle = shell / 'tools/android/packaging/xbmc/build.gradle.in'
    g = gradle.read_text()
    g = once(g, f'versionCode {OLD_VERSION}', f'versionCode {VERSION}', 'versionCode')
    g = once(g, 'versionName "' + OLD_NAME + '"',
             'versionName "' + NEW_NAME + '"', 'versionName')
    gradle.write_text(g)

    runtime = Path('scripts/infinity_background_resume.py')
    r = runtime.read_text()
    r = once(r, f'VERSION_CODE = {OLD_VERSION}', f'VERSION_CODE = {VERSION}', 'runtime code')
    r = once(r, "RELEASE = '" + OLD_NAME + "'",
             "RELEASE = '" + NEW_NAME + "'", 'runtime name')
    runtime.write_text(r)

    pack = Path('scripts/package_background_resume.py')
    p = pack.read_text()
    old = 'Infinity-' + OLD_NAME
    new = 'Infinity-' + NEW_NAME
    req(p.count(old) >= 2, 'packager identity drift')
    pack.write_text(p.replace(old, new))
    return gradle

def apply(shell: Path):
    receipt_path = Path('engine/background-resume-source.json')
    receipt = json.loads(receipt_path.read_text())
    req(receipt.get('version_code') == OLD_VERSION and receipt.get('version_name') == OLD_NAME,
        'Expected exact locked 2103221 replay')
    req(receipt.get('native_engine_sha256') == NATIVE, 'Native engine receipt drift')

    splash = shell / (SOURCE + 'Splash.java.in')
    activity = shell / (SOURCE + 'InfinityLiveActivity.java.in')
    smart = shell / (SOURCE + 'CobraSmartReturn.java.in')
    main = shell / (SOURCE + 'Main.java.in')
    renderer = shell / (SOURCE + 'CobraVisualRenderer.java.in')
    for p in (splash, activity, smart, main, renderer):
        req(p.is_file(), 'Missing ' + str(p))

    protected_files = {
        'activity': sha(activity),
        'smart_return': sha(smart),
        'main': sha(main),
        'visual_renderer': sha(renderer),
    }

    scope = patch_splash(splash)
    gradle = patch_identity(shell)

    req(sha(activity) == protected_files['activity'], 'Activity changed')
    req(sha(smart) == protected_files['smart_return'], 'Smart Return changed')
    req(sha(main) == protected_files['main'], 'Kodi Main changed')
    req(sha(renderer) == protected_files['visual_renderer'], 'Global dialog renderer changed')

    for name in (
        SOURCE + 'Splash.java.in',
        SOURCE + 'InfinityLiveActivity.java.in',
        SOURCE + 'CobraSmartReturn.java.in',
        SOURCE + 'Main.java.in',
    ):
        req(name in receipt['files'], 'Receipt missing ' + name)
        receipt['files'][name]['after'] = sha(shell / name)
    rel = 'tools/android/packaging/xbmc/build.gradle.in'
    receipt['files'][rel]['after'] = sha(gradle)

    receipt.update(
        version_code=VERSION,
        version_name=NEW_NAME,
        source_parent=OLD_VERSION,
        candidate_locked=False,
        physical_device_verified=False,
        runtime_device_tested=False,
        native_engine_rebuilt=False,
        native_engine_reused_from_2103209=True,
        native_engine_sha256=NATIVE,
        experience_options_ui_fixed=True,
        infinity_options_ui_fixed=True,
        cobra_options_ui_fixed=True,
        chooser_option_actions_unchanged=True,
        chooser_option_labels_unchanged=True,
        chooser_main_screen_unchanged=True,
        smart_return_untouched=True,
        drawer_owner_untouched=True,
        active_section_lifecycle_untouched=True,
        playback_unchanged=True,
        providers_unchanged=True,
        health_center_behavior_unchanged=True,
        global_dialog_renderer_untouched=True,
    )
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')

    for name, row in receipt['files'].items():
        req(sha(shell / name) == row['after'], 'Receipt drift ' + name)

    Path('audit222').mkdir(exist_ok=True)
    scope.update({
        'build': VERSION,
        'parent': OLD_VERSION,
        'parent_locked_branch': 'locked-infinity-cobra-2103221-drawer-owner-ui-restore-passed',
        'authorized_delta': 'showExperienceCardSettings presentation + build identity only',
        'both_gears_fixed': True,
        'infinity_accent': '#B59A5A',
        'cobra_accent': '#35C7D9',
        'option_actions_unchanged': True,
        'option_labels_unchanged': True,
        'smart_return_untouched': True,
        'drawer_owner_untouched': True,
        'protected_files_sha256': protected_files,
        'native_engine_sha256': NATIVE,
        'native_engine_rebuilt': False,
        'status': 'TEST CANDIDATE',
    })
    Path('audit222/scope.json').write_text(json.dumps(scope, indent=2, sort_keys=True) + '\n')
    print('PASS: 2103222 changes only both Choose Your Experience gear-menu presentation; behavior untouched')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--shell', type=Path, required=True)
    a = p.parse_args()
    apply(a.shell)

if __name__ == '__main__':
    main()
