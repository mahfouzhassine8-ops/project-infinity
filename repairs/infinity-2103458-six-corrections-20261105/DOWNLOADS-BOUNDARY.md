# Downloads-only filtering boundary — no native patch authorized or made

Read-only inspection of the frozen native source:

- `xbmc/filesystem/SourcesDirectory.cpp`, CSourcesDirectory::GetDirectory: copies all configured video sources, adds removable drives and emits each source. No URL filter option exists for selecting user-added folders rather than provider sources.
- `xbmc/video/windows/GUIWindowVideoNav.cpp`, GetStartFolder: the native files alias resolves to sources://video/. Directory handling and source context actions rely on this original source-root identity.
- `xbmc/windows/GUIMediaWindow.cpp`, Update: native Add videos is inserted for sources://video/; an arbitrary plugin-produced directory does not automatically preserve that behavior.
- The existing Downloads helper first opens an accessible Download directory, otherwise uses the native source browser. Opening the physical folder alone cannot simultaneously show other configured folders and native Add videos.

No existing equivalent filtered source entry was verified. Skin-only hiding would leave the native item list, focus indices and context ownership inconsistent. A replacement Python directory would require emulating source/add-video behavior and is not being introduced.

The narrow potential native boundary remains `xbmc/video/windows/GUIWindowVideoNav.cpp` and `.h`: explicit Downloads-only activation state; filter only the copied root result, never the source registry; retain native source item flags and Add videos insertion; clear state when entering unrelated destinations. SourcesDirectory and GUIMediaWindow are dependencies to preserve, not proposed edit targets. This is a dependency assessment, not an approved patch or proven design.

Classification is also unresolved: protocol alone does not prove a source is user-added. A user-created plugin or network folder must not be hidden merely because it is remote. Any future reviewed proposal must establish reliable entry classification, Back/reentry state, source-context preservation and unchanged ordinary sources navigation before requesting authorization. No source definition, native file, permission or user setting was changed.
