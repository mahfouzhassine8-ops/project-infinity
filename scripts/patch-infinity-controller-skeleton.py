from pathlib import Path
import re

ROOT = Path('/tmp/decoded')

# Find only the real Project Infinity Kodi Main class.
main_candidates = []
for smali_root in ROOT.glob('smali*'):
    main_candidates.extend(smali_root.rglob('Main.smali'))
main_candidates = [p for p in main_candidates if 'projectinfinity/kodi' in str(p).replace('\\', '/')]
if not main_candidates:
    raise SystemExit('Stable 2 Main.smali not found')
MAIN = main_candidates[0]
PKG_DIR = MAIN.parent
main_text = MAIN.read_text()

class_match = re.search(r'^\.class[^\n]*\s(L[^;]+;)', main_text, re.M)
if not class_match:
    raise SystemExit('Could not determine Main descriptor')
MAIN_DESC = class_match.group(1)
PKG_DESC = MAIN_DESC.rsplit('/', 1)[0]
CTRL = f'{PKG_DESC}/InfinityController;'

# SURGICAL DIAGNOSTIC BUILD:
# - creates the permanent central brain class
# - stores the Activity reference only
# - starts NO threads
# - opens NO sockets
# - touches NO PiP APIs
# - changes NO native libraries
controller = f'''.class public final {CTRL}
.super Ljava/lang/Object;
.source "InfinityController.java"

.field private static activity:Landroid/app/Activity;
.field public static volatile isVideoPlaying:Z

.method static constructor <clinit>()V
    .locals 1
    const/4 v0, 0x0
    sput-boolean v0, {CTRL}->isVideoPlaying:Z
    return-void
.end method

.method private constructor <init>()V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static init(Landroid/app/Activity;)V
    .locals 0
    sput-object p0, {CTRL}->activity:Landroid/app/Activity;
    return-void
.end method

.method public static shouldAllowPiP()Z
    .locals 1
    sget-boolean v0, {CTRL}->isVideoPlaying:Z
    return v0
.end method
'''
(PKG_DIR / 'InfinityController.smali').write_text(controller)

# Only one hook: instantiate/store the Activity after NativeActivity's onCreate.
if f'{CTRL}->init(Landroid/app/Activity;)V' not in main_text:
    m = re.search(r'(?ms)^\.method[^\n]* onCreate\(Landroid/os/Bundle;\)V\n.*?^\.end method', main_text)
    if not m:
        raise SystemExit('Main.onCreate(Bundle) not found')
    body = m.group(0)
    super_call = re.search(r'(?m)^\s*invoke-super \{p0, p1\}, L[^;]+;->onCreate\(Landroid/os/Bundle;\)V\s*$', body)
    if not super_call:
        raise SystemExit('Main.onCreate super call not found')
    add = f'\n    invoke-static {{p0}}, {CTRL}->init(Landroid/app/Activity;)V\n'
    body = body[:super_call.end()] + add + body[super_call.end():]
    main_text = main_text[:m.start()] + body + main_text[m.end():]

MAIN.write_text(main_text)
print('Infinity Controller skeleton created: no thread, no socket, no PiP API calls')
print(f'Main: {MAIN}')
print(f'Controller: {PKG_DIR / "InfinityController.smali"}')
