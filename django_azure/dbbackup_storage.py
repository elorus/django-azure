import os
from tempfile import SpooledTemporaryFile
from django.conf import settings
from azure.storage.blobservice import BlobService
try:
    from dbbackup.storage.base import BaseStorage, StorageError
except:
    pass


class Storage(BaseStorage):
    """
    Azure Storage for django-dbbackup. In settings:
    DBBACKUP_STORAGE = 'django_azure.dbbackup_storage'
    """
    AZURE_ACCOUNT_NAME = getattr(settings, 'DBBACKUP_AZURE_ACCOUNT_NAME', None)
    AZURE_ACCOUNT_KEY = getattr(settings, 'DBBACKUP_AZURE_ACCOUNT_KEY', None)
    AZURE_CONTAINER = getattr(settings, 'DBBACKUP_AZURE_CONTAINER', None)
    AZURE_DOMAIN = getattr(settings, 'DBBACKUP_AZURE_DOMAIN', '.blob.core.windows.net')
    AZURE_PROTOCOL = getattr(settings, 'DBBACKUP_AZURE_PROTOCOL', 'https')
    AZURE_DIRECTORY = getattr(settings, 'DBBACKUP_AZURE_DIRECTORY', 'django-dbbackups')

    def __init__(self, server_name=None):
        self._check_errors()
        self.name = 'Microsoft Azure'
        self._service = None
        BaseStorage.__init__(self)

    def _check_errors(self):
        if not self.AZURE_ACCOUNT_NAME:
            raise StorageError('db-backup azure storage requires '
                               'DBBACKUP_AZURE_ACCOUNT_NAME to be '
                               'defined in settings.')
        if not self.AZURE_ACCOUNT_KEY:
            raise StorageError('db-backup azure storage requires '
                               'DBBACKUP_AZURE_ACCOUNT_KEY to be '
                               'defined in settings.')
        if not self.AZURE_CONTAINER:
            raise StorageError('db-backup azure storage requires '
                               'DBBACKUP_AZURE_CONTAINER to be '
                               'defined in settings.')

    @property
    def service(self):
        if self._service is None:
            self._service = BlobService(self.AZURE_ACCOUNT_NAME,
                    self.AZURE_ACCOUNT_KEY, self.AZURE_PROTOCOL,
                    self.AZURE_DOMAIN)
        return self._service

    def backup_dir(self):
        return self.AZURE_DIRECTORY

    def delete_file(self, filepath):
        self.service.delete_blob(self.AZURE_CONTAINER, filepath)

    def list_directory(self):
        return [blob.name for blob in self.service.list_blobs(
                self.AZURE_CONTAINER, prefix=self.AZURE_DIRECTORY)]

    def write_file(self, filehandle):
        filepath = os.path.join(self.AZURE_DIRECTORY, filehandle.name)
        filehandle.seek(0)
        self.service.put_block_blob_from_file(self.AZURE_CONTAINER,
                                              filepath, filehandle)

    def read_file(self, filepath):
        filepath = os.path.join(self.AZURE_DIRECTORY, filepath)
        filehandle = SpooledTemporaryFile(max_size=10 * 1024 * 1024)
        self.service.get_blob_to_file(self.AZURE_CONTAINER, filepath,
                                      filehandle)
        return filehandle
