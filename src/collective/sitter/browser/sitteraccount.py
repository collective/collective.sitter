from .. import MessageFactory as _
from ..sitterstate import ISitterState
from plone import api
from Products.Five.browser import BrowserView

import logging


logger = logging.getLogger(__name__)


class SitterAccountView(BrowserView):

    @property
    def is_manager(self):
        return False
        return api.user.has_permission(
            'collective.sitter: Manage sitters', obj=self.context
        )

    @property
    def sitter_state(self):
        return ISitterState(self.context)

    @property
    def account_intro_text(self):
        # @TODO: into registry and controlpanel
        return "Here, you can finish your registration process and submit your entry"

    def registration_steps(self):
        return self.sitter_state.get_registration_steps()

    def get_current_registration_step(self):
        return self.sitter_state.get_current_step()
