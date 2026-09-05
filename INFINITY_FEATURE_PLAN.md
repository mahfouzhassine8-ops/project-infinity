# Infinity Integrated Feature Architecture

Infinity will present its custom tools as built-in application features rather than a collection of user-installed scripts.

## Infinity Settings

### Health & Repair
- Scan Infinity
- Auto Repair
- Manual Repair
- Dependency health
- Repository health
- Log/support package

### Performance
- Automatic
- Smooth
- Turbo
- Active-mode indicator
- Playback-aware switching

### Player
- Internal-player touch lock
- External-player preferences
- Resume handling
- Player history

### Backup & Restore
- Full Infinity setup backup
- Restore
- Build/settings backup

### Storage & Cleanup
- Quick Clean
- Safe Cleanup
- Cache/temp management
- Storage information

## Integration model

1. Bundle supporting Python modules/add-ons into the APK where Kodi's Python API is appropriate.
2. Expose features through Infinity-branded skin/settings navigation instead of requiring ZIP installation.
3. Keep implementation names out of the normal user interface.
4. Move individual features into Kodi/native Android code only when Python cannot provide the required behavior.
5. Preserve Kodi compatibility and test each subsystem before combining it into the final Infinity APK.

## Build priorities

1. Stable/persistent APK signing for future in-place updates.
2. Infinity Settings shell/navigation.
3. Player lock and player tools.
4. Health & Repair integration.
5. Performance integration.
6. Backup/Restore and cleanup.
7. Final branding and regression testing.
