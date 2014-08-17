from django.core.files.base import ContentFile
from django.test import SimpleTestCase
from . import settings as ls
from .storage import AzureStorage


class AzureStorageTestCase(SimpleTestCase):
    def setUp(self):
        self.storage = AzureStorage(container=ls.AZURE_TEST_CONTAINER)

    def test_listdir(self):
        """
        Tests the AzureStorage listdir method
        """
        (dirs, files) = self.storage.listdir(u'')
        self.assertListEqual(dirs, [])
        self.assertListEqual(files, [])
        # create dummy blobs
        self.storage.save(u'dummy-1/dummy-2/blob-1', ContentFile(u'1'))
        self.storage.save(u'dummy-1/blob-2', ContentFile(u'2'))
        self.storage.save(u'dummy-2/blob-3', ContentFile(u'3'))
        self.storage.save(u'dummy-2/blob-4', ContentFile(u'4'))
        self.storage.save(u'dummy-3/blob-5', ContentFile(u'5'))

        (dirs, files) = self.storage.listdir(u'')
        self.assertListEqual(dirs, [u'dummy-1', u'dummy-2', u'dummy-3'])
        self.assertListEqual(files, [])

        (dirs, files) = self.storage.listdir(u'dummy-1')
        self.assertListEqual(dirs, [u'dummy-2'])
        self.assertListEqual(files, [u'blob-2'])

        (dirs, files) = self.storage.listdir(u'dummy-1/dummy-2')
        self.assertListEqual(dirs, [])
        self.assertListEqual(files, [u'blob-1'])

        (dirs, files) = self.storage.listdir(u'dummy-2')
        self.assertListEqual(dirs, [])
        self.assertListEqual(files, [u'blob-3', u'blob-4'])

        # clean up dummy blobs
        self.storage.delete(u'dummy-1/dummy-2/blob-1')
        self.storage.delete(u'dummy-1/blob-2')
        self.storage.delete(u'dummy-2/blob-3')
        self.storage.delete(u'dummy-2/blob-4')
        self.storage.delete(u'dummy-3/blob-5')


    def test_storage(self):
        """
        Tests the AzureStorage basic operations
        """
        # test the AzureStorage exists method
        self.assertFalse(self.storage.exists(u'dummy-blob'))

        # test the AzureStorage save method
        self.storage.save('dummy-blob', ContentFile('dummy content'))
        self.assertTrue(self.storage.exists(u'dummy-blob'))

        # by default AzureStorage will overwrite existing blob
        self.assertEqual(self.storage.get_available_name(u'dummy-blob'),
                         u'dummy-blob')

        # test the AzureStorage open method
        blob = self.storage.open(u'dummy-blob')
        self.assertEqual(blob.read(), u'dummy content')
        blob.close()

        # test the AzureStorage size method
        self.assertEqual(self.storage.size(u'dummy-blob'), 13)

        # test the AzureStorage delete method
        self.storage.delete(u'dummy-blob')
        self.assertFalse(self.storage.exists(u'dummy-blob'))

    def test_url(self):
        """
        Tests the AzureStorage url method
        """
        self.storage.cdn_host = None
        self.assertEqual(self.storage.url(u'dummy-blob'),
                         '%s://%s.blob.core.windows.net/%s/dummy-blob' % 
                         (self.storage.protocol, self.storage.account_name,
                          self.storage.container))
        self.storage.cdn_host = u'dummy.com'
        self.assertEqual(self.storage.url(u'dummy-blob'),
                         '%s://dummy.com/%s/dummy-blob' % 
                         (self.storage.protocol, self.storage.container))
