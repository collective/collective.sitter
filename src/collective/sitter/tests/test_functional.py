from ..testing import SITTER_FUNCTIONAL_TESTING
from ..testing import SITTER_SELENIUM_TESTING
from ..testing import TestCase
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

import os
import transaction
import unittest


SEND_SUCCESSFULLY_MSG = 'Eine E-Mail an den Babysitter wurde erfolgreich versendet'


class BaseTestClass(TestCase):
    layer = SITTER_FUNCTIONAL_TESTING

    def setUp(self):
        super().setUp()
        self.login_site_owner()
        self.portal_url = self.portal.absolute_url()

        for name, state in [
            ('sitter-01', 'private'),
            ('sitter-02', 'private'),
            ('sitter-03', 'deleting'),
            ('sitter-04', 'deleting'),
            ('sitter-05', 'pending'),
            ('sitter-06', 'published'),
            ('sitter-07', 'published'),
        ]:
            sitter = api.content.create(
                container=self.sitter_folder,
                type='sitter',
                id=name,
            )
            api.content.transition(sitter, to_state=state)
        sitter = api.content.create(
            container=self.sitter_folder,
            type='Folder',
            id='hi',
        )
        api.content.transition(sitter, to_state='published')

        sitter = self.sitter_folder['sitter-06']
        sitter.nickname = 'Nickname'

        transaction.commit()

        self.assertIn(self.sitter_folder_name, self.portal)
        self.assertIsNotNone(self.sitter_folder)
        self.sitter_folder.title = 'Test Title'
        self.sitter_folder.vorlage = 'Hallo'
        self.assertIn('sitter-05', self.sitter_folder)
        sitter_07 = self.sitter_folder['sitter-07']
        sitter_07.nickname = 'Äh üö'
        transaction.commit()
        self.login_site_owner()


@unittest.skip('')
class TestRedirection(BaseTestClass):
    def _login_using_page(self):
        url = f'{self.portal_url}/{self.sitter_folder_name}/login'
        self.browser.open(url)
        username = TEST_USER_NAME
        pswd = TEST_USER_PASSWORD
        form = self.browser.getForm('login_form')
        form.getControl(name='__ac_name').value = username
        form.getControl(name='__ac_password').value = pswd
        btn = form.getControl(name='submit')
        print(btn)
        btn.click()

    def test_redirectionToAcceptAGBPage(self):
        self._login_using_page()
        self.assertIn('signupview', self.browser.url)
        self.assertIn('Accept', self.browser.contents)
        self.assertIn('Decline', self.browser.contents)

    def test_noRedirectionAgain(self):
        self._login_using_page()
        self.browser.getControl(name='form.button.Accept').click()
        self._login_using_page()
        self.assertIn(self.sitter_folder_name, self.browser.url)
        self.assertIn('Babysitter Liste filtern', self.browser.contents)


class BaseSeleniumTestClass(BaseTestClass):
    def setup_selenium(self):
        options = webdriver.FirefoxOptions()
        options.headless = not os.environ.get('WEBDRIVER_DEBUG')
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(10)  # seconds

    def selenium_login_test_user(self):
        self.url = f'{self.portal_url}/login'
        self.driver.get(self.url)
        self.driver.find_element_by_id('__ac_name').send_keys(TEST_USER_NAME)
        self.driver.find_element_by_id('__ac_password').send_keys(TEST_USER_PASSWORD)
        self.driver.find_element_by_name('submit').click()

    def selenium_login_site_owner(self):
        self.url = f'{self.portal_url}/login'
        self.driver.get(self.url)
        self.driver.find_element_by_id('__ac_name').send_keys(SITE_OWNER_NAME)
        self.driver.find_element_by_id('__ac_password').send_keys(SITE_OWNER_PASSWORD)
        self.driver.find_element_by_name('submit').click()


