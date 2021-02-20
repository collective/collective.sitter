from ..testing import SITTER_INTEGRATION_TESTING
from ..testing import TestCase
from DateTime import DateTime
from plone import api
from zope.component import getMultiAdapter


class TestDeleteSitter(TestCase):
    layer = SITTER_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.login_site_owner()

        for name, state in [
            ('sitter-01', 'private'),
            ('sitter-02', 'private'),
            ('sitter-03', 'deleting'),
            ('sitter-04', 'deleting'),
            ('sitter-05', 'pending'),
            ('sitter-06', 'published'),
        ]:
            sitter = api.content.create(
                container=self.sitter_folder,
                type='sitter',
                id=name,
            )
            api.content.transition(sitter, to_state=state)

        private_days = api.portal.get_registry_record(
            'sitter.days_until_deletion_of_private_sitters', default=100
        )
        del_days = api.portal.get_registry_record(
            'sitter.days_until_deletion_of_deleting_sitters', default=60
        )

        sitter_01 = self.sitter_folder['sitter-01']
        self.set_modifaction_date(sitter_01, DateTime() - private_days)

        sitter_02 = self.sitter_folder['sitter-02']
        self.set_modifaction_date(sitter_02, DateTime() - (private_days - 1))

        sitter_03 = self.sitter_folder['sitter-03']
        self.set_modifaction_date(sitter_03, DateTime() - del_days)

        sitter_04 = self.sitter_folder['sitter-04']
        self.set_modifaction_date(sitter_04, DateTime() - (del_days - 1))

        context = self.sitter_folder
        request = getattr(context, 'REQUEST', None)
        self.view_under_test = getMultiAdapter((context, request), name='deletesitter')
        self.assertIsNotNone(self.view_under_test)
        self.view_under_test()

    def set_modifaction_date(self, obj, date=DateTime() - 100):
        obj.setModificationDate(date)
        od = obj.__dict__
        od['notifyModified'] = lambda *args: None
        obj.reindexObject()
        del od['notifyModified']

    def test_findPrivateSitters(self):
        result = self.view_under_test.find_private_sitters()
        self.assertEqual(1, len(result))

    def test_findDeletingSitters(self):
        result = self.view_under_test.find_deleting_sitters()
        self.assertTrue(len(result) == 1)

    def test_deletePrivate(self):
        self.assertEqual(6, len(self.sitter_folder.getFolderContents()))
        self.view_under_test.delete_private_sitters()
        self.assertEqual(5, len(self.sitter_folder.getFolderContents()))

    def test_deleteDeleting(self):
        self.assertEqual(6, len(self.sitter_folder.getFolderContents()))
        self.view_under_test.delete_deleting_sitters()
        self.assertEqual(5, len(self.sitter_folder.getFolderContents()))
