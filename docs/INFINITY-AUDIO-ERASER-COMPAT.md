# Infinity Samsung Audio Eraser compatibility

Samsung documents real-time Audio Eraser in the Quick panel for select apps. No public Samsung developer API or self-service opt-in is documented for arbitrary third-party package IDs.

Infinity therefore uses only legitimate Android platform signals:

- package identity remains `com.projectinfinity.kodi`
- `android:appCategory="video"`
- the existing single Kodi/Infinity `MediaSession`
- local playback with `AudioAttributes.USAGE_MEDIA`
- `AudioAttributes.CONTENT_TYPE_MOVIE`
- MediaStyle playback notification and transport controls
- normal PiP/video activity integration

This is a compatibility posture, not a Samsung whitelist bypass. Device testing decides whether the current Samsung firmware surfaces the Audio Eraser Quick-panel chip for Infinity. We do not impersonate Crunchyroll, YouTube, Opera, or any other allowlisted package.
