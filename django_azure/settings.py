from django.conf import settings


AZURE_ACCOUNT_NAME = getattr(settings, 'AZURE_ACCOUNT_NAME', None)
AZURE_ACCOUNT_KEY = getattr(settings, 'AZURE_ACCOUNT_KEY', None)
AZURE_DEFAULT_CONTAINER = getattr(settings, 'AZURE_DEFAULT_CONTAINER', None)
AZURE_TEST_CONTAINER = getattr(settings, 'AZURE_TEST_CONTAINER', None)
AZURE_STATIC_FILES_CONTAINER = getattr(settings, 'AZURE_STATIC_FILES_CONTAINER', None)
AZURE_CDN_HOST = getattr(settings, 'AZURE_CDN_HOST', None)
AZURE_DEFAULT_PROTOCOL = getattr(settings, 'AZURE_DEFAULT_PROTOCOL', 'https')
AZURE_BLOB_OVERWRITE = getattr(settings, 'AZURE_BLOB_OVERWRITE', True)
AZURE_GZIPPED_CONTENT = getattr(settings, 'AZURE_GZIPPED_CONTENT', False)
AZURE_GZIPPED_CONTENT_TYPES = getattr(settings, 'AZURE_GZIPPED_CONTENT_TYPES',
                                      ('text/css', 'text/javascript',
                                       'application/javascript',
                                       'application/x-javascript'))

TIMESTAMP_FORMAT = u'%a, %d %b %Y %H:%M:%S %Z'
