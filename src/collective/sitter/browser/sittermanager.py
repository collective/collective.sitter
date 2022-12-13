from ..sitterstate import ISitterState
from plone import api
from Products.Five.browser import BrowserView


class SitterManagerView(BrowserView):
    def __call__(self, *args, **kwargs):
        if api.user.has_permission(
            'collective.sitter: Manage sitters', obj=self.context
        ):
            return super().__call__(*args, **kwargs)
        else:
            # if we change permission of this view in configure.zcml the view will not
            # be themed with diazo anymore
            # b/c diazo rules only match for "body.viewpermission-view"
            response = self.request.response
            response.setStatus(403)

    @property
    def sitter_state(self):
        return ISitterState(self.context)

    @property
    def sitter_folder(self):
        return self.sitter_state.get_sitter_folder()

    @property
    def account_intro_text(self):
        return api.portal.get_registry_record('sitter.sitteraccount_intro_text_manager')

    @property
    def get_faq(self):
        return api.portal.get_registry_record('sitter.sitteraccount_faq_manager')

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
