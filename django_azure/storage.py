import mimetypes
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.files.storage import Storage, get_storage_class
from azure import WindowsAzureMissingResourceError
from azure.storage.blobservice import BlobService
from . import settings as ls


class AzureStorage(Storage):
    account_name = ls.AZURE_ACCOUNT_NAME
    account_key = ls.AZURE_ACCOUNT_KEY

    def __init__(self, container=ls.AZURE_DEFAULT_CONTAINER,
            cdn_host=ls.AZURE_CDN_HOST, protocol=ls.AZURE_DEFAULT_PROTOCOL):
        self._service = None
        self.container = container
        self.cdn_host = cdn_host
        self.protocol = protocol

    def _clean_name(self, name):
        return name.replace("\\", "/")

    def _get_properties(self, name):
        return self.service.get_blob_properties(self.container, name)

    def _open(self, name, mode='rb'):
        return ContentFile(self.service.get_blob(self.container, name))

    def _save(self, name, content):
        if hasattr(content.file, 'content_type'):
            content_type = content.file.content_type
        else:
            content_type = mimetypes.guess_type(name)[0] or \
                    u'application/octet-stream'

        self.service.put_blob(self.container, name, content.read(),
                              x_ms_blob_type='BlockBlob',
                              x_ms_blob_content_type=content_type)
        return name

    def delete(self, name):
        try:
            self.service.delete_blob(self.container, name)
        except WindowsAzureMissingResourceError:
            pass

    def exists(self, name):
        try:
            self._get_properties(name)
        except WindowsAzureMissingResourceError:
            return False
        else:
            return True

    def get_available_name(self, name):
        if ls.AZURE_BLOB_OVERWRITE:
            return self._clean_name(name)
        return super(AzureStorage, self).get_available_name(name)

    def listdir(self, path):
        dirs, files = set(), []
        base_parts = path.split("/") if path and path != '' else []
        for blob in self.service.list_blobs(self.container, 
                prefix=path if path != '' else None):
            parts = blob.name.split("/")[len(base_parts):]
            if len(parts) == 1:
                files.append(parts[-1])
            elif len(parts) > 1:
                dirs.add(parts[0])
        return (list(dirs), files)

    def modified_time(self, name):
        return datetime.strptime(self._get_properties(name)['last-modified'],
                                 ls.TIMESTAMP_FORMAT)

    @property
    def service(self):
        if self._service is None:
            self._service = BlobService(self.account_name,
                    self.account_key, self.protocol)
        return self._service

    def size(self, name):
        return len(self._open(name))

    def url(self, name):
        return '{0}://{1}/{2}/{3}'.format(self.protocol, self.cdn_host,
                                          self.container, name) \
                if self.cdn_host else self.service.make_blob_url(
                        container_name=self.container, blob_name=name)


class StaticFilesAzureStorage(AzureStorage):
    def __init__(self, *args, **kwargs):
        super(StaticFilesAzureStorage, self).__init__(*args, **kwargs)
        self.container = ls.AZURE_STATIC_FILES_CONTAINER


class CachedAzureStorage(StaticFilesAzureStorage):
    """
    Azure storage backend that saves the files locally, too.
    """
    def __init__(self, *args, **kwargs):
        super(CachedAzureStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
                'compressor.storage.CompressorFileStorage')()

    def save(self, name, content):
        name = super(CachedAzureStorage, self).save(name, content)
        self.local_storage._save(name, content)
        return name
