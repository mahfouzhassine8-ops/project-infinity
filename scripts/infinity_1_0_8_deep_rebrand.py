#!/usr/bin/env python3
"""Deep user-facing Kodi -> Infinity rebrand for Infinity 1.0.8 / Kodi 21.3.

`source` changes only presentation-owned Android/source resources: app label,
adaptive + themed launcher icons, day/night Android splash, launch activity,
shared media artwork, banner/notification/recommendation art, and native splash
contain behavior. Package/class/database/API identifiers are deliberately left
alone.

`apk` runs after the normal Infinity upper-layer repack. It re-asserts shared
Infinity artwork and carefully changes user-facing English labels / web chrome,
while byte-preserving DEX, resources.arsc, AndroidManifest.xml and libkodi.so.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

RELEASE = "1.0.8-Deep-Rebrand-1"
VERSION_CODE = 2103122
PACKAGE_ID = "com.projectinfinity.kodi"
CORE_PO = "assets/addons/resource.language.en_gb/resources/strings.po"
WEB = "assets/addons/webinterface.default/"
LEGAL = ("kodi.tv", "team kodi", "kodi foundation", "xbmc foundation", "copyright", "gpl", "license", "licensed", "spdx", "501(c)(3)")
PROTECTED = ("AndroidManifest.xml", "resources.arsc", "lib/arm64-v8a/libkodi.so")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def convert(*args: str) -> None:
    exe = shutil.which("convert") or shutil.which("magick")
    if not exe:
        raise RuntimeError("ImageMagick is required")
    run(exe, *args)


def font() -> str:
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(p).is_file():
            return p
    raise RuntimeError("Install fonts-dejavu-core")


def app_icon(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    inset = max(2, round(size * .035)); radius = round(size * .215); stroke = max(2, round(size * .012))
    convert("-size", f"{size}x{size}", "gradient:#04101d-#071c2d",
            "-fill", "none", "-stroke", "#20bfff", "-strokewidth", str(stroke),
            "-draw", f"roundrectangle {inset},{inset} {size-inset-1},{size-inset-1} {radius},{radius}",
            "-font", font(), "-gravity", "center", "-fill", "#20aaff", "-stroke", "none",
            "-pointsize", str(round(size * .55)), "-annotate", "+0-4", "∞", str(path))


def transparent_symbol(path: Path, size: int, monochrome: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fill = "white" if monochrome else "#20aaff"
    convert("-size", f"{size}x{size}", "xc:none", "-font", font(), "-gravity", "center",
            "-fill", fill, "-pointsize", str(round(size * .52)), "-annotate", "+0-4", "∞", str(path))


def adaptive_background(path: Path, size: int = 432) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    inset = round(size * .10); radius = round(size * .19)
    convert("-size", f"{size}x{size}", "gradient:#03101c-#071c2d",
            "-fill", "none", "-stroke", "#20bfff", "-strokewidth", "5",
            "-draw", f"roundrectangle {inset},{inset} {size-inset},{size-inset} {radius},{radius}", str(path))


def splash(path: Path, dark: bool, jpeg: bool = False, size: str = "1920x1080") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bg = "#000000" if dark else "#f7fafd"; fg = "#f7fbff" if dark else "#0c1c2b"; sub = "#9cc6dc" if dark else "#506a80"
    convert("-size", size, f"xc:{bg}",
            "-fill", "#123e68", "-draw", "circle 960,520 960,160", "-blur", "0x120",
            "-font", font(), "-gravity", "center", "-fill", "#20aaff", "-pointsize", "330", "-annotate", "+0-160", "∞",
            "-fill", fg, "-pointsize", "76", "-annotate", "+0+125", "I N F I N I T Y",
            "-fill", sub, "-pointsize", "24", "-annotate", "+0+245", "M E D I A   W I T H O U T   L I M I T S",
            "-quality", "95", str(path))


def wordmark(path: Path, dark: bool = True, size: str = "960x240") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fg = "#f7fbff" if dark else "#0c1c2b"
    convert("-size", size, "xc:none", "-font", font(), "-gravity", "west",
            "-fill", "#20aaff", "-pointsize", "150", "-annotate", "+20+0", "∞",
            "-fill", fg, "-pointsize", "52", "-annotate", "+260+0", "I N F I N I T Y", str(path))


def banner(path: Path, size: str = "320x180") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    convert("-size", size, "gradient:#03101c-#071c2d", "-fill", "none", "-stroke", "#20bfff", "-strokewidth", "3",
            "-draw", "roundrectangle 4,4 315,175 26,26", "-font", font(), "-fill", "#20aaff", "-stroke", "none",
            "-pointsize", "92", "-gravity", "west", "-annotate", "+20+0", "∞",
            "-fill", "#f7fbff", "-pointsize", "26", "-annotate", "+130+0", "INFINITY", str(path))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one exact match, found {n}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, repl: str, label: str) -> str:
    out, n = re.subn(pattern, repl, text, count=1)
    if n != 1:
        raise RuntimeError(f"{label}: expected one match, found {n}")
    return out


def patch_manifest(path: Path) -> None:
    text = path.read_text()
    owners = ('android:icon="@drawable/project_infinity_icon"', 'android:icon="@drawable/ic_launcher"')
    found = [x for x in owners if x in text]
    if len(found) != 1:
        raise RuntimeError(f"unexpected icon owner: {found}")
    text = text.replace(found[0], 'android:icon="@mipmap/ic_launcher"', 1)
    if 'android:roundIcon="@drawable/project_infinity_icon"' in text:
        text = text.replace('android:roundIcon="@drawable/project_infinity_icon"', 'android:roundIcon="@mipmap/ic_launcher_round"', 1)
    elif 'android:roundIcon="@drawable/ic_launcher"' in text:
        text = text.replace('android:roundIcon="@drawable/ic_launcher"', 'android:roundIcon="@mipmap/ic_launcher_round"', 1)
    elif 'android:roundIcon=' not in text:
        text = text.replace('android:icon="@mipmap/ic_launcher"', 'android:icon="@mipmap/ic_launcher"\n        android:roundIcon="@mipmap/ic_launcher_round"', 1)
    else:
        raise RuntimeError("unexpected round icon owner")
    if 'android:label="@string/app_name"' not in text:
        raise RuntimeError("application label owner changed")
    path.write_text(text)


def patch_android_text(src: Path) -> None:
    gradle = src / "tools/android/packaging/xbmc/build.gradle.in"
    text = gradle.read_text(); text = regex_once(text, r"versionCode\s+\d+", f"versionCode {VERSION_CODE}", "versionCode"); text = regex_once(text, r'versionName\s+"[^"]+"', f'versionName "{RELEASE}"', "versionName"); gradle.write_text(text)
    patch_manifest(src / "tools/android/packaging/xbmc/AndroidManifest.xml.in")

    strings = src / "tools/android/packaging/xbmc/strings.xml.in"; root = ET.fromstring(strings.read_text())
    nodes = {n.attrib.get("name"): n for n in root.findall("string")}
    for key in ("app_name", "search_hint"):
        if key not in nodes: raise RuntimeError(f"missing Android string {key}")
        nodes[key].text = "Infinity"
    strings.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))

    colors = src / "tools/android/packaging/xbmc/colors.xml.in"; root = ET.fromstring(colors.read_text())
    wanted = {"principal_color":"#24B7FF", "recommendation_color":"#24B7FF", "infinity_splash_background":"#F7FAFD", "infinity_splash_text":"#0C1C2B", "infinity_icon_background":"#061522"}
    for name, value in wanted.items():
        node = next((n for n in root.findall("color") if n.attrib.get("name") == name), None)
        if node is None: node = ET.SubElement(root, "color", {"name":name})
        node.text = value
    colors.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))

    layout = src / "tools/android/packaging/xbmc/res/layout/activity_splash.xml"; text = layout.read_text()
    text = replace_once(text, 'android:background="@android:color/black"', 'android:background="@color/infinity_splash_background"', "splash background")
    text = replace_once(text, 'android:scaleType="centerCrop"', 'android:scaleType="fitCenter"', "splash fit")
    if 'android:contentDescription=' not in text:
        text = replace_once(text, 'android:src="@drawable/applaunch_screen" />', 'android:src="@drawable/applaunch_screen"\n        android:contentDescription="@string/app_name" />', "splash accessibility")
    text = replace_once(text, 'android:textColor="@android:color/white"', 'android:textColor="@color/infinity_splash_text"', "splash text")
    text = text.replace('android:textSize="16dp"', 'android:textSize="16sp"'); ET.fromstring(text); layout.write_text(text)

    java = src / "tools/android/packaging/xbmc/src/Splash.java.in"; text = java.read_text()
    visible = {
        'dialog.setTitle("Info");':'dialog.setTitle("Infinity");',
        'dialog.setButton(DialogInterface.BUTTON_NEUTRAL, "continue"':'dialog.setButton(DialogInterface.BUTTON_NEUTRAL, "Continue"',
        'mSplash.mTextView.setText("Asking for permissions...");':'mSplash.mTextView.setText("Preparing Infinity permissions...");',
        'mErrorMsg = "Permission denied!! Exiting...";':'mErrorMsg = "Permission denied. Infinity cannot continue.";',
        'mSplash.mTextView.setText("Clearing cache...");':'mSplash.mTextView.setText("Refreshing Infinity...");',
        'mSplash.mTextView.setText("Waiting for external storage...");':'mSplash.mTextView.setText("Waiting for storage...");',
        'mSplash.mTextView.setText("External storage OK...");':'mSplash.mTextView.setText("Storage ready...");',
        'mSplash.mTextView.setText("Starting @APP_NAME@...");':'mSplash.mTextView.setText("Starting Infinity...");',
        'mSplash.mTextView.setText("Preparing for first run. Please wait...");':'mSplash.mTextView.setText("Preparing Infinity for first run. Please wait...");',
    }
    for old, new in visible.items(): text = replace_once(text, old, new, "Splash.java visible branding")
    java.write_text(text)


def native_splash_keep(path: Path) -> None:
    text = path.read_text(); lines = [x for x in text.splitlines() if "SetAspectRatio" in x and ("splash" in x.lower() or "m_image" in x)]
    joined = "\n".join(lines)
    if "AR_KEEP" in joined: return
    if "AR_SCALE" not in joined: raise RuntimeError(f"native splash aspect owner changed: {path}")
    path.write_text(text.replace("CAspectRatio::AR_SCALE", "CAspectRatio::AR_KEEP", 1))


def qualified_res(src: Path) -> None:
    res = src / "tools/android/packaging/xbmc/res"
    (res / "values-night").mkdir(parents=True, exist_ok=True)
    (res / "values-night/infinity_colors.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n  <color name="infinity_splash_background">#000000</color>\n  <color name="infinity_splash_text">#F7FBFF</color>\n  <color name="infinity_icon_background">#061522</color>\n</resources>\n')
    theme = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n  <style name="AppTheme" parent="android:Theme.NoTitleBar">\n    <item name="android:colorPrimary">@color/principal_color</item>\n    <item name="android:windowSplashScreenBackground">@color/infinity_splash_background</item>\n    <item name="android:windowSplashScreenAnimatedIcon">@drawable/infinity_splash_icon</item>\n    <item name="android:windowSplashScreenIconBackgroundColor">@android:color/transparent</item>\n  </style>\n</resources>\n'
    for q in ("values-v31", "values-night-v31"):
        (res / q).mkdir(parents=True, exist_ok=True); (res / q / "infinity_splash_theme.xml").write_text(theme)
    v26 = '<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n  <background android:drawable="@drawable/infinity_icon_background_bitmap" />\n  <foreground android:drawable="@drawable/infinity_icon_foreground" />\n</adaptive-icon>\n'
    v33 = v26.replace('</adaptive-icon>', '  <monochrome android:drawable="@drawable/infinity_icon_monochrome" />\n</adaptive-icon>')
    for q, xml in (("mipmap-anydpi-v26", v26), ("mipmap-anydpi-v33", v33)):
        (res/q).mkdir(parents=True, exist_ok=True); (res/q/"ic_launcher.xml").write_text(xml); (res/q/"ic_launcher_round.xml").write_text(xml)


def art(src: Path) -> None:
    media = src / "media"; splash(media/"applaunch_screen.png", False); splash(media/"infinity_launch_dark.png", True); splash(media/"splash.jpg", True, True)
    wordmark(media/"vendor_logo.png", True); app_icon(media/"vendor_icon.png", 512); banner(media/"banner.png", "480x270")
    for n in (16,32,48,80,120,256): app_icon(media/f"icon{n}x{n}.png", n)
    res = src / "tools/android/packaging/xbmc/res"; splash(res/"drawable-night/applaunch_screen.png", True); splash(res/"drawable-night-xxxhdpi/applaunch_screen.png", True)
    adaptive_background(res/"drawable-nodpi/infinity_icon_background_bitmap.png"); transparent_symbol(res/"drawable-nodpi/infinity_icon_foreground.png", 432); transparent_symbol(res/"drawable-nodpi/infinity_icon_monochrome.png", 432, True); transparent_symbol(res/"drawable-nodpi/infinity_splash_icon.png", 288); transparent_symbol(res/"drawable/notif_icon.png", 96, True)
    for q,n in {"mdpi":48,"hdpi":72,"xhdpi":96,"xxhdpi":144,"xxxhdpi":192}.items(): app_icon(res/f"mipmap-{q}/ic_launcher.png",n); app_icon(res/f"mipmap-{q}/ic_launcher_round.png",n)
    legacy = src / "tools/android/packaging/media"
    for q,n in {"ldpi":36,"mdpi":48,"hdpi":72,"xhdpi":96,"xxhdpi":144,"xxxhdpi":192}.items(): app_icon(legacy/f"drawable-{q}/ic_launcher.png",n)
    banner(legacy/"drawable-xhdpi/banner.png")


def makefile_night(src: Path) -> None:
    path = src / "tools/android/packaging/Makefile.in"; text = path.read_text(); anchor='\tcp -fp $(CMAKE_SOURCE_DIR)/media/applaunch_screen.png xbmc/res/drawable/\n'
    add=anchor+'\tmkdir -p xbmc/res/drawable-night xbmc/res/drawable-night-xxxhdpi\n\tcp -fp $(CMAKE_SOURCE_DIR)/media/infinity_launch_dark.png xbmc/res/drawable-night/applaunch_screen.png\n\tcp -fp $(CMAKE_SOURCE_DIR)/media/infinity_launch_dark.png xbmc/res/drawable-night-xxxhdpi/applaunch_screen.png\n'
    text=replace_once(text,anchor,add,"night splash packaging"); path.write_text(text)


def verify_source(src: Path) -> None:
    assert f"versionCode {VERSION_CODE}" in (src/"tools/android/packaging/xbmc/build.gradle.in").read_text()
    assert f'versionName "{RELEASE}"' in (src/"tools/android/packaging/xbmc/build.gradle.in").read_text()
    manifest=(src/"tools/android/packaging/xbmc/AndroidManifest.xml.in").read_text(); assert '@mipmap/ic_launcher' in manifest and '@mipmap/ic_launcher_round' in manifest
    strings=(src/"tools/android/packaging/xbmc/strings.xml.in").read_text(); assert '>Infinity<' in strings and '@APP_NAME@' not in strings
    layout=(src/"tools/android/packaging/xbmc/res/layout/activity_splash.xml").read_text(); assert 'fitCenter' in layout and 'infinity_splash_background' in layout
    java=(src/"tools/android/packaging/xbmc/src/Splash.java.in").read_text(); assert 'Starting Infinity...' in java and 'Preparing Infinity for first run' in java
    for rel in ("media/applaunch_screen.png","media/infinity_launch_dark.png","media/splash.jpg","media/vendor_logo.png","media/vendor_icon.png","tools/android/packaging/xbmc/res/mipmap-anydpi-v26/ic_launcher.xml","tools/android/packaging/xbmc/res/mipmap-anydpi-v33/ic_launcher.xml","tools/android/packaging/xbmc/res/values-v31/infinity_splash_theme.xml","tools/android/packaging/xbmc/res/values-night-v31/infinity_splash_theme.xml"):
        if not (src/rel).is_file(): raise RuntimeError(f"missing branding resource {rel}")


def source_phase(src: Path, receipt: Path) -> None:
    src=src.resolve(); tracked=("tools/android/packaging/xbmc/build.gradle.in","tools/android/packaging/xbmc/AndroidManifest.xml.in","tools/android/packaging/xbmc/strings.xml.in","tools/android/packaging/xbmc/colors.xml.in","tools/android/packaging/xbmc/res/layout/activity_splash.xml","tools/android/packaging/xbmc/src/Splash.java.in","tools/android/packaging/Makefile.in","xbmc/windows/GUIWindowSplash.cpp","xbmc/rendering/RenderSystem.cpp")
    before={p:file_sha(src/p) for p in tracked}
    patch_android_text(src); makefile_night(src); native_splash_keep(src/"xbmc/windows/GUIWindowSplash.cpp"); native_splash_keep(src/"xbmc/rendering/RenderSystem.cpp"); qualified_res(src); art(src); verify_source(src)
    receipt.parent.mkdir(parents=True,exist_ok=True); receipt.write_text(json.dumps({"schema":1,"release":RELEASE,"version_code":VERSION_CODE,"package_id":PACKAGE_ID,"internal_kodi_identifiers_renamed":False,"playback_refresh_bridge_redesigned":False,"before":before,"after":{p:file_sha(src/p) for p in tracked}},indent=2,sort_keys=True)+"\n")
    print("PASS: Infinity deep source rebrand applied")


def po_rebrand(text: str) -> tuple[str,int]:
    parts=re.split(r"(\n\s*\n)",text); count=0
    for i in range(0,len(parts),2):
        block=parts[i]; low=block.lower()
        if "kodi" not in low or any(x in low for x in LEGAL): continue
        out=[]
        for line in block.splitlines():
            if line.startswith("msgid ") or line.startswith("msgstr ") or line.startswith('"'):
                count += len(re.findall(r"\bKodi\b",line)); line=re.sub(r"\bKodi\b","Infinity",line)
            out.append(line)
        parts[i]="\n".join(out)
    return "".join(parts),count


def image_bytes(kind: str, dark: bool=True, size: int|None=None) -> bytes:
    with tempfile.TemporaryDirectory(prefix="infinity-art-") as td:
        p=Path(td)/("art.jpg" if kind=="splash-jpg" else "art.png")
        if kind=="splash-jpg": splash(p,True,True)
        elif kind=="splash": splash(p,dark)
        elif kind=="wordmark": wordmark(p,dark)
        elif kind=="banner": banner(p,"480x270")
        else: app_icon(p,size or 256)
        return p.read_bytes()


def apk_changes(z: zipfile.ZipFile) -> tuple[dict[str,bytes],dict]:
    changes={}; report={"po_replacements":0,"images":[],"web_text":[]}
    media={"assets/media/applaunch_screen.png":image_bytes("splash",False),"assets/media/splash.jpg":image_bytes("splash-jpg"),"assets/media/vendor_logo.png":image_bytes("wordmark",True),"assets/media/vendor_icon.png":image_bytes("icon",size=512),"assets/media/banner.png":image_bytes("banner")}
    for n in (16,32,48,80,120,256): media[f"assets/media/icon{n}x{n}.png"]=image_bytes("icon",size=n)
    web={WEB+"themes/base/images/logo.png":image_bytes("wordmark",False),WEB+"images/splash_hi.png":image_bytes("splash",False),WEB+"favicon.png":image_bytes("icon",size=64),WEB+"icon.png":image_bytes("icon",size=256),WEB+"icon-128.png":image_bytes("icon",size=128),WEB+"icon-144.png":image_bytes("icon",size=144),WEB+"icon-152.png":image_bytes("icon",size=152),WEB+"icon-192.png":image_bytes("icon",size=192)}
    for name,data in {**media,**web}.items():
        if name in z.namelist(): changes[name]=data; report["images"].append(name)
    if CORE_PO in z.namelist():
        before=z.read(CORE_PO).decode(); after,n=po_rebrand(before)
        if after!=before: changes[CORE_PO]=after.encode(); report["po_replacements"]=n
    addon=WEB+"addon.xml"
    if addon in z.namelist():
        root=ET.fromstring(z.read(addon)); changed=False
        for tag in ("summary","description","disclaimer"):
            for node in root.findall(f".//{tag}"):
                if node.text and "Kodi" in node.text and not any(x in node.text.lower() for x in LEGAL): node.text=re.sub(r"\bKodi\b","Infinity",node.text); changed=True
        if changed: changes[addon]=ET.tostring(root,encoding="utf-8",xml_declaration=True); report["web_text"].append(addon)
    index=WEB+"index.html"
    if index in z.namelist():
        text=z.read(index).decode(); after=re.sub(r"(<title>[^<]*?)Kodi([^<]*</title>)",r"\1Infinity\2",text,flags=re.I)
        if after!=text: changes[index]=after.encode(); report["web_text"].append(index)
    return changes,report


def signing(name: str) -> bool:
    u=name.upper(); return u.startswith("META-INF/") and (u.endswith((".RSA",".DSA",".EC",".SF")) or u.endswith("MANIFEST.MF"))


def verify_apk(apk: Path) -> None:
    with zipfile.ZipFile(apk) as z:
        for n in ("assets/media/splash.jpg","assets/media/vendor_logo.png","assets/media/vendor_icon.png",CORE_PO):
            if n not in z.namelist(): raise RuntimeError(f"missing branded APK member {n}")
        po=z.read(CORE_PO).decode()
        for old in ('msgid "About Kodi"','msgid "Kodi media center"','msgid "Use Kodi"'):
            if old in po: raise RuntimeError(f"unbranded UI label remains: {old}")
        if 'msgid "About Infinity"' not in po: raise RuntimeError("Infinity About label missing")
        if "Kodi Foundation" not in po: raise RuntimeError("required Kodi legal attribution was removed")


def apk_phase(inp: Path, outp: Path, receipt: Path) -> None:
    if outp.exists(): raise RuntimeError(f"refusing to overwrite {outp}")
    with zipfile.ZipFile(inp) as src:
        protected={n:sha(src.read(n)) for n in PROTECTED if n in src.namelist()}; dex={n:sha(src.read(n)) for n in src.namelist() if re.fullmatch(r"classes\d*\.dex",n)}; changes,report=apk_changes(src)
        if not changes: raise RuntimeError("no APK branding changes produced")
        with zipfile.ZipFile(outp,"w",allowZip64=True) as dst:
            for item in src.infolist():
                if signing(item.filename) or item.filename in changes: continue
                dst.writestr(item,src.read(item.filename))
            for name,data in changes.items(): dst.writestr(name,data,compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(outp) as z:
        if protected!={n:sha(z.read(n)) for n in protected}: raise RuntimeError("compiled protected member changed")
        if dex!={n:sha(z.read(n)) for n in dex}: raise RuntimeError("DEX changed in APK branding phase")
    verify_apk(outp); receipt.write_text(json.dumps({"schema":1,"release":RELEASE,"version_code":VERSION_CODE,"input_sha256":file_sha(inp),"output_sha256":file_sha(outp),"changed_members":sorted(changes),"protected_compiled_members_preserved":True,"dex_preserved":True,"report":report},indent=2,sort_keys=True)+"\n"); print(f"PASS: {len(changes)} APK branding members updated; engine preserved")


def main() -> None:
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("source"); a.add_argument("--source",type=Path,required=True); a.add_argument("--receipt",type=Path,required=True)
    a=sp.add_parser("verify-source"); a.add_argument("--source",type=Path,required=True)
    a=sp.add_parser("apk"); a.add_argument("--input",type=Path,required=True); a.add_argument("--output",type=Path,required=True); a.add_argument("--receipt",type=Path,required=True)
    a=sp.add_parser("verify-apk"); a.add_argument("--apk",type=Path,required=True)
    args=p.parse_args()
    if args.cmd=="source": source_phase(args.source,args.receipt)
    elif args.cmd=="verify-source": verify_source(args.source); print("PASS: source verification")
    elif args.cmd=="apk": apk_phase(args.input,args.output,args.receipt)
    else: verify_apk(args.apk); print("PASS: APK verification")

if __name__=="__main__": main()
