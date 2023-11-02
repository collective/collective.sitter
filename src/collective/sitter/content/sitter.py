from .. import _
from .. import vocabularies
from ..sitterstate import ISitterState
from bs4 import BeautifulSoup
from plone import api
from plone.app.textfield import RichText as RichTextField
from plone.app.z3cform.widget import RichTextFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Item
from plone.indexer.decorator import indexer
from plone.namedfile.field import NamedBlobImage
from plone.namedfile.interfaces import IImageScaleTraversable
from plone.supermodel import model
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.checkbox import SingleCheckBoxFieldWidget
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.select import SelectFieldWidget
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory

import logging


logger = logging.getLogger(__name__)

TINY_MCE_LIGHT_OPTIONS = {
    'tiny': {
        'menubar': False,
        'toolbar': 'undo redo | bold italic' ' | bullist numlist',
        'plugins': [
            'lists',
            'paste',
        ],
    }
}


class ISitter(model.Schema, IImageScaleTraversable):
    """
    Sitter Information
    """

    nickname = schema.TextLine(
        title=_('Nickname'),
        required=True,
    )

    directives.widget(
        'details',
        RichTextFieldWidget,
        pattern_options=TINY_MCE_LIGHT_OPTIONS,
    )
    details = RichTextField(
        title=_('Detailed Information'),
        description=_('Beschreiben Sie sich hier mit ein paar kurzen Worten.'),
        required=False,
        allowed_mime_types=['text/html'],
    )

    image = NamedBlobImage(
        title=_('Image'),
        description=_(
            'Wählen Sie ein Foto von Ihrer Festplatte, um es in der Übersicht '
            'anzuzeigen. Sie bestätigen uns, dass Sie das alleinige Urheberrecht, das '
            'Recht bzw. die Erlaubnis auf Veröffentlichung des im Rahmen der '
            'Babysitteranzeige hochgeladenen Fotos besitzen sowie die Zustimmung '
            'eventuell weiterer Personen auf dem Foto vorliegen haben.'
        ),
        required=False,
    )

    directives.widget('district', SelectFieldWidget)
    district = schema.List(
        title=_('District'),
        value_type=schema.Choice(source=vocabularies.voc_district),
        description=_('desc_district'),
        required=True,
    )

    directives.widget(gender=RadioFieldWidget)
    gender = schema.Choice(
        title=_('Gender'),
        vocabulary='collective.taxonomy.gender',
        description=_('desc_gender'),
        required=False,
    )

    directives.widget(experiences=CheckBoxFieldWidget)
    experiences = schema.List(
        title=_('Experiences'),
        value_type=schema.Choice(source=vocabularies.voc_experience),
        description=_(
            'Waehlen Sie aus, mit welchen Altersklassen sie schon Erfahrungen haben.'
        ),
        required=False,
    )

    directives.widget(mobility=CheckBoxFieldWidget)
    mobility = schema.List(
        title=_('Mobility'),
        value_type=schema.Choice(vocabulary='collective.taxonomy.mobility'),
        description=_('Waehlen Sie aus, wie mobil Sie sind.'),
        required=False,
    )

    fullage = schema.Bool(
        title=_('Full age'),
        description=_('desc_fullage'),
        required=True,
    )
    # Display the field as optional since a value will be set in any case and marking
    # the field as required wrongly suggests having to check it as true.
    directives.widget(
        'fullage',
        SingleCheckBoxFieldWidget,
        required=False,
    )

    directives.widget(language=CheckBoxFieldWidget)
    language = schema.List(
        title=_('Languages'),
        value_type=schema.Choice(vocabulary='collective.taxonomy.language'),
        description=_('Select languages that you speak.'),
        required=False,
    )

    directives.widget(qualifications=CheckBoxFieldWidget)
    qualifications = schema.List(
        title=_('Qualifications'),
        value_type=schema.Choice(source=vocabularies.voc_quali),
        description=_('Geben Sie hier die Qualifikationen an, die Sie mitbringen.'),
        required=False,
    )


@indexer(ISitter)
def experiencesIndexer(context):
    return [str(e).replace(' ', '_') for e in context.experiences or []]


@indexer(ISitter)
def qualificationsIndexer(context):
    return [str(e).replace(' ', '_') for e in context.qualifications or []]


class InvalidEmailError(schema.ValidationError):
    __doc__ = 'Please enter a valid e-mail address.'


