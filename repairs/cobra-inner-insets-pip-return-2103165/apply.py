#!/usr/bin/env python3
"""2103165 Android-shell follow-up over the exact locked 2103164 playback-stability source.

Scope is deliberately narrow:
- general/browse surfaces show the Android status bar and re-apply insets after Fold/PiP transitions;
- fullscreen video/multiview alone own fullscreen status-bar hiding;
- launching Infinity while a PiP/fullscreen session exists routes back to Cobra browsing,
  while tapping/expanding the native PiP window without a launcher intent keeps fullscreen;
- the approved/locked player chrome, transport order, drawer, track UI and lock UI are protected.
"""
from pathlib import Path
import argparse, hashlib, json, re

ROOT = Path(__file__).resolve().parent
REL = Path("tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in")
BASE_LOCK = "d9819b9823ff281f874daaa2bf91fdac1613aeb1"

def sha_bytes(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()

def once(text, old, new):
    count = text.count(old)
    if count != 1:
        raise RuntimeError("Exact anchor drift (%d): %r" % (count, old[:180]))
    return text.replace(old, new, 1)

def method_matches(text, name):
    return list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        + re.escape(name) + r'\s*\(', text, re.M))

def method_span(text, name):
    matches = method_matches(text, name)
    if len(matches) != 1:
        raise RuntimeError("Method cardinality %s = %d" % (name, len(matches)))
    start = matches[0].start()
    brace = text.index("{", matches[0].end())
    depth = 0
    quote = None
    escape = False
    line = False
    block = False
    i = brace
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if line:
            if c == "\n":
                line = False
        elif block:
            if c == "*" and n == "/":
                block = False
                i += 1
        elif quote:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
        elif c == "/" and n == "/":
            line = True
            i += 1
        elif c == "/" and n == "*":
            block = True
            i += 1
        elif c in ('"', "'"):
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise RuntimeError("Unclosed method " + name)

def method_text(text, name):
    a, b = method_span(text, name)
    return text[a:b]

def edit_method(text, name, old, new):
    a, b = method_span(text, name)
    return text[:a] + once(text[a:b], old, new) + text[b:]

def prepend_method(text, name, code):
    a, b = method_span(text, name)
    block = text[a:b]
    brace = block.index("{") + 1
    block = block[:brace] + "\n" + code.rstrip() + block[brace:]
    return text[:a] + block + text[b:]

def append_method_body(text, name, code):
    a, b = method_span(text, name)
    block = text[a:b]
    pos = block.rfind("}")
    line_start = block.rfind("\n", 0, pos)
    if line_start < 0 or block[line_start + 1:pos].strip():
        raise RuntimeError("Unexpected closing-brace layout in " + name)
    block = block[:line_start + 1] + code.rstrip() + "\n" + block[line_start + 1:]
    return text[:a] + block + text[b:]

def append_class(text, block):
    pos = text.rfind("\n}")
    if pos < 0:
        raise RuntimeError("Class closing brace missing")
    return text[:pos] + "\n" + block.rstrip() + "\n" + text[pos:]

def normalize_open_player(block):
    return block.replace("    cobraApplySystemBarsForSurface();\n", "", 1)

