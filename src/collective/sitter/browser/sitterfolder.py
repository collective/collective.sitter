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
import urllib.request


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

    def find_private_sitters(self):
        days = api.portal.get_registry_record(
            'sitter.days_until_deletion_of_private_sitters', default=100
        )
        modified_before = DateTime() - days
        results = api.content.find(
            portal_type='sitter',
            review_state='private',
            modified={'query': modified_before, 'range': 'max'},
            sort_on='modified',
            sort_order='descending',
        )
        return results

    def find_deleting_sitters(self):
        days = api.portal.get_registry_record(
            'sitter.days_until_deletion_of_deleting_sitters', default=60
        )
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


class CheckCreatorView(BrowserView):
    def __call__(self, deleted_ldap_users_service=None):
        request = self.request
        alsoProvides(request, IDisableCSRFProtection)

        if deleted_ldap_users_service is None:
            self.deleted_ldap_users_service = DeletedLdapUsersService()
        else:
            self.deleted_ldap_users_service = deleted_ldap_users_service

        if 'action' in self.request:
            action = self.request['action']
            if action == 'set_to_private':
                self.set_to_private()

        return super().__call__()

    def set_to_private(self):
        status_action = {
            'deleting': None,
            'pending': 'reject',
            'private': None,
            'published': 'reject',
        }
        for brain in self.find_invalid_sitter_objects():
            current_status = brain.review_state
            action = status_action[current_status]
            logger.error(f'Setting {brain.getId} to private using {action}')
            if action is None:
                continue
            current_object = brain.getObject()
            try:
                api.content.transition(current_object, action)
            except Exception as e:
                logger.error(
                    f'Could not set {current_object.id} to private using {action}: {e}'
                )

        self.deleted_ldap_users_service.remove_all_from_list()

    def find_invalid_sitter_objects(self):
        catalog_results = api.content.find(portal_type='sitter')
        results = [r for r in catalog_results if not self._is_valid_user(r.Creator)]
        return results

    def _is_valid_user(self, user):
        is_valid = user in self._get_local_users()
        if not is_valid:
            is_valid = not self._is_a_deleted_ldap_user(user)
        return is_valid

    def _get_local_users(self):
        return self.context.acl_users.source_users.getUserNames() + ['admin']

    def _is_a_deleted_ldap_user(self, user):
        return user in self.deleted_ldap_users_service.list_of_removed_users


class DeletedLdapUsersService:
    def __init__(self):
        self.list_deleted_users_web_service_url = api.portal.get_registry_record(
            'sitter.list_deleted_users_web_service_url', default=None
        )
        self.remove_deleted_users_web_service_url = api.portal.get_registry_record(
            'sitter.remove_deleted_users_web_service_url', default=None
        )
        self._list_of_removed_users = self._get_list_of_removed_users()

    def _get_list_of_removed_users(self):
        try:
            logger.info(f'web service url {self.list_deleted_users_web_service_url}')
            no_proxy_support = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(no_proxy_support)
            result = opener.open(self.list_deleted_users_web_service_url)
            logger.info('got users to delete')
            deleted_users_list = result.read().split('\n')
        except Exception as e:
            logger.warn(f'Could not get list of deleted ldap users: {e}')
            deleted_users_list = []
        return deleted_users_list

    @property
    def list_of_removed_users(self):
        return self._list_of_removed_users

    def remove_user_from_list_of_deleted_users(self, user):
        url = f'{self.remove_deleted_users_web_service_url}/{user}'
        try:
            no_proxy_support = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(no_proxy_support)
            opener.open(url)
        except Exception as e:
            logger.warn(
                f'Could not remove user {user} from list of deleted ldap users: {e}'
            )

    def remove_all_from_list(self):
        for c in self.list_of_removed_users:
            self.remove_user_from_list_of_deleted_users(c)


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
