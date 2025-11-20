from .. import _
from datetime import date
from eea.facetednavigation.interfaces import IDisableSmartFacets
from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.interfaces import IHidePloneRightColumn
from eea.facetednavigation.layout.events import faceted_enabled
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from persistent.list import PersistentList
from plone import api
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from Products.GenericSetup.context import SnapshotImportContext
from Products.GenericSetup.interfaces import IBody
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.lifecycleevent import IObjectAddedEvent

import logging
import os


logger = logging.getLogger(__name__)
logger.setLevel(level='INFO')


REMOVE_INACTIVE_KEY = 'REMOVE_INACTIVE'


class ISitterFolder(model.Schema, IFacetedNavigable):
    """
    Folder which is holding all babysitters
    """

    title = schema.TextLine(
        title=_('sitter_folder_name'),
    )

    agreement = RelationChoice(
        title=_('possible_agreement'),
        vocabulary='collective.sitter.Catalog',
        required=False,
    )
    directives.widget(
        'agreement',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['Document'],
        ),
    )

    info_text = RelationChoice(
        title=_('info_text'),
        vocabulary='collective.sitter.Catalog',
        required=False,
    )
    directives.widget(
        'info_text',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['Document'],
        ),
    )

    info_text_logged_in_user = RelationChoice(
        title=_('info_text_logged_in_user'),
        vocabulary='collective.sitter.Catalog',
        required=False,
    )
    directives.widget(
        'info_text_logged_in_user',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['Document'],
        ),
    )

    qualifications = RelationList(
        title=_('qualifications'),
        value_type=RelationChoice(
            title=_('possible_qualifications'),
            vocabulary='collective.sitter.Catalog',
        ),
        required=False,
        default=[],
        missing_value=[],
    )
    directives.widget(
        'qualifications',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['sitterqualification'],
        ),
    )

    experiences = RelationList(
        title=_('experiences', 'Erfahrung'),
        value_type=RelationChoice(
            title=_('possible_experiences'),
            vocabulary='collective.sitter.Catalog',
        ),
        required=False,
        default=[],
        missing_value=[],
    )
    directives.widget(
        'experiences',
        RelatedItemsFieldWidget,
        pattern_options=dict(
            selectableTypes=['sitterexperience'],
        ),
    )

    vorlage = schema.Text(
        title=_('Kontaktformular Vorlage'),
        description=_('Geben Sie hier eine Vorlage fuer das Kontaktformular an.'),
        required=True,
    )


