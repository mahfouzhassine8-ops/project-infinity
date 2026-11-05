# Final skin behavior proposals — both remain unapplied

These proposals are independently reviewable. Neither is part of the runtime overlay. Current visual code and all approved actions remain as at1aacaf61.

## A. Info Back and Trailer

File: existing skin `unified/DialogVideoInfo.xml` only. Exact patch: ../INFO-CONTROL-PROPOSAL.patch. Source/proposed hashes and replacement counts: ../INFO-CONTROL-PROPOSAL.json.

- Back10 ->9011: prevents native Get Artwork from receiving the Back click. Retain PreviousMenu, layout, visual states, default focus, and existing loading registration; update only ID-linked focus/loading references.
- Trailer15 ->9012: prevents native Manage Video Extras from receiving the Trailer click. Retain existing conditional Stop, original script.trailer.bridge request/arguments, visibility and alternate label, loading notifications/ownership and target identity. Do not use native Trailer11, replace the player or add another trailer path.
- Keep Play8, Cast5/list50, More Info106 and all other bindings unchanged. No native edit.

Required tests after approval: click dispatch reaches only the intended action; Back opens no artwork dialog and restores prior window/item; Trailer invokes the original bridge once with idle or active playback, without extras/duplicate native playback; missing trailer, bridge failure/cancel and episode-hidden cases; truthful loading cleanup; Play/Cast/More Info/focus/input regressions; Light/Dark and Fold portrait/landscape. Static patch validation is not proof that the existing trailer bridge itself is operational on the device.

## B. Details action-row Up

File: existing `unified/Includes_InfinityMediaLists.xml` only. Exact patch: ../continuation-a7/DETAILS-NAVIGATION-PROPOSAL.patch. It changes only the Up routes of98070/98071/98072:

    <onup condition="Control.IsVisible(98066)">98066</onup>
    <onup>50</onup>

The original target98064 is a textbox that native code cannot focus. The proposal uses the existing visible scrollbar, falling back to the existing media list for one-page content. Preserve all click actions, visibility, enablement, left/right/down, control IDs, touch controller, context menus and native source. It does not reset scrolling automatically or modify scrollbar boundary behavior.

Required tests after approval: real Up from each visible action; overflowing versus one-page/empty details; hidden Play/Trailer on folders/seasons; scrolling to both boundaries and return to the correct list item; repeated Info/Back/directory transitions; remote/keyboard/touch and Fold/theme coverage. Retain prior failed tests. The synchronized Linux sequence comparison does not establish rapid physical input acceptance.

## Separate limits

No package/build/signing approval is implied. Downloads has its own three-file proposal and unresolved classification/context gates. The custom Info plot400 is not native plot4; renaming it would change native Cast/Plot ownership and is not included in either proposal. Existing full-text Info accessibility remains a separate verification/dependency question, not permission to silently reassign that control.
