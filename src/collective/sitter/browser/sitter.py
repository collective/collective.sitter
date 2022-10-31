from ..content.sitter import ISitter
from ..sitterstate import ISitterState
from collective.sitter import _
from plone import api
from plone.autoform.form import AutoExtensibleForm
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from Products.CMFPlone import PloneMessageFactory
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope import component
from zope import interface
from zope import schema
from zope.interface import Interface, Invalid

import logging


logger = logging.getLogger(__name__)


def is_checked(value):
    if not value:
        raise Invalid(_("Bitte akzeptieren Sie die Nutzungbedingungen"))
    return True


class ISitterContactFormSchema(Interface):
    """Define form fields"""

    name = schema.TextLine(
        title=u"Your name",
    )
    email = schema.TextLine(
        title=u"Your email",
    )
    homepage = schema.TextLine(
        title=u"Your homepage",
        required=False
    )
    accept_terms = schema.Bool(
        title=_(
            u'Accept terms',
        ),
        description=_(u''),
        required=True,
        default=None,
        readonly=False,
        constraint=is_checked
    )
    message = schema.Text(
        title=_(
            u'Message',
        ),
        description=_(
            u'Message',
        ),
        default=None,
        required=False,
        readonly=False,
    )


@component.adapter(interface.Interface)
@interface.implementer(ISitterContactFormSchema)
class SitterContactAdapter(object):
    def __init__(self, context):
        self.name = None
        self.email = None
        self.homepage = None
        self.accept_terms = None
        self.message = None


class SitterContactForm(AutoExtensibleForm, form.Form):
    schema = ISitterContactFormSchema
    form_name = 'sittercontactform'
    view_name = 'sitterview'
    # fields = field.Fields(ISitterContactFormSchema)
    enable_form_tabbing = False
    css_class = 'easyformForm'
    default_fieldset_label = _(u'')
    form_template = ViewPageTemplateFile('templates/sitterview.pt')
    thx_template = ViewPageTemplateFile('templates/thankspage.pt')

    thx_title = _(u'Eine E-Mail an den Babysitter wurde erfolgreich versendet')
    thx_text = _(u'Sie erhalten eine Kopie dieser E-Mail.')
    mail_send_sucsessfully = False


    def update(self):
        if not self.context.getLayout() == self.view_name:
            self.request.response.redirect(self.context.absolute_url())

        # disable Plone's editable border
        # self.request.set('disable_border', True)

        # call the base class version - this is very important!
        super(SitterContactForm, self).update()
        if self.fields['message'].field.default is None or self.fields['message'].field.default != self.getTextvorlage():
            self.fields['message'].field.default = self.getTextvorlage()
            super(SitterContactForm, self).update()
        self.template = self.form_template

        # Goto thankspage if form has been send without errors
        if self.request.method != 'POST':
            return
        data, errors = self.extractData()
        if errors:
            # render errors
            return
        if self.mail_send_sucsessfully:
            self.template = self.thx_template

    @button.buttonAndHandler(_(u'Absenden'), name='submit')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        error_msg = _('Fehler beim Kontaktieren des Babysitters')
        fromname = data['name']
        fromemail = data['email']
        message = data['message']
        toname =self.context.nickname
        toemail = self.context.email
        accept_terms = data['accept_terms']
        if data['homepage'] is None and accept_terms and toemail != '':
            # only spammers will fill homepage field
            mailer = SitterMailer(toname, toemail, fromname, fromemail, message)
            try:
                mailer.send_mail()
                self.mail_send_sucsessfully = True
            except Exception as ex:
                self.status = error_msg
                self.mail_send_sucsessfully = False
        else:
            self.status = error_msg

    # Sitter properties
    @property
    def sitter_state(self):
        return ISitterState(self.context)

    @property
    def sitter(self):
        return ISitter(self.context)

    def __call__(self):
        self.remove_from_portal_messages(
            self.context.translate(PloneMessageFactory('Item state changed.'))
        )
        return super().__call__()

    def get_current_registration_step(self):
        sitter_state = self.sitter_state
        current_user = sitter_state.logged_in_member.id
        creator = self.context.get_creator()
        if current_user == creator:
            current_step = sitter_state.get_current_step()
            return current_step
        else:
            return None

    def remove_from_portal_messages(self, *messages_to_remove):
        status_message = IStatusMessage(self.request)  # noqa: P001
        messages = status_message.show()  # clears messages
        for msg in messages:
            if msg.message not in messages_to_remove:
                status_message.add(msg.message, msg.type)

    def getTextvorlage(self):
        sitter_folder = self.sitter_state.get_sitter_folder()
        return sitter_folder.vorlage or ''

    def get_state(self):
        workflow_tool = api.portal.get_tool('portal_workflow')
        current_review_state = workflow_tool.getInfoFor(self.context, 'review_state')
        return current_review_state

    def get_terms_of_use_link(self):
        sitter_folder = self.sitter_state.get_sitter_folder()
        agreement = sitter_folder.agreement
        if agreement is not None:
            return '/'.join(agreement.to_object.getPhysicalPath())

    def get_local_referer(self):
        if (referer := self.request.getHeader('Referer')) is not None:
            referer_without_params = referer.split('?', 1)[0]
            if self.context.absolute_url().startswith(referer_without_params):
                return referer

    def get_overview_url(self):
        sitter_folder = self.sitter_state.get_sitter_folder()
        return sitter_folder.absolute_url()


class SitterMailer(object):

    mail_template = """\
To: "{to_name}" <{to_mail}>
From: "{from_name}" <{from_mail}>
Subject: {subject}

{text}"""

    def __init__(self, toname: str, toemail: str, fromname: str, fromemail: str, message: str):
        self.toname = toname
        self.fromname = fromname
        self.toemail = toemail
        self.fromemail = fromemail
        self.message = message
        self.fromname_default = api.portal.get_registry_record('sitter.contact_name')
        self.fromemail_default = api.portal.get_registry_record('sitter.contact_from')
        self.contact_subject = api.portal.get_registry_record('sitter.contact_subject')

    def send_mail(self):
        text = api.portal.get_registry_record('sitter.contact_sitter_text')
        mail_text = self.mail_template.format(
            to_mail=self.toemail,
            to_name=self.toname,
            from_mail=self.fromemail,
            from_name=self.fromname,
            subject=self.contact_subject,
            text=text.format(text=self.message),
        )

        copy = api.portal.get_registry_record('sitter.contact_copy_text')
        mail_copy = self.mail_template.format(
            to_mail=self.fromemail,
            to_name=self.fromname,
            from_mail=self.fromemail_default,
            from_name=self.fromname_default,
            subject=self.contact_subject,
            text=copy.format(text=self.message),
        )

        try:
            logger.info(
                f'Send contact mail to sitter {self.sitter_mail} and copy to {self.email}.'
            )
            host = api.portal.get_tool('MailHost')
            host.send(mail_text, immediate=True, charset='utf-8')
            host.send(mail_copy, immediate=True, charset='utf-8')
        except Exception as ex:
            # This should only occur while testing
            logger.error(f'Could not send email: {ex}')
            raise ex


class AddForm(DefaultAddForm):
    """Custom add form that makes sure of some policies that cannot be expressed by
    permissions alone.
    """
    #ToDo: Is this still working?
    def render(self):
        sitterstate = ISitterState(self.context)
        if not sitterstate.has_accepted():
            self.request.response.redirect(self.context.absolute_url() + '/signupview')
        elif sitter := sitterstate.get_sitter():
            self.request.response.redirect(sitter.getURL() + '/edit')
        else:
            return super().render()


class AddView(DefaultAddView):
    form = AddForm
