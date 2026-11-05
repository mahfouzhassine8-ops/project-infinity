# Separate Details navigation proposal — NOT APPLIED

One skin file only: existing unified/Includes_InfinityMediaLists.xml. No native changes.

Confirmed mechanism: controls98070/98071/98072 currently send Up to textbox98064. Frozen GUITextBox::CanFocus returns false. Existing source-bound Linux tests also fail to focus it. The textbox's own onup/ondown declarations cannot make it focusable.

Propose replacing only those three Up targets with:

    <onup condition="Control.IsVisible(98066)">98066</onup>
    <onup>50</onup>

Reuse existing details scrollbar98066 when visible; otherwise return to existing media list50. Native GUIAction::GetNavigation evaluates conditional integer targets in order, so the unconditional50 is a fallback. GUIScrollBarControl::IsVisible hides the control for one-page content when showonepage=false. This avoids directing focus to an invisible scrollbar. No SetFocus worker, event system, new control, direct action, context-menu mapping, default selection, left/right/down action, metadata or provider changes are proposed. Existing scrollbar boundary handling remains unchanged, including the currently investigated selection-restoration observation.

Static checks: exactly three replacements; exact byte restoration; unchanged remaining actions/data/theme fields; parsed XML. The proposal patch is outside the overlay and not applied. No proposed runtime behavior has been executed.

After separate approval, test real Up from each visible Play/Trailer/Info button, with overflowing and one-page details. Verify scrollbar focus, Down/Up scrolling, return at each boundary, selected-item identity and scroll restoration. Include folders/seasons without Play/Trailer, missing art/plot, long synopsis, repeated Info/Back, Light/Dark, both Fold displays/orientations and touchscreen/remote/keyboard. Preserve the old failed textbox-focus results. Do not accept this proposal as resolving the separate scroll-boundary selection observation without a before/after runtime check.

Back/Trailer remains a separate unapplied proposal in INFO-CONTROL-REVIEW.md. Neither proposal authorizes native edits, APK packaging or signing.
