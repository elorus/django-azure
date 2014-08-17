import os
from django.contrib.staticfiles.management.commands import collectstatic
from django.contrib.staticfiles import storage
from django.utils.encoding import smart_text
from django.utils.functional import LazyObject
from ...storage import CachedAzureStorage


class Command(collectstatic.Command):
    cached = False

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        if self._is_cached_storage():
            self.storage = storage.staticfiles_storage.local_storage
            self.remote_storage = storage.staticfiles_storage
            self.cached = True

    def _clear_storage(self, path, storage):
        """
        Deletes the given relative path using the storage backend.
        """
        dirs, files = storage.listdir(path)
        for f in files:
            fpath = os.path.join(path, f)
            if self.dry_run:
                self.log("Pretending to delete '%s'" %
                         smart_text(fpath), level=1)
            else:
                self.log("Deleting '%s'" % smart_text(fpath), level=1)
                storage.delete(fpath)
        for d in dirs:
            self._clear_storage(os.path.join(path, d), storage)

    def _is_cached_storage(self):
        if issubclass(storage.staticfiles_storage.__class__, LazyObject):
            static_storage = storage.staticfiles_storage._wrapped
        else:
            static_storage = storage.staticfiles_storage
        return isinstance(static_storage, CachedAzureStorage)

    def clear_dir(self, path):
        """
        Override method from collectstatic to delete all files from both
        remote and local storages.
        """
        if self.cached:
            self._clear_storage(path, self.storage)
            self._clear_storage(path, self.remote_storage)
        else:
            super(Command, self).clear_dir(path)

    def copy_file(self, path, prefixed_path, source_storage):
        """
        Override method from collectstatic to copy file in both
        remote and local storages.
        """
        # Skip this file if it was already copied earlier
        if prefixed_path in self.copied_files:
            return self.log("Skipping '%s' (already copied earlier)" % path)
        # Delete the target file if needed or break
        if not self.delete_file(path, prefixed_path, source_storage):
            return
        # The full path of the source file
        source_path = source_storage.path(path)
        # Finally start copying
        if self.dry_run:
            self.log("Pretending to copy '%s'" % source_path, level=1)
        else:
            self.log("Copying '%s'" % source_path, level=1)
            if self.local:
                full_path = self.storage.path(prefixed_path)
                try:
                    os.makedirs(os.path.dirname(full_path))
                except OSError:
                    pass
            with source_storage.open(path) as source_file:
                if self.cached:
                    self.remote_storage.save(prefixed_path, source_file)
                else:
                    self.storage.save(prefixed_path, source_file)
        if not prefixed_path in self.copied_files:
            self.copied_files.append(prefixed_path)
