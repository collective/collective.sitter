from .. import MessageFactory as _
from plone import api
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.interface import implementer

import logging


logger = logging.getLogger(__name__)


class ISitterFolder(model.Schema):
    """
    Folder which is holding all babysitters
    """

    title = schema.TextLine(
        title=_('sitter_folder_name'),
    )

    agreement = RelationChoice(
        title=_('possible_agreement'),
        vocabulary='collective.sitter.Catalog',
        required=False,
    )
    directives.widget(
        'agreement',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['Document'],
        ),
    )

    info_text = RelationChoice(
        title=_('info_text'),
        vocabulary='collective.sitter.Catalog',
        required=False,
    )
    directives.widget(
        'info_text',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['Document'],
        ),
    )

    info_text_logged_in_user = RelationChoice(
        title=_('info_text_logged_in_user'),
        vocabulary='collective.sitter.Catalog',
        required=False,
    )
    directives.widget(
        'info_text_logged_in_user',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['Document'],
        ),
    )

    qualificationlist = RelationList(
        title=_('qualifications'),
        value_type=RelationChoice(
            title=_('possible_qualifications'),
            vocabulary='collective.sitter.Catalog',
        ),
        required=False,
        default=[],
        missing_value=[],
    )
    directives.widget(
        'qualificationlist',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['sitterqualification'],
        ),
    )

    experiences = RelationList(
        title=_('experiences', 'Erfahrung'),
        value_type=RelationChoice(
            title=_('possible_experiences'),
            vocabulary='collective.sitter.Catalog',
        ),
        required=False,
        default=[],
        missing_value=[],
    )
    directives.widget(
        'experiences',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['sitterexperience'],
        ),
    )

    vorlage = schema.Text(
        title=_('Kontaktformular Vorlage'),
        description=_('Geben Sie hier eine Vorlage fuer das Kontaktformular an.'),
        required=True,
    )

    def find_sitters(**query_params):
        pass


@implementer(ISitterFolder)
class SitterFolder(Container):
    def find_sitters(self, **query_params):
        query = dict(
            portal_type='sitter',
            path={'query': '/'.join(self.getPhysicalPath())},
        )
        query.update(query_params)
        results = api.content.find(**query)
        return results
