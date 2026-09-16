#!/usr/bin/env python3
"""Compatibility/handoff hardening for the Cobra 2103150 iron-polish pass."""
from __future__ import annotations

import infinity_cobra_2103150_iron_polish as base

_original_patch = base.patch


def patch(java: str) -> str:
    java = _original_patch(java)

    # showCobraPrimaryView() constructs the new TextureView synchronously but its
    # transfer attachment is posted to that view. Do not release the preserved
    # ExoPlayer before the posted attachment has had a chance to run.
    old = '''      showCobraPrimaryView();
      if (mCobraTransferPlayer != null) releaseCobraTransferPlayer();
      return;'''
    new = '''      showCobraPrimaryView();
      if (mCobraTransferPlayer != null && mCobraPreviewHost != null)
        mCobraPreviewHost.postDelayed(() -> {
          if (mCobraTransferPlayer != null) releaseCobraTransferPlayer();
        }, 500L);
      return;'''
    if java.count(old) != 1:
        raise RuntimeError("2103150 transfer sequencing anchor missing")
    java = java.replace(old, new, 1)

    # Returning through the player Settings drawer should use the same seamless
    # fullscreen -> preview path as Android Back and the compact player button.
    a, b = base.span(java, "  private void showPlayerSettingsDrawer() {")
    block = java[a:b]
    old_guide = '    guide.setOnClickListener(v -> { closePlayer(); showGuide(); });\n'
    if old_guide in block:
        block = block.replace(old_guide,
            '    guide.setOnClickListener(v -> { closePlayerSettingsDrawer(); closeFullscreenToCobraView(); });\n', 1)
        java = java[:a] + block + java[b:]

    return java


base.patch = patch

if __name__ == "__main__":
    base.main()
