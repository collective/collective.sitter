from ..browser.sitterfolder import DeletedLdapUsersService
from ..testing import SITTER_INTEGRATION_TESTING
from ..testing import TestCase
from plone import api
from zope.component import getMultiAdapter


class TestCheckCreator(TestCase):
    layer = SITTER_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.login_site_owner()

        for name, state in [
            ('sitter-01', 'published'),
            ('sitter-02', 'published'),
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

        self._set_creator(self.sitter_folder['sitter-01'], 'user1')
        self._set_creator(self.sitter_folder['sitter-02'], 'user27')
        self._set_creator(self.sitter_folder['sitter-03'], 'user2')
        self._set_creator(self.sitter_folder['sitter-04'], 'user28')

        context = self.sitter_folder
        request = getattr(context, 'REQUEST', None)
        self.view_under_test = getMultiAdapter((context, request), name='checkcreator')
        self.assertIsNotNone(self.view_under_test)
        self.view_under_test(deleted_ldap_users_service=FakeDeletedLdapUsersService())

    def _set_creator(self, obj, creator_name):
        obj.setCreators([creator_name])
        obj.reindexObject()

    def test_find_invalid_sitters(self):
        self.assertEqual('user1', self.sitter_folder['sitter-01'].Creator())
        self.assertEqual('user2', self.sitter_folder['sitter-03'].Creator())
        invalid_sitters = self.view_under_test.find_invalid_sitter_objects()
        self.assertEqual(2, len(invalid_sitters))

    def test_set_to_private(self):
        pwt = api.portal.get_tool('portal_workflow')
        state = pwt.getInfoFor(self.sitter_folder['sitter-01'], 'review_state')
        self.assertEqual('published', state)
        self.view_under_test.set_to_private()

        state = pwt.getInfoFor(self.sitter_folder['sitter-01'], 'review_state')
        self.assertEqual('private', state)
        service = self.view_under_test.deleted_ldap_users_service
        call_count = service.called_remove_user_from_list_of_deleted_users
        self.assertEqual(3, call_count)


class FakeDeletedLdapUsersService(DeletedLdapUsersService):
    def __init__(self):
        self._list_of_removed_users = ['user1', 'user2', 'user3']
        self.called_remove_user_from_list_of_deleted_users = 0

    @property
    def list_of_removed_users(self):
        return self._list_of_removed_users

    def remove_user_from_list_of_deleted_users(self, user):
        self.called_remove_user_from_list_of_deleted_users += 1
