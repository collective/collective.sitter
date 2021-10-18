from . import MessageFactory as _
from plone import api
from plone.memoize.view import memoize
from zope.interface import implementer
from zope.interface import Interface
from zope.location.location import LocationIterator

import logging


logger = logging.getLogger(__name__)


class ISitterState(Interface):
    """An adapter that gives access to the current state of the registration process
    of the currently logged in sitter"""

    def is_logged_in():
        """Is a user logged in?"""

    def has_accepted():
        """Has Sitter accepted AGB?"""

    def is_created():
        """Is the sitter object created?"""

    def is_submitted():
        """Is the sitter object submitted to reviewer?"""

    def is_published():
        """Is the sitter object published?"""

    def get_sitter_folder():
        """Return the nearest ISitterFolder up the hierarchy or None."""


@implementer(ISitterState)
class SitterState:
    def __init__(self, context):
        self.context = context
        self.logged_in_member = api.user.get_current()

    @memoize
    def is_logged_in(self):
        return not api.user.is_anonymous()

    @memoize
    def has_accepted(self):
        if not self.is_logged_in():
            return False

        return self.logged_in_member.getProperty('accepted_sitter_agreement')

    @memoize
    def is_created(self):
        sitter_folder = self.get_sitter_folder()
        if not sitter_folder:
            return False

        results = api.content.find(
            portal_type='sitter',
            path='/'.join(sitter_folder.getPhysicalPath()),
            Creator=str(self.logged_in_member),
        )
        return bool(results)

    @memoize
    def is_deleted(self):
        sitter_folder = self.get_sitter_folder()
        is_deleted = False
        if sitter_folder is not None:
            member = self.logged_in_member
            results = api.content.find(
                portal_type='sitter',
                path='/'.join(sitter_folder.getPhysicalPath()),
                Creator=str(member),
                review_state='deleting',
            )
            if results:
                is_deleted = True
        return is_deleted

    @memoize
    def get_sitter_folder(self):
        from .content.sitterfolder import ISitterFolder

        for obj in LocationIterator(self.context):
            if ISitterFolder.providedBy(obj):
                return obj

    def is_submitted(self):
        return self._get_workflow_state() == 'pending'

    def is_published(self):
        return self._get_workflow_state() == 'published'

    @memoize
    def _get_workflow_state(self):
        sitter = self.get_sitter()
        if sitter:
            return sitter.review_state

    @memoize
    def get_sitter(self):
        member = self.logged_in_member
        query = {
            'portal_type': 'sitter',
            'Creator': str(member),
        }

        sitter_folder = self.get_sitter_folder()
        if sitter_folder:
            query['path'] = '/'.join(sitter_folder.getPhysicalPath())

        results = api.content.find(**query)
        if results:
            return results[0]

    @memoize
    def get_registration_steps(self):
        steps = []
        sitter_folder_path = self.get_sitter_folder().absolute_url()
        link = sitter_folder_path + '/login'
        step1 = RegistrationStep(
            _('Anmelden'),
            description=_(
                'Bitte melden Sie sich mit Ihrem Staff oder Students-Account an.'
            ),
            is_finished=self.is_logged_in(),
            is_current=(not self.is_logged_in()),
            link=link,
        )
        steps.append(step1)

        link = self.get_sitter_folder().absolute_url() + '/++add++sitter/'

        step2 = RegistrationStep(
            _('Nutzungsbedingungen akzeptieren'),
            description=_('Bitte akzeptieren Sie die Nutzungsbedingungen.'),
            is_finished=self.has_accepted(),
            is_current=(
                self.is_logged_in()
                and not self.has_accepted()
                and not self.is_deleted()
            ),
            link=link,
        )
        steps.append(step2)

        this_sitter = self.get_sitter()
        if this_sitter is not None:
            this_sitter = this_sitter.getObject()
            link = (
                this_sitter.absolute_url()
                + '/content_status_modify?workflow_action=submit'
            )

        edit_link = ''
        delete_link = ''
        recycle_link = ''
        if this_sitter is not None:
            edit_link = this_sitter.absolute_url() + '/edit'
            delete_link = (
                this_sitter.absolute_url()
                + '/content_status_modify?workflow_action=delete'
            )
            recycle_link = (
                this_sitter.absolute_url()
                + '/content_status_modify?workflow_action=recycle'
            )

        if not self.is_deleted():
            step3 = RegistrationStep(
                _('Daten eingeben'),
                description=_('Bitte geben Sie einige Daten zu sich an.'),
                is_finished=self.is_created(),
                is_current=(
                    self.is_logged_in()
                    and self.has_accepted()
                    and not self.is_created()
                    and not self.is_deleted()
                ),
                link=link,
            )
            steps.append(step3)

            step4 = RegistrationStep(
                _('Einreichen'),
                description=_(
                    'Sie können Ihren Eintrag jetzt <a href="${link}">einreichen</a>, '
                    'damit er von der Redaktion freigegeben werden kann. '
                    'Auch können Sie Ihren Eintrag weiter '
                    '<a href="${edit_link}">bearbeiten</a> oder '
                    '<a href="${delete_link}">löschen</a>.',
                    mapping=dict(
                        link=link, edit_link=edit_link, delete_link=delete_link
                    ),
                ),
                is_finished=self.is_submitted() or self.is_published(),
                is_current=(
                    self.is_logged_in()
                    and self.has_accepted()
                    and self.is_created()
                    and not self.is_submitted()
                    and not self.is_published()
                    and not self.is_deleted()
                ),
                link=link,
            )
            steps.append(step4)

            step5 = RegistrationStep(
                _('Warten auf Freigabe'),
                description=_(
                    'Ihr Eintrag wird von der Redaktion geprüft und freigegeben. '
                    'Sie können Ihre Daten weiterhin '
                    '<a href="${edit_link}">bearbeiten</a> oder '
                    '<a href="${delete_link}">löschen</a>.',
                    mapping=dict(edit_link=edit_link, delete_link=delete_link),
                ),
                is_finished=self.is_published(),
                is_current=(
                    self.is_logged_in()
                    and self.has_accepted()
                    and self.is_created()
                    and self.is_submitted()
                    and not self.is_published()
                    and not self.is_deleted()
                ),
                link='',
            )
            steps.append(step5)

            step6 = RegistrationStep(
                _('Eintrag veröffentlicht'),
                description=_(
                    'Ihr Eintrag ist veröffentlicht. '
                    'Sie können Ihren Eintrag auch '
                    '<a href="${edit_link}">bearbeiten</a> oder '
                    '<a href="${delete_link}">löschen</a>.',
                    mapping=dict(edit_link=edit_link, delete_link=delete_link),
                ),
                is_finished=self.is_published(),
                is_current=(
                    self.is_logged_in()
                    and self.has_accepted()
                    and self.is_created()
                    and not self.is_submitted()
                    and self.is_published()
                    and not self.is_deleted()
                ),
                finished_class_name='fa fa-flag-checkered fa-lg finished',
                link='',
            )
            steps.append(step6)
        else:
            days = api.portal.get_registry_record(
                'sitter.days_until_deletion_of_deleting_sitters', default=60
            )
            step7 = RegistrationStep(
                _('Eintrag gelöscht'),
                description=_(
                    'Ihr Eintrag ist zum Löschen markiert '
                    'und wird innerhalb der nächsten ${days} Tage gelöscht. '
                    'Bis dahin haben Sie die Möglichkeit ihn '
                    '<a href="${recycle_link}">wiederherzustellen. </a>',
                    mapping=dict(days=days, recycle_link=recycle_link),
                ),
                is_finished=self.is_deleted(),
                is_current=(self.is_created() and self.is_deleted()),
                finished_class_name='fa fa-trash-o fa-lg finished',
            )
            steps.append(step7)

        return steps

    @memoize
    def get_current_step(self):
        steps = self.get_registration_steps()
        return next(x for x in steps if x.is_current is True)


class RegistrationStep:
    def __init__(
        self,
        text,
        description='',
        is_finished=False,
        is_current=False,
        link='',
        finished_class_name='fa fa-check fa-lg done',
        more_links=None,
    ):
        self.text = text
        self.description = description
        self.is_finished = is_finished
        self.is_current = is_current
        self.link = link
        self.finished_class_name = finished_class_name
        if more_links is None or not (
            type(more_links) is list or type(more_links) is tuple
        ):
            self.more_links = []
        else:
            self.more_links = more_links

    def get_icon_classes(self):
        if self.is_finished:
            return self.finished_class_name
        elif self.is_current:
            return 'fa fa-arrow-left fa-lg activestep-img'
        else:
            return ''

    def get_css_classes(self):
        if not self.is_finished and not self.is_current:
            return 'steptodo portletItem'
        else:
            return 'step portletItem'

    def has_more_links(self):
        return len(self.more_links) > 0


class Link:
    def __init__(self, text, link, class_name):
        self.text = text
        self.link = link
        self.class_name = class_name
