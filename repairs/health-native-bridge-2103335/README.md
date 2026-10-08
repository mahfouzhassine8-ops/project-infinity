# Infinity 2103335 — Health native trace bridge

Purpose: make the existing bounded native shutdown critical timeline visible inside Health Center's ordinary report.txt so device evidence can be pasted directly without manually extracting ZIP internals.

Parent: exact successful 2103334 Script-Exit RC1 from run 37732755842.

Scope:
- Android package only.
- One source template changes: InfinityHealthExport.java.in.
- Existing shutdown/critical.jsonl and shutdown/critical.previous.jsonl ZIP entries remain.
- report.txt additionally contains both timelines, each bounded to 512 KiB.
- Missing evidence is explicitly reported as unknown, never as success.
- libkodi.so remains byte-identical to 2103334.
- No shutdown behavior, timeout, process-kill, player, provider, skin, Cobra, Resume Hub, data, or native-engine change.

This candidate is diagnostic-only and must not be locked as a shutdown fix.
