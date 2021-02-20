from ..browser.controlpanel import ISitterSettings
from ..testing import SITTER_INTEGRATION_TESTING
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getUtility

import unittest


class TestDefaultValuesInRegistry(unittest.TestCase):

    layer = SITTER_INTEGRATION_TESTING

    def setUp(self):
        self.registry = getUtility(IRegistry)
        self.portal = self.layer['portal']

    def get_config_values(self):
        return self.registry.forInterface(ISitterSettings, prefix='sitter')

    def do_test_values(self, config_values, expected_values):
        for prop in expected_values:
            value = getattr(config_values, prop, None)
            self.assertEqual(expected_values[prop], value)

    def test_default_values(self):

        config_values = self.get_config_values()
        expected_default_values = {
            'days_until_deletion_of_private_sitters': 90,
            'days_until_deletion_of_deleting_sitters': 30,
            'sitters_per_page': 20,
        }
        self.do_test_values(config_values, expected_default_values)

    def test_modified_values(self):
        config_values = self.get_config_values()
        setattr(config_values, 'reviewer_email', 'reviewer@example.org')
        # import transaction
        # transaction.commit()
        # reinstall
        setup_tool = self.portal.portal_setup
        setup_tool.runAllImportStepsFromProfile('profile-collective.sitter:default')
        config_values = self.get_config_values()
        expected_values = {
            'reviewer_email': 'reviewer@example.org',
            'days_until_deletion_of_private_sitters': 90,
            'days_until_deletion_of_deleting_sitters': 30,
            'sitters_per_page': 20,
        }
        self.do_test_values(config_values, expected_values)
