from .. import _
from plone.dexterity.content import Item
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


class ISitterExperience(model.Schema):
    """
    Babysitter Informations
    """

    title = schema.TextLine(
        title=_('Name'),
        required=True,
    )
    beschreibung = schema.TextLine(
        title=_('Beschreibung'),
        required=True,
    )


@implementer(ISitterExperience)
class SitterExperience(Item):
    exclude_from_nav = False
