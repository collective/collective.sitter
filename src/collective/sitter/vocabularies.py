from .sitterstate import ISitterState
from plone import api
from plone.app.vocabularies.catalog import CatalogVocabulary
from plone.app.vocabularies.utils import parseQueryString
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import provider
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class CatalogVocabularyFactory:
    """Create a catalog vocabulary that includes objects outside the current path.

    Basically copied parts to keep from plone.app.vocabularies.catalog. Should be
    reconsidered upon Plone upgrades as according to a comment in the original's source,
    using CatalogSource is becoming the preferred way.

    """

    def __call__(self, context, query=None):
        parsed = {}
        if query:
            parsed = parseQueryString(context, query['criteria'])
            if 'sort_on' in query:
                parsed['sort_on'] = query['sort_on']
            if 'sort_order' in query:
                parsed['sort_order'] = str(query['sort_order'])

        return CatalogVocabulary.fromItems(parsed, context)


@provider(IContextSourceBinder)
def voc_district(context):
    taxonomy_name = api.portal.get_registry_record('sitter.district_taxonomy')
    taxonomy = getUtility(IVocabularyFactory, name=taxonomy_name)
    return taxonomy(context)


@implementer(IVocabularyFactory)
@implementer(IContextSourceBinder)
class ContentVocabularyFactory:
    items_name = None

    def __call__(self, context):
        terms = []
        sitter_folder = ISitterState(context).get_sitter_folder()
        if sitter_folder is not None:
            items = getattr(sitter_folder, self.items_name)
            for x in items or ():
                obj = x.to_object
                terms.append(SimpleTerm(value=obj.UID(), title=obj.title))

        return SimpleVocabulary(terms)


class ExperienceVocabularyFactory(ContentVocabularyFactory):
    items_name = 'experiences'


voc_experience = ExperienceVocabularyFactory()


class QualificationVocabularyFactory(ContentVocabularyFactory):
    items_name = 'qualifications'


voc_quali = QualificationVocabularyFactory()
