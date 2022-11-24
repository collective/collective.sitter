from ..content.sitterfolder import ISitterFolder
from ..sitterstate import ISitterState
from plone import api
from Products.CMFPlone.interfaces import IRedirectAfterLogin
from zope.interface import implementer


@implementer(IRedirectAfterLogin)
def redirect(context, request):
    sitterstate = ISitterState(context)
    sitter_folder = sitterstate.get_sitter_folder()
    if sitter_folder is None:
        for sitter_folder in api.portal.get().objectValues():
            if ISitterFolder.providedBy(sitter_folder):
                break
        else:
            return

    def adapter(*args):
        is_manager = api.user.has_permission(
            'collective.sitter: Manage sitters', obj=sitter_folder
        )
        target = (
            f'{sitter_folder.absolute_url()}/sittermanager'
            if is_manager
            else f'{sitter_folder.absolute_url()}/account'
        )
        return target

    return adapter