@implementer(ISitterFolder)
class SitterFolder(Container):
    exclude_from_nav = False

    def find_inactive_sitters(self, login_after):
        for sitter in api.content.find(
            portal_type='sitter',
            path='/'.join(self.getPhysicalPath()),
        ):
            user = api.user.get(sitter.Creator)
            if user is None:
                # We cannot, in general, be sure whether the user doesn't exist
                # oder whether there was just an error in some PAS plugin.
                # Better to skip this user than to delete user data by accident.
                continue
            if user.getProperty('last_login_time').asdatetime().date() < login_after:
                yield sitter, user

    def send_renewal_reminder(self, login_after, action):
        fromname = api.portal.get_registry_record('sitter.contact_name')
        fromemail = api.portal.get_registry_record('sitter.contact_from')
        subject = api.portal.get_registry_record('sitter.renewal_reminder_subject')
        text = api.portal.get_registry_record('sitter.renewal_reminder_text')
        followup = action.endswith('_followup')
        today = date.today()
        portal_url = api.portal.get().absolute_url()

        for sitter, user in self.find_inactive_sitters(login_after):
            if sitter.review_state != 'published':
                # Don't bother creators of private or deleting sitter ads,
                # those will be handled by another clean-up process.
                continue

            sitter_ann = IAnnotations(sitter.getObject())
            last = sitter_ann.get(REMOVE_INACTIVE_KEY, ())
            if followup:
                if not (last and last[-1][1:] == (login_after, 'initial_reminder')):
                    # All reminders must have been sent before deletion, so we skip the
                    # followup if the initial one wasn't sent in the first place.
                    continue
            elif last and last[-1][1] == login_after:
                continue

            logger.info(f'Send renewal reminder to {sitter.Creator}.')
            toname = user.getProperty('fullname')
            toemail = user.getProperty('email')
            api.portal.send_email(
                sender=f'"{fromname}" <{fromemail}>',
                recipient=f'"{toname}" <{toemail}>',
                subject=subject,
                body=text.format(toname=toname, portal_url=portal_url),
                immediate=True,
            )
            if not last:
                last = sitter_ann[REMOVE_INACTIVE_KEY] = PersistentList()
            last.append(
                (
                    today,
                    login_after,
                    ('followup_reminder' if followup else 'initial_reminder'),
                )
            )

    def delete_inactive_sitters(self, login_after):
        # Delete a sitter advertisement object. In order to do further clean-up such as
        # removing user data, subscribe to the IObjectRemovedEvent.
        for sitter_brain, user in self.find_inactive_sitters(login_after):
            sitter = sitter_brain.getObject()
            sitter_ann = IAnnotations(sitter)
            last = sitter_ann.get(REMOVE_INACTIVE_KEY, ())
            if not (
                len(last) >= 2
                and last[-2][1:] == (login_after, 'initial_reminder')
                and last[-1][1:] == (login_after, 'followup_reminder')
            ):
                # All reminders must have been sent before deletion. Followup shouldn't
                # have been sent without initial, but let's be extra safe.
                continue
            logger.info(f'Delete inactive sitter {sitter_brain.getId}.')
            api.content.delete(sitter)

    def eval_renewal_action(self, run_for_date=None):
        schedule = api.portal.get_registry_record('sitter.renewal_schedule')
        today = date.today()
        year = today.year
        if run_for_date:
            today = date.fromisoformat(f'{year}-{run_for_date}')

        for line in schedule.splitlines():
            if not (line := line.strip()):
                continue
            login_after, reminder1, reminder2, deletion = [
                date.fromisoformat(f'{year}-{item.strip()}') for item in line.split(',')
            ]
            # TODO: sanity checks?
            if login_after <= today <= deletion:
                action = (
                    'send_renewal_reminder_initial'
                    if today == reminder1
                    else (
                        'send_renewal_reminder_followup'
                        if today == reminder2
                        else 'delete_inactive_sitters' if today == deletion else None
                    )
                )
                return action, login_after

        return None, None

    def run_renewal(self, run_for_date=None):
        action, login_after = self.eval_renewal_action(run_for_date)
        if action and action.startswith('send_renewal_reminder'):
            self.send_renewal_reminder(login_after, action)
        if action == 'delete_inactive_sitters':
            self.delete_inactive_sitters(login_after)


@adapter(ISitterFolder, IObjectAddedEvent)
def configure_facetednavigation(sitterfolder, event=None):
    config_file_name = 'facetednavigation.xml'
    layout_id = 'faceted-sitter'

    alsoProvides(sitterfolder, IDisableSmartFacets)
    alsoProvides(sitterfolder, IHidePloneRightColumn)
    faceted_enabled(sitterfolder, None)

    logger.info(
        f'Loading configuration {config_file_name} for faceted view '
        f'on {"/".join(sitterfolder.getPhysicalPath())}'
    )
    import_file_path = os.path.join(os.path.dirname(__file__), config_file_name)
    with open(import_file_path) as import_file:
        xml = import_file.read()

        # XXX quick fix to limit search, there should be a less hacky way to do this
        xml = xml.replace('SITTERFOLDER', f'/{sitterfolder.getId()}')

        environ = SnapshotImportContext(sitterfolder, 'utf-8')
        importer = queryMultiAdapter((sitterfolder, environ), IBody)
        importer.body = xml
    IFacetedLayout(sitterfolder).update_layout(layout_id)
