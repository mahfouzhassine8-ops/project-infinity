# Selected verification for rotation and fullscreen audio only

Before executing application tests, select the new two-state rotation policy, native fullscreen real-button presses, selected Multi-View audio mute/restore, control order/touch geometry, state/lifecycle transitions and their explicit preservation controls from the user brief. No shutdown tests, data clearing or unrelated feature suite is selected.

Build input is the exact signed2103444 COBRA ZIP, SHA256 f00c5e887cd221b12ee37a1e2a801dd61e60ecf555e0cfc1bb38974fd41ba690. Original-key APK SHA256 38dff935ffc0967e2c16e8d61e6e4bfd693fcb73bbaa130e8fa354e468b85a76. Native source preimages must match that component. Infinity/shared/chooser executable and resource owners remain unchanged. Existing source/host evidence is historical, not proof of the new changes.

Targeted host tests will check actual native button presses across mode/screen/theme representatives; repeated auto/lock toggles in all four displayed rotations; mode and fullscreen transitions; PiP/multiwindow restrictions and restored policy; actual selected-player mute/unmute and volume restoration; no device-volume mutation or stream restart. Additional source/class/method comparison must identify every altered method and reject changes outside the reviewed list. Android verification and original-key packaging are pending; no candidate exists yet.
