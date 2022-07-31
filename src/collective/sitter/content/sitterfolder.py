from .. import MessageFactory as _
from eea.facetednavigation.interfaces import IDisableSmartFacets
from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.interfaces import IHidePloneRightColumn
from eea.facetednavigation.layout.events import faceted_enabled
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from Products.GenericSetup.context import SnapshotImportContext
from Products.GenericSetup.interfaces import IBody
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.lifecycleevent import IObjectAddedEvent

import logging
import os


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

    qualifications = RelationList(
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
        'qualifications',
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


@implementer(ISitterFolder)
class SitterFolder(Container):
    pass


@adapter(ISitterFolder, IObjectAddedEvent)
def configure_facetednavigation(sitterfolder, event=None):
    config_file_name = 'facetednavigation.xml'
    layout_id = 'faceted-sitter'

    alsoProvides(sitterfolder, IFacetedNavigable)
    alsoProvides(sitterfolder, IDisableSmartFacets)
    alsoProvides(sitterfolder, IHidePloneRightColumn)
    faceted_enabled(sitterfolder, None)

    logger.info(
        f'Loading configuration {config_file_name} for faceted view '
        f'on {"/".join(sitterfolder.getPhysicalPath())}'
    )
    import_file_path = os.path.join(os.path.dirname(__file__), config_file_name)
    with open(import_file_path) as import_file:
        xml = import_file.read()

        # XXX quick fix to limit search, there should be a less hacky way to do this
        xml = xml.replace('SITTERFOLDER', f'/{sitterfolder.getId()}')

        environ = SnapshotImportContext(sitterfolder, 'utf-8')
        importer = queryMultiAdapter((sitterfolder, environ), IBody)
        importer.body = xml
    IFacetedLayout(sitterfolder).update_layout(layout_id)
