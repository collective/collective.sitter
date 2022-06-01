from eea.facetednavigation.interfaces import IDisableSmartFacets
from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.interfaces import IHidePloneRightColumn
from eea.facetednavigation.layout.events import faceted_enabled
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from Products.GenericSetup.context import SnapshotImportContext
from Products.GenericSetup.interfaces import IBody
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides

import logging
import os


log = logging.getLogger(__name__)


def post_install(context=None):
    return


def configure_facetednavigation(sitterfolder):
    config_file_name = 'sitter.xml'
    layout_id = 'faceted-sitter'

    alsoProvides(sitterfolder, IFacetedNavigable)
    alsoProvides(sitterfolder, IDisableSmartFacets)
    alsoProvides(sitterfolder, IHidePloneRightColumn)
    faceted_enabled(sitterfolder, None)

    log.info(
        'Loading configuration {0} for faceted view on {1}'.format(
            config_file_name, '/'.join(sitterfolder.getPhysicalPath())
        )
    )
    import_file_path = os.path.join(
        os.path.dirname(__file__),
        'profiles/default/facetednavigation/',
        config_file_name,
    )
    with open(import_file_path) as import_file:
        xml = import_file.read()
        environ = SnapshotImportContext(sitterfolder, 'utf-8')
        importer = queryMultiAdapter((sitterfolder, environ), IBody)
        importer.body = xml
    IFacetedLayout(sitterfolder).update_layout(layout_id)
