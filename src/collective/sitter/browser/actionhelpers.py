from ..sitterstate import ISitterState
from plone import api
from Products.Five.browser import BrowserView


class ActionHelpers(BrowserView):
    def get_sitter(self):
        sitter_state = ISitterState(self.context)
        return sitter_state.get_sitter()

    def current_user_has_sitter_entry(self):
        return self.get_sitter() is not None

    def sitter_path(self):
        sitter = self.get_sitter()
        if sitter is not None:
            return sitter.getObject().absolute_url()

    def accepted_sitter_agreement(self):
        sitter_state = ISitterState(self.context)
        return sitter_state.has_accepted()

    def reject_sitter_agreement(self):
        user = api.user.get_current()
        user.setMemberProperties(mapping={'accepted_sitter_agreement': False})
        self.request.response.redirect(self.sitter_path())
