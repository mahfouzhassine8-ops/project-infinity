"""On-demand native ZIP picker preview. Installation returns through the original picker."""
import os
import sys
import threading

import xbmc
import xbmcgui
import xbmcvfs

sys.path.insert(0, os.path.dirname(__file__))
from infinity_zip_metadata import clean_text, inspect
from infinity_preview_state import Session

PREFIX = 'Infinity.FilePreview.'
BACK_ACTIONS = (9, 10, 92, 101)


def size_label(size):
    if size is None:
        return 'Unavailable'
    if size < 1024:
        return str(size) + ' bytes'
    for unit in ('KiB', 'MiB', 'GiB', 'TiB'):
        size /= 1024.0
        if size < 1024:
            return f'{size:.1f} {unit}'
    return f'{size:.1f} TiB'


def details(metadata):
    rows = []
    for title, value in [('Version', metadata.version), ('Add-on ID', metadata.addon_id),
                         ('Type', metadata.addon_type or metadata.kind), ('File', metadata.file_name),
                         ('Size', size_label(metadata.size)), ('Location', metadata.path)]:
        if value:
            rows.append('[B]' + title + '[/B]\n' + clean_text(value, 1024))
    if metadata.description:
        rows.append('[B]Description[/B]\n' + metadata.description)
    return '\n\n'.join(rows)


class PreviewDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.parent = kwargs['parent']
        self.parent_id = kwargs['parent_id']
        self.nonce = kwargs['nonce']
        self.request_path = kwargs['request_path']
        self.folder = kwargs['folder']
        self.label = kwargs['label']
        self.size_hint = kwargs['size_hint']
        self.session = Session()
        self.worker = None
        self.check_worker = None
        self.accepted = False

    def current(self):
        try:
            return (self.parent.getProperty(PREFIX + 'Nonce') == self.nonce and
                    self.parent.getProperty(PREFIX + 'Path') == self.request_path and
                    self.parent.getProperty(PREFIX + 'NativeVersion') == 'v1')
        except Exception:
            return False

    def onInit(self):
        self.setProperty('Preview.Title', clean_text(self.label, 256) or 'File preview')
        self.setProperty('Preview.Status', 'Reading file information…')
        self.getControl(80).setEnabled(False)
        self.setFocusId(81)
        self.worker = threading.Thread(target=self.run_worker, name='InfinityZipPreview', daemon=True)
        self.worker.start()

    def run_worker(self):
        self.load_metadata()
        monitor = xbmc.Monitor()
        while not self.session.cancelled.wait(0.25):
            if self.session.state == 'install':
                return
            if monitor.abortRequested() or not self.current():
                self.session.cancel()
                self.close()
                return

    def read_metadata(self):
        path = self.request_path
        if path.startswith('special://'):
            path = xbmcvfs.translatePath(path)
        return inspect(path, folder=self.folder, label=self.label, size_hint=self.size_hint,
                       cancel=self.session.cancelled.is_set)

    def apply_metadata(self, metadata):
        if self.session.cancelled.is_set() or not self.current():
            return
        self.setProperty('Preview.Title', metadata.name or metadata.file_name)
        self.setProperty('Preview.Author', metadata.author or metadata.kind)
        self.setProperty('Preview.Status', metadata.status)
        self.getControl(20).setText(details(metadata))
        if metadata.icon:
            self.getControl(10).setImage(metadata.icon, useCache=False)
        self.getControl(80).setEnabled(metadata.compatible)

    def load_metadata(self):
        try:
            metadata = self.read_metadata()
            if self.session.loaded(metadata):
                self.apply_metadata(metadata)
        except Exception:
            if not self.session.cancelled.is_set() and self.current():
                self.setProperty('Preview.Status', 'This file could not be previewed. Cancel returns to the file picker.')

    def verify_install(self):
        try:
            metadata = self.read_metadata()
            if self.session.checked(metadata) and self.current():
                self.accepted = True
                self.close()
            elif not self.session.cancelled.is_set() and self.current():
                metadata.status = 'This file changed. Review the updated preview before installing.'
                self.apply_metadata(metadata)
        except Exception:
            self.accepted = False
            self.session.cancel()
            self.close()

    def onClick(self, control_id):
        if control_id in (81, 82):
            self.session.cancel()
            self.close()
        elif (control_id == 80 and self.current() and
              (self.check_worker is None or not self.check_worker.is_alive()) and
              self.session.request_install()):
            self.getControl(80).setEnabled(False)
            self.setProperty('Preview.Status', 'Checking the selected file…')
            self.check_worker = threading.Thread(target=self.verify_install, name='InfinityZipPreviewCheck', daemon=True)
            self.check_worker.start()

    def onAction(self, action):
        if action.getId() in BACK_ACTIONS:
            self.session.cancel()
            self.close()

    def stop(self):
        self.session.cancelled.set()
        for worker in (self.worker, self.check_worker):
            if worker is not None and worker is not threading.current_thread():
                worker.join(timeout=1.0)


def main():
    parent = None
    nonce = ''
    dialog = None
    try:
        if len(sys.argv) != 2 or not sys.argv[1].isdigit():
            return
        parent_id = int(sys.argv[1])
        if parent_id <= 0 or parent_id > 0x7fffffff or parent_id & 0xffff != 10126:
            return
        parent = xbmcgui.Window(parent_id)
        nonce = parent.getProperty(PREFIX + 'Nonce')
        if (not nonce.isdigit() or not int(nonce) or len(nonce) > 20 or
                parent.getProperty(PREFIX + 'NativeVersion') != 'v1' or
                parent.getProperty(PREFIX + 'OptIn') != 'v1' or xbmc.getSkinDir() != 'skin.infinity.diggz'):
            return
        request_path = parent.getProperty(PREFIX + 'Path')
        if not request_path or len(request_path) > 8192:
            return
        hint = parent.getProperty(PREFIX + 'Size')
        size_hint = int(hint) if hint.isdigit() and len(hint) <= 20 else None
        skin_path = xbmcvfs.translatePath('special://skin')
        dialog = PreviewDialog('InfinityFilePreview.xml', skin_path, 'Default', '1080i',
                               parent=parent, parent_id=parent_id, nonce=nonce, request_path=request_path,
                               folder=parent.getProperty(PREFIX + 'Folder') == 'true',
                               label=parent.getProperty(PREFIX + 'Label'), size_hint=size_hint)
        dialog.doModal()
        if dialog.accepted and dialog.current() and not dialog.session.cancelled.is_set():
            parent.setProperty(PREFIX + 'AcceptNonce', nonce)
            # Only trusted integer window/control IDs enter the command. Native validation
            # checks the nonce and still-selected ZIP before the original installer runs.
            xbmc.executebuiltin(f'SendClick({parent_id},9411)', wait=True)
    except Exception:
        xbmc.log('Infinity file preview could not open; original browsing remains available.', xbmc.LOGWARNING)
    finally:
        if dialog is not None:
            dialog.stop()
        if parent is not None:
            try:
                if nonce and parent.getProperty(PREFIX + 'Nonce') == nonce:
                    if dialog is not None and not dialog.accepted:
                        parent.setFocusId(450)  # Native ZIP browsing always uses the existing list view.
                    for key in ('Active', 'Nonce', 'AcceptNonce', 'Path', 'Label', 'Folder', 'Size'):
                        parent.clearProperty(PREFIX + key)
            except Exception:
                pass
        dialog = None


if __name__ == '__main__':
    main()
