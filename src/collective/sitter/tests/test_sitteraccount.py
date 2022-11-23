from ..testing import SITTER_FUNCTIONAL_TESTING
from ..testing import TestCase


class TestSitterAccountView(TestCase):
    layer = SITTER_FUNCTIONAL_TESTING

    def setUp(self):
        super().setUp()
        self.portal_url = self.portal.absolute_url()
        self.account_url = f'{self.portal_url}/{self.sitter_folder_name}/account'

    def _accept_agb(self):
        self.browser.open(f'{self.portal_url}/{self.sitter_folder_name}/signupview')
        self.browser.getControl(name='form.button.Accept').click()

    def _create_sitter(self, nickname='not', details='this is a test'):
        self.browser.open(f'{self.portal_url}/{self.sitter_folder_name}/++add++sitter')
        form = self.browser.getForm('form')
        form.getControl(name='form.widgets.nickname').value = nickname
        form.getControl(name='form.widgets.details').value = details
        form.getControl(name='form.buttons.save').click()

    def _submit_sitter_entry(self, object_name):
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/{object_name}/transition?workflow_action=submit'
        )
        self.browser.open(url)

    def _delete_sitter_entry(self, object_name):
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/{object_name}/transition?workflow_action=delete'
        )
        self.browser.open(url)

    def _recycle_sitter_entry(self, object_name):
        url = (
            f'{self.portal_url}/{self.sitter_folder_name}'
            f'/{object_name}/transition?workflow_action=recycle'
        )
        self.browser.open(url)

    def _go_to_account_page(self):
        self.browser.open(self.account_url)

    def test_sitteraccount_sitter_view(self):
        self.login_test_user()
        self._go_to_account_page()

        self.assertIn('<h1>Mein Babysittereintrag</h1>', self.browser.contents)

    def test_sitteraccount_sitter_view_next_steps_accept(self):
        self.login_test_user()
        self._go_to_account_page()

        self.assertIn(
            'Bitte akzeptieren Sie die Nutzungsbedingungen.', self.browser.contents
        )

        self._accept_agb()
        self._go_to_account_page()

        self.assertIn('Bitte geben Sie einige Daten zu sich an.', self.browser.contents)

        self._create_sitter(nickname='Testfirst', details='this is a sitter')
        own_sitterobject_name = 'testfirst'
        self._go_to_account_page()

        self.assertIn('Einreichen', self.browser.contents)

        self._submit_sitter_entry(own_sitterobject_name)
        self._go_to_account_page()

        self.assertIn('Warten auf Freigabe', self.browser.contents)

        self._delete_sitter_entry(own_sitterobject_name)
        self._go_to_account_page()

        self.assertIn('Eintrag gelöscht', self.browser.contents)

        self._recycle_sitter_entry(own_sitterobject_name)
        self._go_to_account_page()

        self.assertIn('Einreichen', self.browser.contents)


class TestSitterManagerView(TestCase):
    layer = SITTER_FUNCTIONAL_TESTING

    def setUp(self):
        super().setUp()
        self.portal_url = self.portal.absolute_url()
        self.account_url = f'{self.portal_url}/{self.sitter_folder_name}/sittermanager'

    def _go_to_account_page(self):
        self.browser.open(self.account_url)

    def test_sittermanager_view(self):
        self.login_site_owner()
        self._go_to_account_page()

        self.assertIn('<h1>Sittermanager</h1>', self.browser.contents)
