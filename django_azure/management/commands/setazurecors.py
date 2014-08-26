import sys
from datetime import datetime
from azure.http import HTTPRequest
from azure import _convert_class_to_xml, WindowsAzureData, _get_request_body, \
        _int_or_none, _update_request_uri_query_local_storage
from azure.storage import _update_storage_header, _sign_storage_blob_request, \
    StorageServiceProperties
from azure.storage.blobservice import BlobService
from optparse import make_option
from django.core.management.base import NoArgsCommand, CommandError
from ... import settings as ls


class Command(NoArgsCommand):
    """
    This command sets the specified rule to Azure as the only CORS rule
    for the blob service.
    """
    option_list = NoArgsCommand.option_list + (
            make_option('--container', action='store',
                        default=ls.AZURE_DEFAULT_CONTAINER, dest='container',
                        help='Azure container destination'),
            make_option('--origins', action='append', default=[],
                        dest='origins',
                        help='The origins of the rule. '
                             ' Specify star ("*") for any origin.'),
            make_option('--methods', action='append',
                        dest='methods', default=[],
                        help='The request methods on which the rule will apply. '
                             'Specify one or more of GET, PUT etc.'),
            make_option('--maxage', action='store',
                        default=3600, dest='maxage',
                        help='The maximum amount time that a browser should cache '
                             'the preflight OPTIONS request. Default is 3600'),
            make_option('--disable', action='store_true',
                        default=False, dest='disable',
                        help='Set to disable cors rules '),)

    def handle_noargs(self, **options):
        self.set_options(**options)

        if not self.disable:
            if not ls.AZURE_ACCOUNT_NAME:
                raise CommandError('AZURE_ACCOUNT_NAME setting is missing')
            if not ls.AZURE_ACCOUNT_KEY:
                raise CommandError('AZURE_ACCOUNT_KEY setting is missing')
            if not self.origins:
                raise CommandError('Specify at least one origin')
            if not self.methods:
                raise CommandError('Specify at least one method')

        class CorsRule(WindowsAzureData):
            def __init__(self, origins, methods, maxage):
                self.allowed_origins = ','.join(origins)
                self.allowed_methods = ','.join(methods)
                self.allowed_headers = ''
                self.exposed_headers = ''
                self.max_age_in_seconds = maxage

        class Cors(WindowsAzureData):
            def __init__(self, rules):
                self.cors = rules

        blob_service = BlobService(ls.AZURE_ACCOUNT_NAME, ls.AZURE_ACCOUNT_KEY,
                                   ls.AZURE_DEFAULT_PROTOCOL)

        cors_rule = CorsRule(self.origins, self.methods, self.maxage)
        service_properties = blob_service.get_blob_service_properties()
        self.stdout.write('--FOUND PROPERTIES--')
        self.stdout.write(_convert_class_to_xml(service_properties))

        cors_properties = StorageServiceProperties()
        if not self.disable:
            cors_properties.cors = Cors([cors_rule])
        else:
            cors_properties.cors = Cors([])

        cors_properties.metrics = None
        cors_properties.logging = None
        self.stdout.write('')
        self.stdout.write('--NEW PROPERTIES--')
        self.stdout.write(_convert_class_to_xml(cors_properties))

        # As of the latest version, one can only send 
        # a part of the properties and the rest will stay intact
        # http://msdn.microsoft.com/en-us/library/azure/hh452235.aspx
        self.set_properties(blob_service, cors_properties)

    def set_properties(self, blob_service, storage_service_properties):
        """
        Override API methods to change the API version and send the right
        headers
        """
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = blob_service._get_host()
        request.path = '/?restype=service&comp=properties'
        request.query = [('timeout', _int_or_none(None))]
        request.body = _get_request_body(
            _convert_class_to_xml(storage_service_properties))
        request.path, request.query = _update_request_uri_query_local_storage(
            request, blob_service.use_local_storage)
        request.headers = self.get_request_headers(
            request, blob_service.account_name, blob_service.account_key)

        try:
            if blob_service._batchclient is not None:
                return blob_service._batchclient.insert_request_to_batch(request)
            else:
                resp = blob_service._filter(request)

            if sys.version_info >= (3,) and isinstance(resp, bytes) and \
                'UTF-8':
                resp = resp.decode('UTF-8')

        except:
            raise

        return resp

    def set_options(self, **options):
        """
        Set instance variables based on an options dict
        """
        self.origins = options['origins'] or []
        self.methods = options['methods']
        self.maxage = options['maxage']
        self.disable = options['disable']

    def get_request_headers(self, request, account_name, account_key):
        """
        We need to do most of the wirk by hand here, because we first
        have to patch the version header and then sign the request.
        """
        request = _update_storage_header(request)

        # replace the api version
        for r in request.headers:
            if r[0] == 'x-ms-version':
                request.headers.remove(r)
                break

        request.headers.append(('x-ms-version', '2013-08-15'))

        current_time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        request.headers.append(('x-ms-date', current_time))
        request.headers.append(('Content-Type', 'application/octet-stream Charset=UTF-8'))
        request.headers.append(('Authorization', _sign_storage_blob_request(request, 
                                                    account_name, account_key)))
        return request.headers