def apply(source, receipt_path, out):
    receipt = json.loads(Path(receipt_path).read_text())
    if receipt.get("version_code") != 2103164:
        raise RuntimeError("Expected exact locked 2103164 source receipt")
    src = Path(source) / REL
    before_bytes = src.read_bytes()
    expected = receipt.get("files", {}).get(str(REL), {}).get("after")
    if not expected or sha_bytes(before_bytes) != expected:
        raise RuntimeError("Locked 2103164 Activity identity mismatch")
    before = before_bytes.decode()

    # Protect the player that the user already approved/locked. These methods are not repair targets.
    protected = [
        "cobraBuildPlayerChrome",
        "showCobraPlayerDrawer",
        "showPlayerSettingsDrawer",
        "showTrackChooser",
        "lockCobraPlayer",
        "toggleCobraPlayerPlayPause",
        "cobraPreviewPanel",
    ]
    player_before = {name: sha_bytes(method_text(before, name)) for name in protected}
    open_before = method_text(before, "openPlayerOverlay")
    chrome = method_text(before, "cobraBuildPlayerChrome")
    required_player_tokens = [
        "cobra_player_refined_chrome",
        "Previous channel",
        "Next channel",
        "Lock controls",
        "cobra_player_play_pause",
        "Channels",
        "Display",
        "Multi-View",
        "More",
        "mCobraPlayerProgramProgress",
        "cobra_player_aspect_anchor",
        "cobra_player_options_anchor",
    ]
    missing = [token for token in required_player_tokens if token not in chrome]
    if missing:
        raise RuntimeError("Locked player contract drift: " + ", ".join(missing))

    text = before

    # General Cobra is no longer globally fullscreen. Fullscreen ownership becomes surface-scoped.
    old_fullscreen = """    getWindow().setFlags(
        WindowManager.LayoutParams.FLAG_FULLSCREEN,
        WindowManager.LayoutParams.FLAG_FULLSCREEN);"""
    text = edit_method(
        text, "onCreate", old_fullscreen,
        "    getWindow().clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);"
    )
    text = edit_method(
        text, "onCreate", "    buildShell();",
        "    buildShell();\n    mMain.post(this::cobraApplySystemBarsForSurface);"
    )

    # Locked 2103164 already owns PiP lifecycle. We only add UI routing/inset restoration around it.
    text = edit_method(
        text, "onResume", "    super.onResume();",
        "    super.onResume();\n    mMain.post(()->{cobraConsumeLauncherPipReturn();cobraApplySystemBarsForSurface();});"
    )
    text = append_method_body(
        text, "onPictureInPictureModeChanged",
        "    if(inPictureInPictureMode)mCobraPipReturnArmed=true;\n"
        "    mMain.post(()->{cobraConsumeLauncherPipReturn();cobraApplySystemBarsForSurface();});"
    )
    text = edit_method(
        text, "onConfigurationChanged", "    super.onConfigurationChanged(configuration);",
        "    super.onConfigurationChanged(configuration);\n"
        "    cobraApplySystemBarsForSurface();"
    )
    # onConfigurationChanged has intentional early returns for player, Multi-View,
    # attached guide and Settings. Every exit must leave system-bar ownership settled,
    # then post once more after any reflow work queued by those branches.
    ca, cb = method_span(text, "onConfigurationChanged")
    config = text[ca:cb]
    config = config.replace(
        "return;",
        "cobraApplySystemBarsForSurface();mMain.post(this::cobraApplySystemBarsForSurface);return;"
    )
    text = text[:ca] + config + text[cb:]
    text = append_method_body(
        text, "onConfigurationChanged",
        "    cobraApplySystemBarsForSurface();\n"
        "    mMain.post(this::cobraApplySystemBarsForSurface);"
    )

    # Fullscreen video/multiview hide only the status bar; browse/preview restore it.
    text = prepend_method(text, "openPlayerOverlay", "    cobraApplySystemBarsForSurface();")
    # The call above runs before mPlayerOverlay is created, so post once after creation too.
    text = append_method_body(text, "openPlayerOverlay", "    mMain.post(this::cobraApplySystemBarsForSurface);")
    if len(method_matches(text, "beginMultiView")) == 1:
        text = append_method_body(text, "beginMultiView", "    mMain.post(this::cobraApplySystemBarsForSurface);")
    for name in ("closePlayer", "releaseMulti", "showCobraPrimaryView"):
        if len(method_matches(text, name)) == 1:
            text = append_method_body(text, name, "    mMain.post(this::cobraApplySystemBarsForSurface);")

    state_anchor = "  private final CobraPlaybackPolicy mCobraPlaybackPolicy=new CobraPlaybackPolicy();"
    text = once(
        text, state_anchor,
        state_anchor
        + "\n  private boolean mCobraPipReturnArmed=false;"
        + "\n  private boolean mCobraLauncherPipReentry=false;"
    )

    helpers = r'''
  private boolean cobraIsLauncherReturn(Intent intent){
    if(intent==null)return false;
    if(intent.getBooleanExtra("cobra_open_browse",false))return true;
    return Intent.ACTION_MAIN.equals(intent.getAction())&&intent.hasCategory(Intent.CATEGORY_LAUNCHER);
  }

  @Override protected void onNewIntent(Intent intent){
    super.onNewIntent(intent);setIntent(intent);
    if(cobraIsLauncherReturn(intent)&&(mCobraPipReturnArmed||mCobraPlaybackPolicy.pipOwned
        ||isCobraInPictureInPicture()||mPlayerOverlay!=null||mMultiOverlay!=null)){
      mCobraLauncherPipReentry=true;
    }
  }

  @Override public void onWindowFocusChanged(boolean hasFocus){
    super.onWindowFocusChanged(hasFocus);
    if(hasFocus)mMain.post(this::cobraApplySystemBarsForSurface);
  }

  private void cobraConsumeLauncherPipReturn(){
    if(isCobraInPictureInPicture())return;
    if(!mCobraLauncherPipReentry){
      // No launcher/browse intent means this was native PiP expansion; preserve fullscreen.
      mCobraPipReturnArmed=false;
      return;
    }
    mCobraLauncherPipReentry=false;mCobraPipReturnArmed=false;
    if(mPlayerOverlay!=null){
      clearCobraPlayerLockState(false);
      closeFullscreenToCobraView();
    }else if(mMultiOverlay!=null){
      releaseMulti();showCobraPrimaryView();
    }else if(mRoot!=null){
      showCobraPrimaryView();
    }
  }

  private void cobraApplySystemBarsForSurface(){
    boolean fullscreen=!isCobraInPictureInPicture()&&(mPlayerOverlay!=null||mMultiOverlay!=null);
    android.view.Window window=getWindow();
    if(fullscreen)window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    else window.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
    if(Build.VERSION.SDK_INT>=30){
      android.view.WindowInsetsController controller=window.getInsetsController();
      if(controller!=null){
        if(fullscreen)controller.hide(android.view.WindowInsets.Type.statusBars());
        else controller.show(android.view.WindowInsets.Type.statusBars());
      }
    }else{
      View decor=window.getDecorView();int flags=decor.getSystemUiVisibility();
      if(fullscreen)flags|=View.SYSTEM_UI_FLAG_FULLSCREEN;
      else flags&=~View.SYSTEM_UI_FLAG_FULLSCREEN;
      decor.setSystemUiVisibility(flags);
    }
    View decor=window.getDecorView();decor.requestApplyInsets();decor.requestLayout();
    if(mRoot!=null){mRoot.requestApplyInsets();mRoot.requestLayout();}
  }
'''
    if len(method_matches(text, "onNewIntent")) != 0 or len(method_matches(text, "onWindowFocusChanged")) != 0:
        raise RuntimeError("Unexpected pre-existing launcher/window-focus override in locked baseline")
    text = append_class(text, helpers)

    # Player chrome and approved controls must remain byte-identical.
    for name, expected_hash in player_before.items():
        actual = sha_bytes(method_text(text, name))
        if actual != expected_hash:
            raise RuntimeError("Protected player method changed: " + name)
    open_after = method_text(text, "openPlayerOverlay")
    normalized = normalize_open_player(open_after).replace(
        "    mMain.post(this::cobraApplySystemBarsForSurface);\n", "", 1
    )
    if normalized != open_before:
        raise RuntimeError("openPlayerOverlay changed beyond system-bar ownership hooks")

    after_bytes = text.encode()
    out = Path(out);out.mkdir(parents=True, exist_ok=True)
    (out / "source-before").mkdir(exist_ok=True)
    (out / "source-before" / src.name).write_bytes(before_bytes)
    src.write_bytes(after_bytes)
    proof = {
        "base_locked_commit": BASE_LOCK,
        "base_version_code": 2103164,
        "files": {str(REL): {"before": sha_bytes(before_bytes), "after": sha_bytes(after_bytes)}},
        "protected_player_methods": player_before,
        "player_contract_tokens": required_player_tokens,
        "status_bar_scope": "browse-visible / fullscreen-video-hidden",
        "pip_launcher_return": "browse",
        "native_pip_expand": "preserve fullscreen",
        "native_changed": False,
        "physical_device_verified": False,
    }
    (out / "patch.json").write_text(json.dumps(proof, indent=2) + "\n")
    print("PASS: locked 2103164 -> 2103165 inset/PiP-return delta; approved player chrome protected")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    apply(a.source,a.receipt,a.out)
