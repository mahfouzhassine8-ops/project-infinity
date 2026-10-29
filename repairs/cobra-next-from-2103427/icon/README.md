# Theme-qualified launcher resource exception

The full approved icon brief was read before implementation. This implementation
starts from actual signed 2103429 icon resources. It changes no executable code,
Activity/alias, manifest icon ID, app identity, source data, startup behavior,
chooser design, native library, persistence or shutdown behavior.

`resources.py` modifies only the two existing `mipmap/ic_launcher` and
`mipmap/ic_launcher_round` resource IDs. Their existing default configurations
point to seven new light resource files. Night-qualified clones point to the
exact original dark files. The two type-spec entries add Android's `UI_MODE`
configuration-change bit. No new resource IDs or changes to non-icon table
entries are introduced. All original resource files remain byte-identical.

The original foreground and original Android13 monochrome foreground have
**identical alpha pixels** at 432×432. The new light adaptive icon uses an inline
white ColorDrawable and a black-tinted BitmapDrawable referencing that existing
monochrome source. It does not trace, redraw or synthesize a replacement emblem.
The old adaptive XMLs, colored foreground, navy background, monochrome, original
master and five density pairs remain unchanged for night mode.

Legacy light fallback images use the same original monochrome alpha's standard
centered 72-of-108 adaptive viewport, resampled to the existing legacy dimensions.
They retain each exact old density's rounded-tile alpha. Adaptive rendering uses
the exact original mask without resampling by this implementation; legacy density
resampling is explicitly distinct from a byte-identical mask. Canonical stored
DEFLATE PNG encoding avoids timestamps and zlib/Pillow encoder-version drift.

`BASELINE_SHA256` pins all 19 original inputs. `reference/` retains those exact
inputs for offline verification. `expected_resources(baseline_members)` returns
the changed table and seven new paths. `verify_resources(candidate_members,
baseline_members)` independently regenerates the exact expected bytes and rejects
changed original artwork or a different candidate table/light resource. Other
resource members and complete package ownership are additionally checked by the
existing owner/release gate.

The selected host checks are recorded in `SELECTION.json`. They do **not** prove
Samsung launcher behavior. Final combined-APK Android resource inflation,
system-mode switching and launcher refresh observations are recorded by the parent
release task. A launcher may cache app icons until a supported refresh. A user-
enabled themed-icon setting may use the unchanged monochrome mask and choose its
own wallpaper palette: those colors cannot promise the approved exact cyan/navy
or black/white treatment on every system surface. No component toggling, duplicate
icon, launcher reset, service, polling or unsafe workaround is introduced.
