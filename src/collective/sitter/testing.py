from plone import api
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import MOCK_MAILHOST_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser
from plone.testing.zope import WSGI_SERVER_FIXTURE
from Products.Sessions.tests.testSessionDataManager import _populate
from z3c.relationfield import RelationValue
from zope.component import getUtility
from zope.intid import IIntIds

import collective.sitter
import collective.taxonomy
import unittest


class SitterLayer(PloneSandboxLayer):

    defaultBases = (
        PLONE_APP_CONTENTTYPES_FIXTURE,
        MOCK_MAILHOST_FIXTURE,
    )

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=collective.sitter)

    def setUpPloneSite(self, portal):
        _populate(portal.__parent__)

        applyProfile(portal, 'collective.sitter:default')
        portal.acl_users.userFolderAddUser(
            SITE_OWNER_NAME, SITE_OWNER_PASSWORD, ['Manager'], []
        )
        api.user.get(username=SITE_OWNER_NAME).setMemberProperties(
            {'email': 'sitter-06@example.org'}
        )
        setRoles(portal, TEST_USER_ID, ['Member'])

        login(portal, SITE_OWNER_NAME)
        sitter_folder = api.content.create(
            container=portal,
            type='sitterfolder',
            id='sitter_folder',
        )
        api.content.transition(sitter_folder, transition='publish')

        int_ids = getUtility(IIntIds)
        terms_of_use = api.content.create(
            container=portal, type='Document', id='terms_of_use'
        )
        api.content.transition(terms_of_use, transition='publish')
        sitter_folder.agreement = RelationValue(int_ids.queryId(terms_of_use))


SITTER_FIXTURE = SitterLayer()
SITTER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(SITTER_FIXTURE,), name='Sitter:Integration'
)
SITTER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(SITTER_FIXTURE,), name='Sitter:Functional'
)
SITTER_SELENIUM_TESTING = FunctionalTesting(
    bases=(SITTER_FIXTURE, WSGI_SERVER_FIXTURE), name='Sitter:Selenium'
)


class TestCase(unittest.TestCase):
    def setUp(self):
        self.portal = self.layer['portal']
        self.sitter_folder_name = 'sitter_folder'
        self.sitter_folder = self.portal[self.sitter_folder_name]
        self.browser = self.make_browser()

    def make_browser(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        return browser

    def login(self, username, password=None):
        self.logout()
        login(self.portal, username)
        if password:
            self.browser.addHeader('Authorization', f'Basic {username}:{password}')

    def login_site_owner(self):
        self.login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def login_test_user(self):
        self.login(TEST_USER_NAME, TEST_USER_PASSWORD)

    def logout(self):
        logout()
        self.browser = self.make_browser()
