#!/usr/bin/env python3
"""Guarded drawer edits over the user-supplied locked skin 195.

No provider, player, Python, asset, profile-selection or native changes.
"""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE_ZIP_SHA256 = "c5290ee4352ba8b0b60af9222b4e7b032c40c2d1ccef4d1a4387699f9a5c83f9"
BEFORE = {
    "unified/Home.xml": "11ef0072eec4c117e0b02a3ede9f8f592cb1956ed8433e19f249efddb4d598ac",
    "unified/Custom_1198_InfinityNav.xml": "437fd869facc7c35b2f32e3fd229c81eed65ee6ec5bfeb41730e3e5b48bb9651",
}
AFTER = {
    "unified/Home.xml": "e621925860065cc631070a0b28653e9ff323e7974c1f1cf0fc8a8c3d4375e90a",
    "unified/Custom_1198_InfinityNav.xml": "25b60eaca60f927ab364b733604fa1a740d5834922dbfb1e7e71fa24428add0b",
}
FIXTURE_SHA256 = dict(BEFORE, **{
    "unified/IncludesVariables.xml": "65511e4e198a68255f8d104c66afd9541c911086555c7f761513f5491749ebc9",
})
EDITS = {
    "unified/Home.xml": [(
        '        <texturefocus border="20" colordiffuse="$VAR[InfinityDrawerFocusWash]">infinity_polish/field.png</texturefocus>\n'
        '        <texturenofocus border="20" colordiffuse="00000000">infinity_polish/field.png</texturenofocus>',
        '        <texturefocus border="20" colordiffuse="$VAR[InfinityGlassFocus]">infinity_polish/focus_rim.png</texturefocus>\n'
        '        <texturenofocus>infinity_reference/slider_transparent.png</texturenofocus>',
    )],
    "unified/Custom_1198_InfinityNav.xml": [(
        '<height max="1120">88%</height>', '<height max="1050">88%</height>',
    ), (
        'start="11.47,10.89" end="100,100"', 'start="11.47,11.62" end="100,100"',
    ), (
        'start="100,100" end="11.47,10.89"', 'start="100,100" end="11.47,11.62"',
    ), (
        '<control type="button" id="1198305">\n'
        '            <align>left</align>\n'
        '            <onclick>Dialog.Close(1198)</onclick>\n'
        '            <onclick>ActivateWindow(InterfaceSettings)</onclick>',
        '<control type="button" id="1198310">\n'
        '            <align>left</align>\n'
        '            <onclick>Dialog.Close(1198)</onclick>\n'
        '            <onclick>ActivateWindow(InterfaceSettings)</onclick>',
    )],
}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def repair(original):
    candidate = dict(original)
    for name, replacements in EDITS.items():
        require(sha(original[name]) == BEFORE[name], "Wrong locked XML preimage: " + name)
        content = original[name].decode("utf-8")
        for old, new in replacements:
            require(content.count(old) == 1, "Ambiguous edit: " + name)
            content = content.replace(old, new, 1)
        if name == "unified/Custom_1198_InfinityNav.xml":
            # Only the first marker belongs to the newly added UI Theme row.
            # The legacy Performance & refresh control keeps its original ID.
            old_marker = "Control.HasFocus(1198305)"
            require(content.count(old_marker) == 2, "Wrong baseline focus markers")
            content = content.replace(old_marker, "Control.HasFocus(1198310)", 1)
        candidate[name] = content.encode("utf-8")
        require(sha(candidate[name]) == AFTER[name], "Unexpected repaired XML hash: " + name)
    return candidate


def fixtures():
    original = {name: (HERE / "fixtures" / name).read_bytes() for name in FIXTURE_SHA256}
    for name, digest in FIXTURE_SHA256.items():
        require(sha(original[name]) == digest, "Regression fixture changed: " + name)
    return original
