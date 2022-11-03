from .. import _
from plone.dexterity.content import Item
from plone.namedfile.field import NamedImage
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


class ISitterQualification(model.Schema):
    """
    Description of the Example Type
    """

    title = schema.TextLine(
        title=_('Name'),
        required=True,
    )
    beschreibung = schema.TextLine(
        title=_('Beschreibung'),
        required=True,
    )
    picture = NamedImage(
        title=_('Bildbeschreibung'),
        required=False,
    )


@implementer(ISitterQualification)
class SitterQualification(Item):
    exclude_from_nav = False
