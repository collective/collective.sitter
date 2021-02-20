from .. import MessageFactory as _
from ..sitterstate import ISitterState
from plone import api
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.formlib import form
from zope.interface import implementer

import logging


logger = logging.getLogger(__name__)


class ISitterPortlet(IPortletDataProvider):
    """Sitter registration portlet."""


@implementer(ISitterPortlet)
class Assignment(base.Assignment):
    title = _('sitter_portlet_title')


class Renderer(base.Renderer):
    @property
    def available(self):
        return not api.user.is_anonymous()

    render_manager = ViewPageTemplateFile('sitterportlet_manager.pt')
    render_other = ViewPageTemplateFile('sitterportlet.pt')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sitter_state = ISitterState(self.context)

        sitter_folder = self.sitter_state.get_sitter_folder()
        self.sitter_folder_path = sitter_folder.absolute_url()

        info_text_obj = sitter_folder.info_text
        self.goto_info_text = self._get_link_for(info_text_obj)

        info_text_logged_in_obj = sitter_folder.info_text_logged_in_user
        self.goto_logged_in_info_text = self._get_link_for(info_text_logged_in_obj)

        agreement_obj = sitter_folder.agreement
        self.goto_agreement = self._get_link_for(agreement_obj)

        is_manager = api.user.has_permission(
            'collective.sitter: Manage sitters', obj=self.context
        )
        self.render = self.render_manager if is_manager else self.render_other

    def _get_link_for(self, relation_obj):
        if relation_obj:
            path = relation_obj.to_path
            if path:
                return f'{path}/edit'

    def registration_steps(self):
        return self.sitter_state.get_registration_steps()


class AddForm(base.NullAddForm):
    schema = ISitterPortlet
    form_fields = form.Fields(ISitterPortlet)
    label = _('sitter_portlet_add_label')
    description = _('sitter_portlet_add_desc')

    def create(self):
        return Assignment()


class EditForm(base.EditForm):
    schema = ISitterPortlet
    form_fields = form.Fields(ISitterPortlet)
    label = _('sitter_portlet_edit_label')
    description = _('sitter_portlet_edit_desc')
