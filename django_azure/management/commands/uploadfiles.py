import os
from optparse import make_option
from django.conf import settings
from django.contrib.staticfiles.utils import matches_patterns
from django.core.management.base import NoArgsCommand, CommandError
from ... import settings as ls
from ...storage import AzureStorage


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
            make_option('--source', action='store', 
                        default=settings.MEDIA_ROOT, dest='source',
                        help='Local path to source folder'),
            make_option('--container', action='store',
                        default=ls.AZURE_DEFAULT_CONTAINER, dest='container',
                        help='Azure container destination'),
            make_option('-i', '--ignore', action='append', default=[],
                        dest='ignore_patterns', metavar='PATTERN',
                        help="Ignore files matching this patterns"),
            make_option('--no-default-ignore', action='store_false',
                        dest='use_default_ignore_patterns', default=True,
                        help="Don't ignore the common private patterns "
                                "'.*' and '*~'."),
            make_option('--dir', action='store', dest='dir',
                        help="Directory to upload files in."))

    def handle_noargs(self, **options):
        self.set_options(**options)
        if not os.path.isdir(self.source):
            raise CommandError('Non existing local path: %s' % self.source)
        if not hasattr(settings, 'AZURE_ACCOUNT_NAME'):
            raise CommandError('AZURE_ACCOUNT_NAME setting is missing')
        if not hasattr(settings, 'AZURE_ACCOUNT_KEY'):
            raise CommandError('AZURE_ACCOUNT_KEY setting is missing')
        if self.container is None and not hasattr(settings, 'AZURE_DEFAULT_CONTAINER'):
            raise CommandError('AZURE_DEFAULT_CONTAINER setting is missing')

        self.log(u'Starting uploading from "%s" to Azure Storage '
                 u'container "%s"' % (self.source, self.container))

        storage = AzureStorage(container=self.container)
        uploaded_files = []
        for root, dirs, files in os.walk(self.source): #@UnusedVariable
            for f in files:
                if matches_patterns(f, self.ignore_patterns):
                    continue
                path = os.path.join(root, f)
                blob_name = os.path.relpath(path, self.source).replace('\\', '/')
                if self.dir:
                    blob_name = os.path.join(self.dir, blob_name)
                self.log(u'uploading %s...' % blob_name)
                try:
                    with open(path, 'rb') as source_file:
                        storage.save(blob_name, source_file)
                except Exception as e:
                    self.log(u'upload aborted...')
                    self.log(str(e), 3)
                    return
                else:
                    uploaded_files.append(blob_name)
        self.stdout.write(u'%s files uploaded.' % len(uploaded_files))

    def log(self, msg, level=2):
        """
        Small log helper
        """
        if self.verbosity >= level:
            self.stdout.write(msg)

    def set_options(self, **options):
        """
        Set instance variables based on an options dict
        """
        self.source = options['source'] or settings.MEDIA_ROOT
        self.container = options['container'] or ls.AZURE_DEFAULT_CONTAINER
        self.verbosity = int(options.get('verbosity', 1))
        ignore_patterns = options['ignore_patterns']
        if options['use_default_ignore_patterns']:
            ignore_patterns += ['.*', '*~']
        self.ignore_patterns = list(set(ignore_patterns))
        self.dir = options['dir']
