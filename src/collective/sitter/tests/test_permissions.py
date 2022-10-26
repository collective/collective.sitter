from ..testing import SITTER_FUNCTIONAL_TESTING
from ..testing import TestCase
from plone import api
from zExceptions import Unauthorized


class TestPermissionsBase(TestCase):
    layer = SITTER_FUNCTIONAL_TESTING

    def _accept_agb(self):
        self.browser.open(f'{self.sitter_folder_url}/signupview')
        self.browser.getControl(name='form.button.Accept').click()

    def _create_sitter(self, nickname='not', details='this is a test'):
        self.browser.open(f'{self.sitter_folder_url}/++add++sitter')
        form = self.browser.getForm('form')
        form.getControl(name='form.widgets.nickname').value = nickname
        form.getControl(name='form.widgets.details').value = details
        form.getControl(name='form.buttons.save').click()
        return nickname.lower()  # actually, title -> id


class TestPermissionsForeign(TestPermissionsBase):
    def setUp(self):
        super().setUp()
        self.login_site_owner()
        self._accept_agb()
        sitter_name = self._create_sitter()
        self.sitter_url = f'{self.sitter_folder_url}/{sitter_name}'
        self.login_test_user()

    def test_notAllowedToEditForeignSitterObjects(self):
        url = f'{self.sitter_url}/edit'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToSubmitForeignSitterObjects(self):
        url = f'{self.sitter_url}/content_status_modify?workflow_action=submit'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToPublishForeignSitterObjects(self):
        url = f'{self.sitter_url}/content_status_modify?workflow_action=publish'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToRejectForeignSitterObjects(self):
        url = f'{self.sitter_url}/content_status_modify?workflow_action=reject'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToRetractForeignSitterObjects(self):
        url = f'{self.sitter_url}/content_status_modify?workflow_action=retract'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToDeleteForeignObject(self):
        url = f'{self.sitter_url}/delete_confirmation'
        self.assertRaises(Unauthorized, self.browser.open, url)


class TestPermissions(TestPermissionsBase):
    def setUp(self):
        super().setUp()
        self.login_test_user()

    def test_notAllowedToPublishOwnSitterObjects(self):
        self._accept_agb()
        own_sitterobject_name = self._create_sitter(
            nickname='Testfirst', details='this is a sitter'
        )
        own_url = f'{self.sitter_folder_url}/{own_sitterobject_name}'

        self.browser.open(f'{own_url}/edit')
        self.assertIn('Testfirst', self.browser.contents)
        self.assertIn('this is a sitter', self.browser.contents)

        self.browser.open(f'{own_url}/content_status_modify?workflow_action=publish')
        sitter = self.sitter_folder[own_sitterobject_name]
        state = api.content.get_state(sitter)
        self.assertEqual('private', state)

    def test_memberDoesNotHaveManageSittersPermission(self):
        ok = dict(name='Member', selected='SELECTED') in self.portal.rolesOfPermission(
            'collective.sitter: Manage sitters'
        )
        self.assertFalse(ok)

    def test_memberCanNotAccessDeleteSitterView(self):
        url = f'{self.sitter_folder_url}/deletesitter'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_siteownerCanAccessDeleteSitterView(self):
        url = f'{self.sitter_folder_url}/deletesitter'
        self.login_site_owner()
        self.browser.open(url)
        self.assertIn('delete_private', self.browser.contents)
        self.assertIn('delete_deleting', self.browser.contents)
