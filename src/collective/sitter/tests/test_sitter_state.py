from ..sitterstate import ISitterState
from ..testing import SITTER_INTEGRATION_TESTING
from ..testing import TestCase
from plone import api


class TestSitterState(TestCase):
    layer = SITTER_INTEGRATION_TESTING

    def get_sitter_state(self):
        return ISitterState(self.sitter_folder)


class TestSitterStateNotLoggedIn(TestSitterState):
    def setUp(self):
        super().setUp()
        self.logout()
        self.sitter_state = self.get_sitter_state()

    def test_isLoggedIn(self):
        self.assertFalse(self.sitter_state.is_logged_in())

    def test_hasAccepted(self):
        self.assertFalse(self.sitter_state.has_accepted())

    def test_isCreated(self):
        self.assertFalse(self.sitter_state.is_created())


class TestSitterStateLoggedIn(TestSitterState):
    def setUp(self):
        super().setUp()
        self.login_test_user()
        self.sitter_state = self.get_sitter_state()

    def test_isLoggedIn(self):
        self.assertTrue(self.sitter_state.is_logged_in())

    def test_hasAccepted(self):
        self.assertFalse(self.sitter_state.has_accepted())

    def test_isCreated(self):
        self.assertFalse(self.sitter_state.is_created())

    def test_isDeleted(self):
        self.assertFalse(self.sitter_state.is_deleted())


class TestSitterStateAccepted(TestSitterState):
    def setUp(self):
        super().setUp()
        self.login_test_user()
        user = api.user.get_current()
        user.setMemberProperties(mapping={'accepted_sitter_agreement': True})
        self.sitter_state = self.get_sitter_state()

    def test_isLoggedIn(self):
        self.assertTrue(self.sitter_state.is_logged_in())

    def test_hasAccepted(self):
        self.assertTrue(self.sitter_state.has_accepted())

    def test_isCreated(self):
        self.assertFalse(self.sitter_state.is_created())

    def test_getSitter(self):
        this_sitter = self.sitter_state.get_sitter()
        self.assertIsNone(this_sitter)

    def test_isDeleted(self):
        self.assertFalse(self.sitter_state.is_deleted())


class TestSitterStateSitterCreated(TestSitterState):
    def setUp(self):
        super().setUp()
        self.login_site_owner()
        self.portal.portal_workflow.setDefaultChain('plone_workflow')

        self.login_test_user()
        sitter = api.content.create(
            container=self.sitter_folder,
            type='sitter',
            id='mary',
        )
        api.content.transition(sitter, to_state='private')

        user = api.user.get_current()
        user.setMemberProperties(mapping={'accepted_sitter_agreement': True})
        self.sitter_state = self.get_sitter_state()

    def test_isLoggedIn(self):
        self.assertTrue(self.sitter_state.is_logged_in())

    def test_hasAccepted(self):
        self.assertTrue(self.sitter_state.has_accepted())

    def test_isCreated(self):
        self.assertTrue(self.sitter_state.is_created())

    def test_getState(self):
        self.assertEqual('private', self.sitter_state._get_workflow_state())

    def test_isSubmitted(self):
        self.assertFalse(self.sitter_state.is_submitted())

    def test_isPublished(self):
        self.assertFalse(self.sitter_state.is_published())

    def test_getSitter(self):
        this_sitter = self.sitter_state.get_sitter()
        self.assertEqual(this_sitter.getObject(), self.sitter_folder['mary'])

    def test_isDeleted(self):
        self.assertFalse(self.sitter_state.is_deleted())


class TestSitterStateSitterSubmitted(TestSitterStateSitterCreated):
    def setUp(self):
        super().setUp()
        self.this_sitter = self.sitter_folder['mary']
        api.content.transition(self.this_sitter, 'submit')

    def test_getState(self):
        self.assertEqual('pending', self.sitter_state._get_workflow_state())

    def test_isSubmitted(self):
        self.assertTrue(self.sitter_state.is_submitted())

    def test_isDeleted(self):
        self.assertFalse(self.sitter_state.is_deleted())


class TestSitterStatePublished(TestSitterStateSitterSubmitted):
    def setUp(self):
        super().setUp()

        self.logout()
        self.login_site_owner()
        api.content.transition(self.this_sitter, 'publish')
        self.logout()
        self.login_test_user()

    def test_getState(self):
        self.assertEqual('published', self.sitter_state._get_workflow_state())

    def test_isSubmitted(self):
        self.assertFalse(self.sitter_state.is_submitted())

    def test_isPublished(self):
        self.assertTrue(self.sitter_state.is_published())

    def test_isDeleted(self):
        self.assertFalse(self.sitter_state.is_deleted())


class TestSitterStateDeleted(TestSitterStateSitterCreated):
    def setUp(self):
        super().setUp()

        self.logout()
        self.login_site_owner()
        self.this_sitter = self.sitter_folder['mary']
        api.content.transition(self.this_sitter, 'delete')
        self.logout()
        self.login_test_user()

    def test_isDeleted(self):
        self.assertTrue(self.sitter_state.is_deleted())

    def test_getState(self):
        self.assertEqual('deleting', self.sitter_state._get_workflow_state())