@implementer(ISitter)
class Sitter(Item):
    def get_creator(self):
        creators = self.listCreators()
        creator = creators[0]
        return creator

    @property
    def email(self):
        creator = api.user.get(username=self.get_creator())
        try:
            mails = creator.getProperty('email')
            if type(mails) is tuple:
                mail = mails[0]
            else:
                mail = mails.split(';')[0].strip()
        except AttributeError:
            mail = None

        return mail

    @property
    def title(self):
        return getattr(self, 'nickname', '')

    def setTitle(self, value):
        return

    def has_image(self):
        return bool(getattr(self, 'image', None))

    def get_language_list(self):
        lang_list = [
            self.get_value_from_vocabulary(x, 'collective.taxonomy.language')
            for x in self.language or []
        ]
        return lang_list

    def get_district(self):
        if self.district:
            district = self.district[0]
            if not district == '--NOVALUE--':
                taxonomy_name = api.portal.get_registry_record(
                    'sitter.district_taxonomy'
                )
                return self.get_value_from_vocabulary(district, taxonomy_name)

    def get_gender(self):
        if self.gender:
            return self.get_value_from_vocabulary(
                self.gender, 'collective.taxonomy.gender'
            )

    def get_mobility(self):
        return [
            self.get_value_from_vocabulary(m, 'collective.taxonomy.mobility')
            for m in self.mobility or []
        ]

    def get_value_from_vocabulary(self, value, vocabulary):
        factory = getUtility(IVocabularyFactory, name=vocabulary)
        vocabulary = factory(self)
        term = vocabulary.getTerm(value)
        return translate(term.title, context=getRequest())

    def get_qualifications(self):
        # don't use vocabulary for efficiency
        sitter_folder = ISitterState(self).get_sitter_folder()
        objects = [x.to_object for x in sitter_folder.qualifications]
        return [obj for obj in objects if obj.UID() in set(self.qualifications)]

    def get_experiences(self):
        # don't use vocabulary for efficiency
        sitter_folder = ISitterState(self).get_sitter_folder()
        objects = [x.to_object for x in sitter_folder.experiences]
        return [obj for obj in objects if obj.UID() in set(self.experiences)]

    def get_details(self):
        return self.details and self.details.output

    def abbreviated_details(self, length):
        details = self.get_details()
        if not details:
            return ''

        soup = BeautifulSoup(details, features='lxml')

        def soup_iter():
            remaining = length
            for s in soup.stripped_strings:
                if remaining <= 0:
                    yield '…'
                    break
                if len(s) > remaining:
                    yield s[:remaining].rsplit(None, 1)[0] + '…'
                    break
                else:
                    yield s
                    remaining -= len(s)

        return ''.join(f'<p>{s}</p>' for s in soup_iter())


def on_created(obj, event):
    base_url = _get_base_url(include_site=True)
    edit_url = f'{base_url}/{event.newParent.id}/{event.newName}'
    send_mail_to_sitter_on_creation(context=obj, edit_url=edit_url)
    send_mail_to_reviewer_on_creation(context=obj, edit_url=edit_url)


def on_modify(obj, event):
    base_url = _get_base_url(include_site=False)
    edit_url = base_url + '/'.join(event.object.getPhysicalPath())
    current_state = api.content.get_state(obj)
    if current_state == 'published':
        send_mail_to_reviewer_on_modify(context=obj, edit_url=edit_url)


def on_change_state(obj, event):
    base_url = _get_base_url(include_site=False)
    edit_url = base_url + '/'.join(event.object.getPhysicalPath())
    state = api.content.get_state(obj)
    if state == 'pending':
        send_mail_to_reviewer_on_submitting(context=obj, edit_url=edit_url)
    if state == 'published':
        send_mail_to_sitter_on_publishing(context=obj, edit_url=edit_url)
    if state == 'deleting':
        creator = obj.get_creator()
        user = api.user.get(username=creator)
        user.setMemberProperties(mapping={'accepted_sitter_agreement': False})


def _get_base_url(include_site=True):
    portal = api.portal.get()
    base = portal if include_site else portal.aq_parent
    return base.absolute_url()


def send_mail_to_sitter_on_publishing(context, edit_url):
    subject = api.portal.get_registry_record('sitter.sitter_msg_publish_subject')
    text = api.portal.get_registry_record('sitter.sitter_msg_publish_text')
    _send_mail_to_sitter(context, subject, text, edit_url)


def send_mail_to_sitter_on_creation(context, edit_url):
    subject = api.portal.get_registry_record('sitter.sitter_msg_create_subject')
    text = api.portal.get_registry_record('sitter.sitter_msg_create_text')
    _send_mail_to_sitter(context, subject, text, edit_url)


def _send_mail_to_sitter(context, subject, text, edit_url):
    if subject is None or text is None:
        return

    mail_from = api.portal.get_registry_record('sitter.review_from')
    mail_to = context.email

    if '{url}' in text:
        text = text.format(url=edit_url)

    _send_mail(context, mail_from, mail_to, subject, text)


def send_mail_to_reviewer_on_creation(context, edit_url):
    subject = api.portal.get_registry_record('sitter.reviewer_msg_create_subject')
    text = api.portal.get_registry_record('sitter.reviewer_msg_create_text')
    _send_mail_to_reviewer(context, subject, text, edit_url)


def send_mail_to_reviewer_on_submitting(context, edit_url):
    subject = api.portal.get_registry_record('sitter.reviewer_msg_submit_subject')
    text = api.portal.get_registry_record('sitter.reviewer_msg_submit_text')
    _send_mail_to_reviewer(context, subject, text, edit_url)


def send_mail_to_reviewer_on_modify(context, edit_url):
    subject = api.portal.get_registry_record('sitter.reviewer_msg_modify_subject')
    text = api.portal.get_registry_record('sitter.reviewer_msg_modify_text')
    _send_mail_to_reviewer(context, subject, text, edit_url)


def _send_mail_to_reviewer(context, subject, text, edit_url):
    mail_from = api.portal.get_registry_record('sitter.review_from')
    mail_to = api.portal.get_registry_record('sitter.reviewer_email')

    text = f'{text}\n\n{edit_url}'

    _send_mail(context, mail_from, mail_to, subject, text)


def _send_mail(context, mail_from, mail_to, subject, text):
    annotations = IAnnotations(getRequest())
    if annotations.get('DONT_SEND_MAIL'):
        return

    mail_text = """\
To: {mail_to}
From: {mail_from}
Subject: {subject}

{text}""".format(
        mail_from=mail_from,
        mail_to=mail_to,
        subject=subject,
        text=text,
    )

    if not mail_to:
        logger.error('No recipient to send email to')
        return

    try:
        mail_host = api.portal.get_tool('MailHost')
        mail_host.send(mail_text, charset='utf-8')  # immediate?
    except Exception:
        logger.error('Could not send email')
