from ..content.sitter import Sitter
from ..sitterstate import ISitterState
from plone import api
from plone.protect.authenticator import createToken
from Products.Five.browser import BrowserView

import logging


logger = logging.getLogger(__name__)


class SitterAccountView(BrowserView):
    @property
    def sitter_state(self):
        return ISitterState(self.context)

    @property
    def sitter_folder(self):
        return self.sitter_state.get_sitter_folder()

    @property
    def sitter(self) -> Sitter:
        return self.sitter_state.get_sitter().getObject()

    @property
    def sittercontentmacro(self) -> BrowserView:
        sitterview = self.sitter.restrictedTraverse('sitterview')
        return sitterview.form_template.macros['sittercontent']

    @property
    def account_intro_text(self):
        return api.portal.get_registry_record('sitter.sitteraccount_intro_text_sitter')

    @property
    def get_faq(self):
        return api.portal.get_registry_record('sitter.sitteraccount_faq_sitter')

    def get_current_registration_step(self):
        return self.sitter_state.get_current_step()

    def add_entry_url(self) -> str:
        return self.context.absolute_url() + '/++add++sitter/'

    def edit_entry_url(self) -> str:
        sitter = self.sitter_state.get_sitter()
        auth_token = createToken()
        auth = f'_authenticator={auth_token}'
        return f'{sitter.getURL()}/edit?{auth}'

    def delete_entry_url(self) -> str:
        sitter = self.sitter_state.get_sitter()
        auth_token = createToken()
        auth = f'_authenticator={auth_token}'
        return f'{sitter.getURL()}/transition?workflow_action=delete&{auth}'

    def submit_entry_url(self) -> str:
        sitter = self.sitter_state.get_sitter()
        auth_token = createToken()
        auth = f'_authenticator={auth_token}'
        return f'{sitter.getURL()}/transition?workflow_action=submit&{auth}'

    def recycle_entry_url(self) -> str:
        sitter = self.sitter_state.get_sitter()
        auth_token = createToken()
        auth = f'_authenticator={auth_token}'
        return f'{sitter.getURL()}/transition?workflow_action=recycle&{auth}'
