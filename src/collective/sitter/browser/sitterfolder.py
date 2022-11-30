from .. import _
from ..sitterstate import ISitterState
from DateTime import DateTime
from eea.facetednavigation.browser.app.query import FacetedQueryHandler
from pathlib import Path
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFPlone.browser.navigation import PhysicalNavigationBreadcrumbs
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.interface import alsoProvides

import eea.facetednavigation.browser
import logging


logger = logging.getLogger(__name__)


class SignupView(BrowserView):
    def __call__(self):
        if 'stay' in self.request:
            # this is a flag for development
            return super().__call__()

        if api.user.is_anonymous():
            logger.debug('Anonymous User')
            self.context.plone_utils.addPortalMessage(
                _('Please login before registering as babysitter'), 'info'
            )
            self.request.response.redirect(self.context.absolute_url() + '/login?')

        elif ISitterState(self.context).has_accepted():
            self.request.response.redirect(self.context.absolute_url())

        elif (
            'form.button.Accept' in self.request
            and not self.request['ACTUAL_URL'] == self.context.absolute_url()
        ):
            self.acceptAgreement()
            self.request.response.redirect(
                self.context.absolute_url() + '/++add++sitter/'
            )

        else:
            return super().__call__()

    def acceptAgreement(self):
        member = api.user.get_current()
        member.setMemberProperties(mapping={'accepted_sitter_agreement': True})


class DeleteSitterView(BrowserView):
    """You can call it via wget like this:
    wget http://localhost:8081/Plone/sitters/deletesitter?action=delete \
    --http-user=cron --http-password=cron --auth-no-challenge
    """

    def __call__(self):
        request = self.request
        alsoProvides(request, IDisableCSRFProtection)

        if 'action' in self.request:
            action = self.request['action']
            if action == 'delete_private' or action == 'delete':
                self.delete_private_sitters()
            if action == 'delete_deleting' or action == 'delete':
                self.delete_deleting_sitters()

        return super().__call__()

    # ToDo: add memoize

    def days_private(self):
        return api.portal.get_registry_record(
            'sitter.days_until_deletion_of_private_sitters', default=100
        )

    def find_private_sitters(self):
        days = self.days_private()
        modified_before = DateTime() - days
        results = api.content.find(
            portal_type='sitter',
            review_state='private',
            modified={'query': modified_before, 'range': 'max'},
            sort_on='modified',
            sort_order='descending',
        )
        return results

    def days_deleting(self):
        return api.portal.get_registry_record(
            'sitter.days_until_deletion_of_deleting_sitters', default=60
        )

    def find_deleting_sitters(self):
        days = self.days_deleting()
        modified_before = DateTime() - days
        results = api.content.find(
            portal_type='sitter',
            review_state='deleting',
            modified={'query': modified_before, 'range': 'max'},
            sort_on='modified',
            sort_order='descending',
        )
        return results

    def delete_private_sitters(self):
        ids_to_delete = [o.id for o in self.find_private_sitters()]
        self._delete(ids_to_delete)

    def delete_deleting_sitters(self):
        ids_to_delete = [o.id for o in self.find_deleting_sitters()]
        self._delete(ids_to_delete)

    def _delete(self, ids_to_delete):
        plone_utils = api.portal.get_tool('plone_utils')
        try:
            folder = self.context
            ids = ids_to_delete[:]
            folder.manage_delObjects(ids_to_delete)
            message = f'Deleted {len(ids)} sitters with ids ({", ".join(ids)})'
            logger.info(message)
            plone_utils.addPortalMessage(message)
        except Exception as e:
            logger.warn(
                f'Could not delete {len(ids)} sitters with ids {", ".join(ids)}: {e}'
            )


def _listify(value):
    if value is None:
        value = []
    if type(value) not in (list, tuple):
        value = [value]
    return value


class SitterFolderFacetedQueryHandler(FacetedQueryHandler):

    index = ViewPageTemplateFile(
        Path(eea.facetednavigation.browser.__file__).parent / 'template/query.pt'
    )

    def __call__(self, *args, **kwargs):
        sdm = api.portal.get_tool('session_data_manager')
        session = sdm.getSessionData(create=True)
        session.set('faceted_query', self.request.get('QUERY_STRING'))
        return super().__call__(*args, **kwargs)


class SitterFolderBreadcrumbs(PhysicalNavigationBreadcrumbs):
    def breadcrumbs(self):
        sdm = api.portal.get_tool('session_data_manager')
        session = sdm.getSessionData()
        breadcrumbs = super().breadcrumbs()
        if session and (query := session.get('faceted_query')):
            breadcrumbs[-1]['absolute_url'] += '#' + query
        return breadcrumbs