@unittest.skip('')
class TestHoneyPot(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.setup_selenium()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-06'
        self.driver.get(self.url)

    def test_honeypotfield_notfilled(self):
        self.driver.find_element_by_id('kontaktname').send_keys('KK')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('kontakttext').send_keys('hallo')
        self.driver.find_element_by_id('accepted').click()
        self.driver.find_element_by_id('sendcontact').click()
        self.assertIn(SEND_SUCCESSFULLY_MSG, self.driver.page_source)

    def test_honeypotfield_filled(self):
        self.driver.find_element_by_id('kontaktname').send_keys('KK')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('homepage').send_keys('http://example.org')
        self.driver.find_element_by_id('accepted').click()
        self.driver.find_element_by_id('kontakttext').send_keys('hallo')
        self.driver.find_element_by_id('sendcontact').click()

        self.assertIn(
            'Die E-Mail wurde !erfolgreich versendet', self.driver.page_source
        )

    def tearDown(self):
        self.driver.quit()


@unittest.skip('')
class TestTermsOfUse(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.setup_selenium()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-06'
        self.driver.get(self.url)

    def test_accepted_false(self):
        self.assertNotIn('Sie die Nutzungbedingungen', self.driver.page_source)
        self.driver.find_element_by_id('kontaktname').send_keys('KK')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('kontakttext').send_keys('hallo')
        self.driver.find_element_by_id('sendcontact').click()
        self.assertIn('Sie die Nutzungbedingungen', self.driver.page_source)

    def test_accepted_true(self):
        self.driver.find_element_by_id('kontaktname').send_keys('KK')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('accepted').click()
        self.driver.find_element_by_id('kontakttext').send_keys('hallo')
        self.driver.find_element_by_id('sendcontact').click()
        self.assertIn(SEND_SUCCESSFULLY_MSG, self.driver.page_source)

    def tearDown(self):
        self.driver.quit()


@unittest.skip('')
class TestSpecialChars(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.setup_selenium()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-07'
        self.driver.get(self.url)

    def test_specialchars(self):
        self.driver.find_element_by_id('kontaktname').send_keys('hä')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('accepted').click()
        self.driver.find_element_by_id('kontakttext').send_keys('hallo täst')
        self.driver.find_element_by_id('sendcontact').click()
        self.assertIn(SEND_SUCCESSFULLY_MSG, self.driver.page_source)


@unittest.skip('')
class TestRemovePortalMessage(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.setup_selenium()
        self.selenium_login_site_owner()
        # submit sitter entry:
        self.url = (
            f'{self.portal_url}/{self.sitter_folder_name}/sitter-01'
            f'/content_status_modify?workflow_action=submit'
        )
        self.driver.get(self.url)

    def test(self):
        self.assertNotIn('Item state changed.', self.driver.page_source)
        self.assertNotIn('Artikelstatus ge', self.driver.page_source)
        self.assertIn('Kontaktformular', self.driver.page_source)

    def tearDown(self):
        self.driver.quit()


class TestPortalActions(BaseTestClass):

    layer = SITTER_FUNCTIONAL_TESTING

    def test_manager_siteActionVisible(self):
        self.login_test_user()
        setRoles(self.portal, TEST_USER_ID, ['Member', 'Manager'])
        transaction.commit()

        url = f'{self.portal_url}/{self.sitter_folder_name}'
        self.browser.open(url)
        self.assertIn('portal-personaltools', self.browser.contents)
        self.assertIn('Log out', self.browser.contents)
        self.assertIn('test_user_1', self.browser.contents)
        self.assertIn('logout', self.browser.contents)

    @unittest.skip('')
    def test_testUser_siteActionNotVisible(self):
        self.login_test_user()
        url = f'{self.portal_url}/{self.sitter_folder_name}'
        self.browser.open(url)
        self.assertNotIn('test_user_1', self.browser.contents)
        self.assertIn('logout', self.browser.contents)

    def test_anonymous_noSiteActionNoLogout(self):
        self.logout()
        url = f'{self.portal_url}/{self.sitter_folder_name}'
        self.browser.open(url)
        self.assertNotIn('logout', self.browser.contents)


@unittest.skip('')
class TestReferer(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.setup_selenium()
        self.selenium_login_site_owner()

    def test_noReferer(self):
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-01'
        self.driver.get(self.url)
        back_link_element = self.driver.find_element_by_css_selector('a.btn-back')
        back_link_href = back_link_element.get_attribute('href')
        expected_url = self.sitter_folder.absolute_url()
        self.assertEqual(expected_url, back_link_href)

    def test_hasReferer(self):
        sitter_list_url = self.sitter_folder.absolute_url()
        self.driver.get(sitter_list_url)
        self.driver.find_element_by_css_selector(
            '#findsittersform > div > form > button'
        ).click()  # Fake searching
        expected_url = self.driver.current_url
        link = self.driver.find_element_by_css_selector(
            '#findsittersresult > div:nth-child(2) > '
            'div > div > div > div:nth-child(1) > h1 > a'
        )
        link.click()
        back_link_element = self.driver.find_element_by_css_selector('a.btn-back')
        back_link_href = back_link_element.get_attribute('href')
        self.assertEqual(expected_url, back_link_href)


@unittest.skip('')
class TestIsEditBarVisible(BaseSeleniumTestClass):
    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.setup_selenium()

    def test_userHasPermission_editbarShow(self):
        self.selenium_login_site_owner()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-07'
        self.driver.get(self.url)
        edit_bar = self.driver.find_element_by_css_selector('#edit-bar')
        self.assertIsNotNone(edit_bar)

    def test_userHasPermission_editbarNotShow(self):
        self.selenium_login_test_user()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-07'
        self.driver.get(self.url)
        self.assertRaises(
            NoSuchElementException,
            self.driver.find_element_by_css_selector,
            '#edit-bar',
        )
