from ..content.sitter import ISitter
from ..sitterstate import ISitterState
from collective.sitter import _
from plone import api
from plone.autoform.form import AutoExtensibleForm
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.edit import DefaultEditView
from Products.CMFPlone import PloneMessageFactory
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import form
from zope import component
from zope import interface
from zope import schema
from zope.interface import Interface
from zope.interface import Invalid

import logging


logger = logging.getLogger(__name__)


def are_terms_accepted(value):
    if not value:
        raise Invalid(_('please accept terms'))
    return True


class ISitterContactFormSchema(Interface):
    """Define form fields"""

    homepage = schema.TextLine(
        title='homepage',
        required=False,
    )
    accept_terms = schema.Bool(
        title=_('accept_terms_title'),
        description=_('accept_terms_description'),
        required=True,
        default=None,
        readonly=False,
        constraint=are_terms_accepted,
    )
    message = schema.Text(
        title=_('message_title'),
        description=_('message_description'),
        default=None,
        required=False,
        readonly=False,
    )


@component.adapter(interface.Interface)
@interface.implementer(ISitterContactFormSchema)
class SitterContactAdapter:
    def __init__(self, context):
        self.homepage = None
        self.accept_terms = None
        self.message = None


class SitterContactForm(AutoExtensibleForm, form.Form):
    schema = ISitterContactFormSchema
    form_name = 'sittercontactform'
    view_name = 'sitterview'
    enable_form_tabbing = False
    css_class = 'easyformForm'
    form_template = ViewPageTemplateFile('templates/sitterview.pt')
    thx_template = ViewPageTemplateFile('templates/thankspage.pt')
    thx_title = _('email sent successfully')
    thx_text = _('You will receive a copy of this email')
    mail_sent_successfully = False

    def update(self):
        if self.context.getLayout() != self.view_name:
            self.request.response.redirect(self.context.absolute_url())

        # disable Plone's editable border
        # self.request.set('disable_border', True)

        # call the base class version - this is very important!
        super().update()
        if self.fields['message'].field.default != self.getTextvorlage():
            self.fields['message'].field.default = self.getTextvorlage()
            super().update()
        self.template = self.form_template

        # Goto thankspage if form has been send without errors
        if self.request.method != 'POST':
            return
        data, errors = self.extractData()
        if errors:
            # render errors
            return
        if self.mail_sent_successfully:
            self.template = self.thx_template

    @button.buttonAndHandler(_('Submit'), name='submit')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        user = api.user.get_current()
        fromname = user.getProperty('fullname')
        fromemail = user.getProperty('email')
        message = data['message']
        toname = self.context.nickname
        toemail = self.context.email
        accept_terms = data['accept_terms']
        if data['homepage'] is None and accept_terms and toemail != '':
            # only spammers will fill homepage field
            mailer = SitterMailer(toname, toemail, fromname, fromemail, message)
            try:
                mailer.send_mail()
            except Exception:
                pass
            else:
                self.mail_sent_successfully = True
                return
        self.status = _('error while sending mail to sitter')

    # Sitter properties
    @property
    def sitter_state(self):
        return ISitterState(self.context)

    @property
    def sitter(self):
        return ISitter(self.context)

    @property
    def logged_in(self):
        return not api.user.is_anonymous()

    @property
    def login_url(self):
        portal = api.portal.get().absolute_url()
        here = self.context.absolute_url()
        return f'{portal}/login?came_from={here}'

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


class SitterMailer:
    def __init__(
        self, toname: str, toemail: str, fromname: str, fromemail: str, message: str
    ):
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
        copy = api.portal.get_registry_record('sitter.contact_copy_text')

        try:
            # Send mail to sitter
            api.portal.send_email(
                sender=f'{self.fromname} <{self.fromemail}>',
                recipient=f'{self.toname} <{self.toemail}>',
                subject=self.contact_subject,
                body=text.format(text=self.message),
                immediate=True,
            )
            # Send copy of mail
            api.portal.send_email(
                sender=f'{self.fromname_default} <{self.fromemail_default}>',
                recipient=f'{self.fromname} <{self.fromemail}>',
                subject=self.contact_subject,
                body=copy.format(text=self.message),
                immediate=True,
            )
        except Exception as ex:
            # This should only occur while testing
            logger.error('Could not send email')
            raise ex


class AccountURLMixin:
    @property
    def account_url(self):
        sitterstate = ISitterState(self.context)
        sitter_folder = sitterstate.get_sitter_folder()
        return f'{sitter_folder.absolute_url()}/account'


class AddForm(DefaultAddForm):
    """Custom add form that makes sure of some policies that cannot be expressed by
    permissions alone.
    """

    def render(self):
        sitterstate = ISitterState(self.context)
        if not sitterstate.has_accepted():
            self.request.response.redirect(self.context.absolute_url() + '/signupview')
        elif sitterstate.get_sitter():
            sitter_folder = sitterstate.get_sitter_folder()
            self.request.response.redirect(sitter_folder.absolute_url() + '/account')
        else:
            return super().render()


class AddView(DefaultAddView):
    form = AddForm


class EditForm(DefaultEditForm, AccountURLMixin):
    def nextURL(self):
        return self.account_url


class EditView(DefaultEditView):
    form = EditForm


class TransitionView(AccountURLMixin):
    def __call__(self):
        workflow_action = self.request.form['workflow_action']
        try:
            api.content.transition(self.context, workflow_action)
        except api.exc.InvalidParameterError:
            pass
        self.request.response.redirect(self.account_url)
