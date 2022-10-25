from .. import MessageFactory as _
from ..sitterstate import ISitterState
from .sitter import SitterView
from plone import api
from Products.Five.browser import BrowserView
from plone.protect.authenticator import createToken

import logging


logger = logging.getLogger(__name__)


class SitterAccountView(BrowserView):

    @property
    def is_manager(self):
        return api.user.has_permission(
            'collective.sitter: Manage sitters', obj=self.context
        )

    @property
    def sitter_state(self):
        return ISitterState(self.context)

    @property
    def sitter_folder(self):
        return self.sitter_state.get_sitter_folder()

    @property
    def sitter(self) -> SitterView:
        return self.sitter_state.get_sitter().getObject()

    @property
    def account_intro_text(self):
        if (self.is_manager):
            return api.portal.get_registry_record('sitter.sitteraccount_intro_text_manager')
        else:
            return api.portal.get_registry_record('sitter.sitteraccount_intro_text_sitter')

    @property
    def get_fqa(self):
        if (self.is_manager):
            return api.portal.get_registry_record('sitter.sitteraccount_faq_manager')
        else:
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
        return f'{sitter.getURL()}/content_status_modify?workflow_action=delete&{auth}'

    def submit_entry_url(self) -> str:
        sitter = self.sitter_state.get_sitter()
        auth_token = createToken()
        auth = f'_authenticator={auth_token}'
        return f'{sitter.getURL()}/content_status_modify?workflow_action=submit&{auth}'

    def recycle_entry_url(self) -> str:
        sitter = self.sitter_state.get_sitter()
        auth_token = createToken()
        auth = f'_authenticator={auth_token}'
        return f'{sitter.getURL()}/content_status_modify?workflow_action=recycle&{auth}'

    @property
    def info_text_url(self):
        try:
            info_text_obj = self.sitter_folder.info_text
            return self._get_link_for(info_text_obj)
        except AttributeError:
            return None

    @property
    def info_text_logged_in_url(self):
        try:
            info_text_logged_in_obj = self.sitter_folder.info_text_logged_in
            return self._get_link_for(info_text_logged_in_obj)
        except AttributeError:
            return None

    @property
    def agreement_url(self):
        try:
            agreement_obj = self.sitter_folder.agreement
            return self._get_link_for(agreement_obj)
        except AttributeError:
            return None

    def _get_link_for(self, relation_obj):
        if relation_obj:
            path = relation_obj.to_path
            if path:
                return f'{path}/edit'
