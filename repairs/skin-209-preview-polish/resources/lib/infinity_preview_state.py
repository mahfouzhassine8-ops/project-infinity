"""One preview session. Cancellation and late worker results cannot trigger installation."""
import threading
from infinity_zip_metadata import same_metadata


class Session:
    def __init__(self):
        self.lock = threading.Lock()
        self.cancelled = threading.Event()
        self.state = 'loading'
        self.metadata = None

    def loaded(self, metadata):
        with self.lock:
            if self.state != 'loading' or self.cancelled.is_set():
                return False
            self.metadata = metadata
            self.state = 'ready'
            return True

    def request_install(self):
        with self.lock:
            if self.state != 'ready' or not self.metadata or not self.metadata.compatible or self.cancelled.is_set():
                return False
            self.state = 'checking'
            return True

    def checked(self, current):
        with self.lock:
            if self.state != 'checking' or self.cancelled.is_set():
                return False
            if same_metadata(self.metadata, current):
                self.state = 'install'
                return True
            self.metadata = current
            self.state = 'ready'
            return False

    def cancel(self):
        with self.lock:
            self.cancelled.set()
            self.state = 'closed'
