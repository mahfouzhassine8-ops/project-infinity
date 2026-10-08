import datetime
import hashlib
import os
import tempfile

import xbmcaddon
import xbmcgui
import xbmcvfs

from source_snapshot import collect, digest_file


def vfs_digest(path):
    digest = hashlib.sha256()
    source = xbmcvfs.File(path, "r")
    try:
        while True:
            chunk = source.readBytes(1024 * 1024)
            if not chunk:
                break
            digest.update(bytes(chunk))
    finally:
        source.close()
    return digest.hexdigest()


def main():
    dialog = xbmcgui.Dialog()
    destination = dialog.browseSingle(3, "Choose a folder for the source ZIP", "files")
    if not destination:
        return
    ids = set()
    for root in ("special://home/addons/", "special://xbmc/addons/"):
        directories, _ = xbmcvfs.listdir(root)
        ids.update(directories)
    addons = []
    missing = []
    for addon_id in sorted(ids):
        try:
            addon = xbmcaddon.Addon(addon_id)
            addons.append({"id": addon_id, "path": xbmcvfs.translatePath(addon.getAddonInfo("path")),
                           "version": addon.getAddonInfo("version")})
        except RuntimeError:
            missing.append(addon_id)
    if not addons:
        dialog.ok("Infinity Source Audit", "No installed add-on paths could be resolved. No export was created.")
        return
    progress = xbmcgui.DialogProgressBG()
    progress.create("Infinity Source Audit", "Reading installed code")
    temporary = None
    try:
        cache = xbmcvfs.translatePath("special://temp/")
        descriptor, temporary = tempfile.mkstemp(prefix="infinity-source-", suffix=".zip", dir=cache)
        os.close(descriptor)
        def update(index, count, addon_id):
            progress.update(int(index * 90 / max(count, 1)), message=addon_id)
        report = collect(addons, temporary, update)
        if missing:
            # Missing paths must remain visible; they are not treated as audited.
            import json
            import zipfile
            with zipfile.ZipFile(temporary, "a", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("UNRESOLVED-ADDON-PATHS.json", json.dumps(missing, indent=2) + "\n")
        name = "Infinity-Installed-Addon-Code-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".zip"
        output = destination.rstrip("/\\") + "/" + name
        if xbmcvfs.exists(output):
            raise ValueError("An export with this name already exists. Run again in a moment.")
        progress.update(95, message="Saving and checking the ZIP")
        expected = digest_file(temporary)
        if not xbmcvfs.copy(temporary, output) or vfs_digest(output) != expected:
            raise ValueError("The export could not be copied and verified in that folder.")
        status = "Some sources are unresolved; that is recorded in the ZIP." if report["errors"] or missing else "Code snapshot verified."
        dialog.ok("Infinity Source Audit", status + "\n\n" + name + "\n\nUpload this exported ZIP in our chat.")
    except Exception as error:
        dialog.ok("Infinity Source Audit", "Export failed: " + str(error))
    finally:
        progress.close()
        if temporary and os.path.exists(temporary):
            os.remove(temporary)


if __name__ == "__main__":
    main()
