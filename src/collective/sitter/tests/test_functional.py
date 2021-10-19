from ..testing import SITTER_FUNCTIONAL_TESTING
from ..testing import SITTER_SELENIUM_TESTING
from ..testing import TestCase
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

import os
import time
import transaction


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


class BaseSeleniumTestClass(BaseTestClass):
    def setUp(self):
        super().setUp()
        options = webdriver.FirefoxOptions()
        options.headless = not os.environ.get('WEBDRIVER_DEBUG')
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(10)  # seconds

    def selenium_login_test_user(self):
        self.selenium_login(TEST_USER_NAME, TEST_USER_PASSWORD)

    def selenium_login_site_owner(self):
        self.selenium_login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def selenium_login(self, name, password):
        self.url = f'{self.portal_url}/login'
        self.driver.get(self.url)
        self.driver.find_element_by_id('__ac_name').send_keys(name)
        self.driver.find_element_by_id('__ac_password').send_keys(password)
        self.driver.find_element_by_name('buttons.login').click()

    def tearDown(self):
        self.driver.quit()
        super().tearDown()


class TestHoneyPot(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
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


class TestTermsOfUse(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-06'
        self.driver.get(self.url)

    def test_accepted_false(self):
        self.assertNotIn('Sie die Nutzungsbedingungen', self.driver.page_source)
        self.driver.find_element_by_id('kontaktname').send_keys('KK')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('kontakttext').send_keys('hallo')
        self.driver.find_element_by_id('sendcontact').click()
        self.assertIn('Sie die Nutzungsbedingungen', self.driver.page_source)

    def test_accepted_true(self):
        self.driver.find_element_by_id('kontaktname').send_keys('KK')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('accepted').click()
        self.driver.find_element_by_id('kontakttext').send_keys('hallo')
        self.driver.find_element_by_id('sendcontact').click()
        self.assertIn(SEND_SUCCESSFULLY_MSG, self.driver.page_source)


class TestSpecialChars(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-07'
        self.driver.get(self.url)

    def test_specialchars(self):
        self.driver.find_element_by_id('kontaktname').send_keys('hä')
        self.driver.find_element_by_id('kontaktemail').send_keys('mail@example.org')
        self.driver.find_element_by_id('accepted').click()
        self.driver.find_element_by_id('kontakttext').send_keys('hallo täst')
        self.driver.find_element_by_id('sendcontact').click()
        self.assertIn(SEND_SUCCESSFULLY_MSG, self.driver.page_source)


class TestRemovePortalMessage(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
        self.selenium_login_site_owner()
        # submit sitter entry:
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-01'
        self.driver.get(self.url)

    def test(self):
        time.sleep(0.1)
        self.driver.find_element_by_id('plone-contentmenu-workflow').click()
        self.driver.find_element_by_id('workflow-transition-submit').click()
        self.assertNotIn('Item state changed.', self.driver.page_source)
        self.assertNotIn('Artikelstatus geändert.', self.driver.page_source)
        self.assertIn('Kontaktformular', self.driver.page_source)


class TestReferer(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def setUp(self):
        super().setUp()
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


class TestIsEditable(BaseSeleniumTestClass):

    layer = SITTER_SELENIUM_TESTING

    def test_sitter_is_editable_for_owner(self):
        self.selenium_login_site_owner()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-07'
        self.driver.get(self.url)
        edit_bar = self.driver.find_element_by_css_selector('#contentview-edit')
        self.assertIsNotNone(edit_bar)

    def test_sitter_is_not_editable_for_others(self):
        self.selenium_login_test_user()
        self.url = f'{self.portal_url}/{self.sitter_folder_name}/sitter-07'
        self.driver.get(self.url)
        self.assertRaises(
            NoSuchElementException,
            self.driver.find_element_by_css_selector,
            '#contentview-edit',
        )
