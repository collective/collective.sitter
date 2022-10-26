from ..testing import SITTER_INTEGRATION_TESTING
from ..testing import TestCase
from ..vocabularies import voc_experience
from ..vocabularies import voc_quali
from plone import api
from unittest.mock import patch
from z3c.relationfield import RelationValue
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.intid import IIntIds
from zope.schema.interfaces import IVocabularyFactory


class BaseTest(TestCase):
    layer = SITTER_INTEGRATION_TESTING

    def set_up(self):
        super().setUp()
        self.login_site_owner()
        self.portal.portal_workflow.setDefaultChain('plone_workflow')

        for name, state in [
            ('sitter-01', 'published'),
            ('sitter-02', 'published'),
            ('sitter-03', 'published'),
            ('sitter-04', 'published'),
            ('sitter-05', 'published'),
            ('sitter-06', 'pending'),
            ('sitter-07', 'private'),
            ('sitter-08', 'deleting'),
        ]:
            sitter = api.content.create(
                container=self.sitter_folder,
                type='sitter',
                id=name,
            )
            api.content.transition(sitter, to_state=state)
        for name, title in [
            ('sitter-exp-01', 'Exp 1'),
            ('sitter-exp-02', 'Exp 2'),
            ('sitter-exp-03', 'Exp 3'),
        ]:
            api.content.create(
                container=self.sitter_folder,
                type='sitterexperience',
                id=name,
                title=title,
            )
        for name, title in [
            ('sitter-quali-01', 'Quali 1'),
            ('sitter-quali-02', 'Quali 2'),
            ('sitter-quali-03', 'Quali 3'),
            ('sitter-quali-04', 'Quali 4'),
        ]:
            api.content.create(
                container=self.sitter_folder,
                type='sitterqualification',
                id=name,
                title=title,
            )

        self.assertIn('sitter-01', self.sitter_folder)
        self.assertIn('sitter-02', self.sitter_folder)

        self.int_ids = getUtility(IIntIds)
        self.sitter_folder.qualifications = (
            RelationValue(self.int_ids.queryId(self.sitter_folder['sitter-quali-01'])),
            RelationValue(self.int_ids.queryId(self.sitter_folder['sitter-quali-02'])),
            RelationValue(self.int_ids.queryId(self.sitter_folder['sitter-quali-03'])),
        )

        self.sitter_folder.experiences = (
            RelationValue(self.int_ids.queryId(self.sitter_folder['sitter-exp-01'])),
            RelationValue(self.int_ids.queryId(self.sitter_folder['sitter-exp-02'])),
            RelationValue(self.int_ids.queryId(self.sitter_folder['sitter-exp-03'])),
        )

        sitter_01 = self.sitter_folder['sitter-01']
        sitter_01.firstname = 'Kristin'
        sitter_01.details = 'Hallo, das ist ein Test'
        sitter_01.fullage = True
        sitter_01.gender = 'female'
        sitter_01.reindexObject()

        sitter_02 = self.sitter_folder['sitter-02']
        sitter_02.fullage = True
        sitter_02.gender = 'male'
        sitter_02.reindexObject()

        voc_q = voc_quali(self.sitter_folder)
        voc_e = voc_experience(self.sitter_folder)
        terms_m = getUtility(IVocabularyFactory, name='collective.taxonomy.mobility')(
            self.sitter_folder
        ).getTerms()

        sitter_03 = self.sitter_folder['sitter-03']
        sitter_03.qualifications = [voc_q._terms[0].value]
        sitter_03.experiences = [voc_e._terms[0].value]
        sitter_03.gender = 'female'
        sitter_03.reindexObject()

        sitter_04 = self.sitter_folder['sitter-04']
        sitter_04.qualifications = [voc_q._terms[0].value, voc_q._terms[2].value]
        sitter_04.experiences = [voc_e._terms[0].value, voc_e._terms[2].value]
        sitter_04.mobility = [terms_m[0].value, terms_m[2].value]
        sitter_04.reindexObject()

        sitter_05 = self.sitter_folder['sitter-05']
        sitter_05.mobility = [terms_m[0].value, terms_m[1].value]
        sitter_05.gender = 'female'
        sitter_05.reindexObject()


