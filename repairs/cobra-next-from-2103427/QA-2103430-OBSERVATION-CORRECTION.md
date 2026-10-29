# Signed2103430 observation correction

Recorded before a second focused run of the **same** signed APK. No production rebuild or signing is selected.

First run40966613409 installed the exact APK and reached Cobra welcome. All four framework launcher resource lookups passed: both day IDs select the new light adaptive XML; night IDs select the original dark XML. Its UI journey stopped at the native M3U picker before testing player actions. The enabled TextView/android:id/text1 sits inside the enabled ListView/android:id/select_dialog_listview, but both report clickable=false because the framework handles item presses through ListView.onItemClick. The QA driver incorrectly required clickable=true on the label. The correction explicitly permits only this normal picker hierarchy, clips the visible row bounds, and sends an actual coordinate tap. Player buttons remain clickable-only.

The first launcher screenshots are Home, despite the observer's app-drawer filenames: its swipe began inside Google's search widget and did not open the drawer. The dark Home prediction labels Infinity but displays the generic Android icon. Logs explicitly report Invalid resource ID0 and PackageManager default-icon fallback for Splash. This is not reported as successful icon rendering or attributed solely to a benign cache. The unchanged binary manifest has correct framework icon/roundIcon attribute IDs and the intended application resource IDs; no Splash icon override exists. The lower-level fallback cause remains unresolved.

Selected additional read-only observations, before importing the synthetic playlist:

- Capture full PackageManager launcher ResolveInfo in both system modes.
- Open normal Android App Info for the installed package and save its native hierarchy/screenshot without pressing any Settings action.
- Return Home and use the standard All Apps key, or a normal upward swipe from the blank workspace region if Home remains visible. Save actual drawer identity, native Infinity item bounds and screenshots; do not infer a drawer from the requested gesture alone.
- Preserve errors and partial classifications, return through the existing exported Cobra Activity, and independently run the finite Pro button journey.

No app-icon launch, Infinity execution, reset, uninstall, force-stop, component toggle, launcher-data operation, hidden API/helper APK or shutdown test is selected. Settings App Info is read-only. The original signed APK, four matching components and their checksums remain unchanged. These observations do not establish Samsung/Fold acceptance.
