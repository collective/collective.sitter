from ..testing import SITTER_INTEGRATION_TESTING
from ..testing import TestCase
from ..vocabularies import voc_district
from plone import api
from plone.app.textfield.value import RichTextValue
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


class TestSitterContentType(TestCase):

    layer = SITTER_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.login_site_owner()

        for name in ('sitter-01', 'sitter-02'):
            api.content.create(
                container=self.sitter_folder,
                type='sitter',
                id=name,
            )
        self.sitter_object = self.sitter_folder['sitter-02']

    def test_sitter_exist(self):
        self.assertIn('sitter-01', self.sitter_folder)

    def test_sitter_email(self):
        user = api.user.get_current()
        user.setMemberProperties(dict(email='test@example.org; test2@example.net'))
        self.assertEqual('test@example.org', self.sitter_object.email)

    def test_sitter_getDistrict(self):
        self.sitter_object.district = (
            voc_district(self.sitter_folder).getTerm('north').token,
        )
        district = self.sitter_object.get_district()
        self.assertEqual('Northern district', district)

    def test_sitter_getDistrict_notSet(self):
        district = self.sitter_object.get_district()
        self.assertIsNone(district)

    def test_sitter_getLanguages(self):
        self.sitter_object.language = ['en', 'ru']
        langs = self.sitter_object.get_language_list()
        self.assertEqual(['English', 'Russian'], langs)

    def test_sitter_getLanguages_notSet(self):
        self.assertTrue(len(self.sitter_object.get_language_list()) == 0)

    def test_sitter_image_notSet(self):
        image = self.sitter_object.image
        self.assertIsNone(image)

    def test_sitter_getGender(self):
        voc_gender = getUtility(IVocabularyFactory, name='collective.taxonomy.gender')
        self.sitter_object.gender = (
            voc_gender(self.sitter_folder).getTerm('female').value
        )

        gender = self.sitter_object.get_gender()
        self.assertEqual('female', gender)

    def test_sitter_getGender_notSet(self):
        gender = self.sitter_object.get_gender()
        self.assertIsNone(gender)

    def test_sitter_getDetails_notSet(self):
        details = self.sitter_object.details
        self.assertIsNone(details)

    def test_sitter_getMobility(self):
        voc_mobility = getUtility(
            IVocabularyFactory, name='collective.taxonomy.mobility'
        )
        self.sitter_object.mobility = (
            voc_mobility(self.sitter_folder).getTerm('public_transport').value,
        )
        mobility = self.sitter_object.get_mobility()
        self.assertIn('public transport', mobility)

    def test_sitter_getMobility_notSet(self):
        mobility = self.sitter_object.get_mobility()
        self.assertTrue(len(mobility) == 0)

class TestSitterAbbreviatedDetailsDetails(TestCase):

    layer = SITTER_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.login_site_owner()

    def test_sitter_details(self):
        api.content.create(
                container=self.sitter_folder,
                type='sitter',
                id='test-sitter-1',
            )
        sitter_object = self.sitter_folder['test-sitter-1']
        sitter_object.details = RichTextValue('<p>asdf asdf asdf asdf asdf</p><p>VG</p>')
        abr_details = sitter_object.abbreviated_details(24)
        self.assertEqual(abr_details, '<p>asdf asdf asdf asdf asdf</p><p>…</p>')

    def test_no_whitespace(self):
        api.content.create(
                container=self.sitter_folder,
                type='sitter',
                id='test-sitter-1',
            )
        sitter_object = self.sitter_folder['test-sitter-1']
        sitter_object.details = RichTextValue('<p>aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</p><p>bbbbbbbbbbbbbbbbbbbbb</p>')
        abr_details = abbreviated_details = sitter_object.abbreviated_details(20)
        self.assertEqual(abr_details,'<p>aaaaaaaaaaaaaaaaaaaa…</p>')

    def test_short_details(self):
        api.content.create(
                container=self.sitter_folder,
                type='sitter',
                id='test-sitter-1',
            )
        sitter_object = self.sitter_folder['test-sitter-1']
        sitter_object.details = RichTextValue('<p>aaaaaaaaa</p>')
        abr_details = sitter_object.abbreviated_details(50)
        self.assertEqual(abr_details, '<p>aaaaaaaaa</p>')