class TestIndexer(BaseTest):
    def setUp(self):
        super().set_up()
        self.catalog_under_test = api.portal.get_tool('portal_catalog')

    def test_sittersCreated(self):
        result = self.catalog_under_test({'portal_type': 'sitter'})
        self.assertEqual(8, len(result))

    def test_overageIndex(self):
        result = self.catalog_under_test({'portal_type': 'sitter', 'fullage': 1})
        self.assertEqual(2, len(result))

    def test_experiencesIndex(self):
        uid_1 = self.sitter_folder['sitter-exp-01'].UID()
        uid_2 = self.sitter_folder['sitter-exp-02'].UID()
        uid_3 = self.sitter_folder['sitter-exp-03'].UID()

        result = self.catalog_under_test(
            {
                'experience': [
                    uid_1,
                ]
            }
        )
        self.assertEqual(2, len(result))

        result = self.catalog_under_test(
            {
                'experience': [
                    uid_3,
                ]
            }
        )
        self.assertEqual(1, len(result))

        result = self.catalog_under_test(
            {
                'experience': {
                    'query': [
                        uid_1,
                        uid_3,
                    ],
                    'operator': 'and',
                }
            }
        )
        self.assertEqual(1, len(result))

        result = self.catalog_under_test({'experience': [uid_2]})
        self.assertEqual(0, len(result))

    def test_qualificationIndex(self):
        uid_1 = self.sitter_folder['sitter-quali-01'].UID()
        uid_2 = self.sitter_folder['sitter-quali-02'].UID()
        uid_3 = self.sitter_folder['sitter-quali-03'].UID()

        result = self.catalog_under_test(
            {
                'qualification': [
                    uid_1,
                ]
            }
        )
        self.assertEqual(2, len(result))

        result = self.catalog_under_test(
            {
                'qualification': [
                    uid_3,
                ]
            }
        )
        self.assertEqual(1, len(result))

        result = self.catalog_under_test(
            {
                'qualification': {
                    'query': [
                        uid_1,
                        uid_3,
                    ],
                    'operator': 'and',
                }
            }
        )
        self.assertEqual(1, len(result))

        result = self.catalog_under_test({'qualification': [uid_2]})
        self.assertEqual(0, len(result))

    def test_mobilityIndex(self):
        result = self.catalog_under_test(
            {
                'mobility': [
                    'public_transport',
                ]
            }
        )
        self.assertEqual(2, len(result))
        result = self.catalog_under_test(
            {
                'mobility': [
                    'bicycle',
                ]
            }
        )
        self.assertEqual(1, len(result))
        result = self.catalog_under_test(
            {'mobility': {'query': ['bicycle', 'public_transport'], 'operator': 'and'}}
        )
        self.assertEqual(1, len(result))
        result = self.catalog_under_test(
            {'mobility': {'query': ['bicycle', 'car'], 'operator': 'and'}}
        )
        self.assertEqual(0, len(result))


