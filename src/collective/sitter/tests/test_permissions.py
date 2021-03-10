from ..testing import SITTER_FUNCTIONAL_TESTING
from ..testing import TestCase
from plone import api
from zExceptions import Unauthorized

import unittest


class TestPermissionsBase(TestCase):
    layer = SITTER_FUNCTIONAL_TESTING

    def setUp(self):
        super().setUp()
        self.portal_url = self.portal.absolute_url()

    def _accept_agb(self):
        self.browser.open(f'{self.portal_url}/{self.sitter_folder_name}/signupview')
        self.browser.getControl(name='form.button.Accept').click()

    def _create_sitter(self, nickname='not', details='this is a test'):
        self.browser.open(f'{self.portal_url}/{self.sitter_folder_name}/++add++sitter')
        form = self.browser.getForm('form')
        form.getControl(name='form.widgets.nickname').value = nickname
        form.getControl(name='form.widgets.details').value = details
        form.getControl(name='form.buttons.save').click()


class TestPermissionsForeign(TestPermissionsBase):
    def setUp(self):
        super().setUp()
        self.login_site_owner()
        self._accept_agb()
        self._create_sitter()
        self.login_test_user()

    def test_notAllowedToEditForeignSitterObjects(self):
        url = f'{self.portal_url}/{self.sitter_folder_name}/not/edit'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToSubmitForeignSitterObjects(self):
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/not/content_status_modify?workflow_action=submit'
        )
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToPublishForeignSitterObjects(self):
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/not/content_status_modify?workflow_action=publish'
        )
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToRejectForeignSitterObjects(self):
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/not/content_status_modify?workflow_action=reject'
        )
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToRetractForeignSitterObjects(self):
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/not/content_status_modify?workflow_action=retract'
        )
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_notAllowedToDeleteForeignObject(self):
        url = f'{self.portal_url}/{self.sitter_folder_name}/not/delete_confirmation'
        self.assertRaises(Unauthorized, self.browser.open, url)


class TestPermissions(TestPermissionsBase):
    def setUp(self):
        super().setUp()
        self.login_test_user()

    def test_notAllowedToPublishOwnSitterObjects(self):
        self._accept_agb()
        self._create_sitter(nickname='Testfirst', details='this is a sitter')
        own_sitterobject_name = 'testfirst'
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/{own_sitterobject_name}/edit'
        )
        self.browser.open(url)
        self.assertIn('Testfirst', self.browser.contents)
        self.assertIn('this is a sitter', self.browser.contents)

        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/{own_sitterobject_name}/content_status_modify?workflow_action=publish'
        )
        self.browser.open(url)
        sitter = self.sitter_folder[own_sitterobject_name]
        state = api.content.get_state(sitter)
        self.assertEqual('private', state)

    @unittest.skip('XXX needs to be fixed')
    def test_notAllowedToDeleteOwnObjects(self):
        self._accept_agb()
        self._create_sitter(nickname='Testfirst', details='this is a sitter')
        own_sitterobject_name = 'testfirst'
        sitter_obj = self.sitter_folder[own_sitterobject_name]
        self.assertIsNotNone(sitter_obj)
        self.login_site_owner()
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/{own_sitterobject_name}/delete_confirmation'
        )
        self.browser.open(url)
        self.assertIn('destructive', self.browser.contents)
        self.assertRaises(Unauthorized, self.browser.getControl('Delete').click)

    def test_memberDoesNotHaveManageSittersPermission(self):
        ok = dict(name='Member', selected='SELECTED') in self.portal.rolesOfPermission(
            'collective.sitter: Manage sitters'
        )
        self.assertFalse(ok)

    def test_memberCanNotAccessDeleteSitterView(self):
        url = f'{self.portal_url}/{self.sitter_folder_name}/deletesitter'
        self.assertRaises(Unauthorized, self.browser.open, url)

    def test_siteownerCanAccessDeleteSitterView(self):
        url = f'{self.portal_url}/{self.sitter_folder_name}/deletesitter'
        self.login_site_owner()
        self.browser.open(url)
        self.assertIn('delete_private', self.browser.contents)
        self.assertIn('delete_deleting', self.browser.contents)
