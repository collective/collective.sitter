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

import logging


logger = logging.getLogger(__name__)


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


@provider(IContextSourceBinder)
def voc_experience(context):
    terms = []
    sitter_folder = ISitterState(context).get_sitter_folder()

    if sitter_folder is not None and sitter_folder.experiences is not None:
        for x in sitter_folder.experiences:
            exp_obj = x.to_object
            terms.append(SimpleTerm(value=exp_obj.UID(), title=exp_obj.title))

    return SimpleVocabulary(terms)


@provider(IContextSourceBinder)
def voc_quali(context):
    terms = []
    sitter_folder = ISitterState(context).get_sitter_folder()

    if sitter_folder is not None and sitter_folder.qualificationlist is not None:
        for x in sitter_folder.qualificationlist:
            quali_obj = x.to_object
            terms.append(SimpleTerm(value=quali_obj.UID(), title=quali_obj.title))
    return SimpleVocabulary(terms)