# TODO Rewrite for faceted search?
class TestSearch:  # (BaseTest):
    def setUp(self):
        super().set_up()
        context = self.sitter_folder
        request = getattr(context, 'REQUEST', None)
        self.view_under_test = getMultiAdapter(
            (context, request), name='searchsitterview'
        )
        self.assertIsNotNone(self.view_under_test)

    def test_searchWithOutFilter_getOnlyPublishedItems(self):
        results = self.view_under_test._find_sitters()
        self.assertEqual(5, len(results))

    def test_searchFilterFullage(self):
        results = self.view_under_test._find_sitters(fullage=True)
        self.assertEqual(2, len(results))
        results = self.view_under_test._find_sitters(fullage=None)
        self.assertEqual(5, len(results))
        results = self.view_under_test._find_sitters(fullage=False)
        self.assertEqual(3, len(results))

    def test_searchFilterMobility(self):
        results = self.view_under_test._find_sitters(mobility=['bicycle'])
        self.assertEqual(1, len(results))
        results = self.view_under_test._find_sitters(
            mobility=['bicycle', 'public_transport']
        )
        self.assertEqual(1, len(results))
        results = self.view_under_test._find_sitters(mobility=['public_transport'])
        self.assertEqual(2, len(results))
        results = self.view_under_test._find_sitters(mobility=['bicycle', 'car'])
        self.assertEqual(0, len(results))
        results = self.view_under_test._find_sitters(mobility='bicycle')
        self.assertEqual(1, len(results))
        results = self.view_under_test._find_sitters(mobility=[])
        self.assertEqual(5, len(results))
        results = self.view_under_test._find_sitters(mobility=None)
        self.assertEqual(5, len(results))
        results = self.view_under_test._find_sitters(mobility=['foo'])
        self.assertEqual(0, len(results))

    def test_searchFilterExperience(self):
        uid_1 = self.sitter_folder['sitter-exp-01'].UID()
        uid_3 = self.sitter_folder['sitter-exp-03'].UID()
        results = self.view_under_test._find_sitters(experiences=[uid_1])
        self.assertEqual(2, len(results))
        results = self.view_under_test._find_sitters(experiences=uid_1)
        self.assertEqual(2, len(results))
        results = self.view_under_test._find_sitters(experiences=[uid_1, uid_3])
        self.assertEqual(1, len(results))
        results = self.view_under_test._find_sitters(experiences=[])
        self.assertEqual(5, len(results))
        results = self.view_under_test._find_sitters(experiences=None)
        self.assertEqual(5, len(results))
        results = self.view_under_test._find_sitters(experiences='foo')
        self.assertEqual(0, len(results))

    def test_searchFilterQualification(self):
        uid_1 = self.sitter_folder['sitter-quali-01'].UID()
        uid_3 = self.sitter_folder['sitter-quali-03'].UID()
        results = self.view_under_test._find_sitters(qualifications=[uid_1])
        self.assertEqual(2, len(results))
        results = self.view_under_test._find_sitters(qualifications=uid_1)
        self.assertEqual(2, len(results))
        results = self.view_under_test._find_sitters(qualifications=[uid_1, uid_3])
        self.assertEqual(1, len(results))
        results = self.view_under_test._find_sitters(qualifications=[])
        self.assertEqual(5, len(results))
        results = self.view_under_test._find_sitters(qualifications=None)
        self.assertEqual(5, len(results))
        results = self.view_under_test._find_sitters(qualifications='foo')
        self.assertEqual(0, len(results))

    def test_searchFilter(self):
        exp_1 = self.sitter_folder['sitter-exp-01'].UID()
        quali_1 = self.sitter_folder['sitter-quali-01'].UID()

        results = self.view_under_test._find_sitters(
            fullage=False, qualifications=quali_1, experiences=exp_1
        )
        self.assertEqual(2, len(results))

        results = self.view_under_test._find_sitters(
            fullage=True, qualifications=quali_1, experiences=exp_1
        )
        self.assertEqual(0, len(results))

    def test_randomOrder_sameSessionSameOrder(self):
        with patch.object(SearchSitterView, '_get_or_create_session', return_value={}):
            results1 = self.view_under_test._find_sitters()
            results2 = self.view_under_test._find_sitters()
        ids1 = [brain.getId for brain in results1]
        ids2 = [brain.getId for brain in results2]
        self.assertEqual(ids1, ids2)

    def test_randomOrder_differentSessionDifferentOrder(self):
        with patch.object(SearchSitterView, '_get_or_create_session', return_value={}):
            results1 = self.view_under_test._find_sitters()
        ids1 = [brain.getId for brain in results1]
        # retry to counter spurious failure if orders turn out equal by chance
        for i in range(3):
            with patch.object(
                SearchSitterView, '_get_or_create_session', return_value={}
            ):
                results2 = self.view_under_test._find_sitters()
            ids2 = [brain.getId for brain in results2]
            try:
                self.assertNotEqual(ids1, ids2)
            except AssertionError as e:
                error = e
            else:
                break
        else:
            raise error

    def test_searchFilterGender_female(self):
        results = self.view_under_test._find_sitters(gender='female')
        self.assertEqual(3, len(results))

    def test_searchFilterGender_male(self):
        results = self.view_under_test._find_sitters(gender='male')
        self.assertEqual(1, len(results))

    def test_searchFilterGender_invalidValue_returnAllGender(self):
        results = self.view_under_test._find_sitters(gender='foo')
        self.assertEqual(5, len(results))

    def test_searchFilterCombined(self):
        uid_1 = self.sitter_folder['sitter-quali-01'].UID()
        result = self.view_under_test._find_sitters(
            qualifications=[
                uid_1,
            ],
            gender='female',
        )
        self.assertEqual(1, len(result))

    def test_searchFilterGender_None_returnAllGender(self):
        results = self.view_under_test._find_sitters(gender=None)
        self.assertEqual(5, len(results))

    def test_searchFilterGender_StringFemale_returnFemale(self):
        results = self.view_under_test._find_sitters(gender='female')
        self.assertEqual(3, len(results))
