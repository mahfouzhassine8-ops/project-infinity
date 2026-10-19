# INFINITY — PLAYBACK / VIDEO SETTINGS / AUDIO & SUBTITLES GLASS MENUS

**User-requested visual behavior — FINAL VISUAL DESIGN NOT YET APPROVED.** Proposed comparison image rendered in conversation October 19, 2026; awaiting explicit approval or requested adjustments.

## Exact newest user instructions (verbatim)

> "Also, for the video icon and the subtitle icon, they should be glass to where the video still can be seen through them to a sense. So if you want to mock that so we can approve it, we can do that."

> "I'm referring to the menu, that is."

> "If anything, playback menu should follow the same."

**CRITICAL INTERPRETATION:** The user means the **WINDOW/PANEL of the menus opened by the existing player controls**, NOT making the actual little video/subtitle OSD icons glass. Their explicit intent is for **all THREE MENUS** to share a readable, translucent Infinity liquid-glass panel through which the video remains partially visible.

## Scope and live status

- **Canonical task 11:** existing monitor/video-looking OSD control must open real Video Settings; existing icon/position kept unchanged. This user request relates to **the menu opened**, not icon artwork.
- **Canonical task 12:** remove ONLY the redundant Video Settings **row** from the existing Playback OPTIONS POPUP, because task 11 gives Video Settings its own OSD entry. Do NOT remove the actual function or any other existing Playback row.
- **Canonical task 13:** Video Settings becomes a **standalone compact modal**, **slightly smaller than the Playback options popup**, with translucent Infinity liquid-glass shell, and actual existing video controls intact.
- **Canonical task 14:** Audio & Subtitles becomes a **standalone compact modal**, **slightly smaller than the Playback options popup**, with matching translucent Infinity liquid-glass shell, and actual audio and subtitles options intact.
- **Playback options popup itself also gets the SAME GLASS PANEL DESIGN**, as a visual part of task 12; this does **not** authorize modifying its controls, actions, focus logic or size beyond the approved translucent styling and the one redundant row removal.
- All these are **user-requested requirements**, but precise visual opacity/background/placement awaits **user approval of mock**. Nothing is implemented, tested, signed, installed or final locked by this document.

## Actual existing Playback menu actions (do not replace with invented mock action lists)

The original user-recorded Playback options popup contains exactly these functional entries:

1. **Now Playing**
2. **Audio & Subtitles**
3. **Video Settings** — remove ONLY this redundant entry *after* OSD's Video Settings button is verified, canonical task 12
4. **Chapters & Bookmarks**
5. **Playlist**
6. **Go To Time**
7. **Player Settings**
8. **Playback Info**
9. **Close Player**

Do **NOT** replace the actual existing Playback popup with the *Play/Pause / Stop / Skip / Repeat / Shuffle* items depicted in an illustrative AI-generated image. **Those labels are NOT approved and MUST NOT enter production code.** There is NO general overhaul or new action inventory approved.

The original **Audio & Subtitles** entry **stays in Playback** and opens the compact glass sub-menu. The **Player Settings** entry stays separate and intact. Every action retains original semantics.

## Glass look and feel — proposed for confirmation

- All three centered modals use same existing Infinity liquid-glass look and architecture. **Video is visible through the window itself, not merely around its edges**; retain enough dark/light opacity for crisp labels, buttons and focus glow. Do not increase opacity until underlying video is completely hidden.
- Light theme: translucent pearl/white, appropriately dark text, restrained cool-blue/cyan focus border.
- Dark theme: translucent navy/charcoal, white text, existing Infinity cyan focus and controls.
- OLED theme: near-black translucent panel/true-black edges without turning the entire video opaque or using gray haze; preserve contrast.
- Night Cinema: restrained warm amber **menu accents only**, no video image recolor or adjustment to actual decoder/display.
- Reuse **existing** theme state, Glass settings, safe-area constraints and motion/reduced/off preferences. The shared **visual tokens** may be reused; do not rewrite global dialogs or alter Cobra.
- Playback popup size stays as approved/current; Video Settings and Audio & Subtitles popups are **slightly smaller than Playback** on same device, responsive to actual content. For more entries use interior scrolling, not a giant full-screen replacement or cut-off rows.
- Playback video **continues** behind menus; no seek/play-state or audio/subtitle interruption from opening/closing menus, no background frame-color changes. Any blur/transparency must be inexpensive and respect already approved performance and reduced-motion modes.
- Touch: large unambiguous target row rectangles, clear selected vs focused state, single real activation; closing X/Back restores original playback/OSD focus without dispatching another action or hiding video.
- Works Fold cover/inner, rotations, Light/Dark/OLED/Night Cinema; no overlaps, clipping or bottom Android navbar obstruction.
- Never substitute a new OSD button icon, new playback screen, global Kodi/native menu rewrite, source/provider change, Audio stream reset or unapproved player behaviors.

## Visual mock approval boundary

The conversation contains rendered visual concepts depicting video playing behind glass menus, but generated movie titles, button icons and option lists may be illustrative and do NOT establish intended functionality or user approval. The REAL Infinity OSD/Playback menu screenshot (previously cited as `1792386488186.jpeg`) and THIS exact functional inventory are authoritative for action labels/order. If actual screenshot bytes are unavailable in future chats, retrieve user source or ask for a new one; NEVER reverse engineer from AI-generated dummy labels.

**User has explicitly requested a glass window effect, and invited a mockup for visual approval. They have NOT yet said LOCK/APPROVE for the pictured opacity/layout.** Save this as `VISUAL_PROPOSAL_PENDING_APPROVAL`; when user approves, add approved final render/reference with a new date and update canonical tasks 11–14, status and handoff. Do not promote the illustrative mock to a bite-for-bite design lock by assumption.

## Protection

Provisional signed APK **2103390** and its SHA-256 `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb` unchanged. Locked Essential-First fallback 2103384 unchanged. **COBRA COMPLETELY OFF LIMITS.** No edits to native engine, PiP, background playback, decoder, source handlers, non-playback menus, progress data or installed profiles are allowed by this appearance request.

**STATUS: VISUAL DESIGN PROPOSAL SAVED; USER APPROVAL PENDING; ZERO IMPLEMENTATION.**
