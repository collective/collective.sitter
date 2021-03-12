from ..sitterstate import ISitterState
from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from Products.Five.browser import BrowserView
from Products.statusmessages import STATUSMESSAGEKEY
from Products.statusmessages.adapter import _decodeCookieValue
from Products.statusmessages.adapter import IStatusMessage
from zope.annotation.interfaces import IAnnotations

import logging
import re


logger = logging.getLogger(__name__)


class BaseSitterView(BrowserView):
    @property
    def sitter_state(self):
        return ISitterState(self.context)

    def get_object_for_qualification(self, qualification_id):
        sitter_folder = self.sitter_state.get_sitter_folder()
        all_qualifications = sitter_folder.qualificationlist
        qualification = [
            x for x in all_qualifications if x.to_object.UID() == qualification_id
        ]
        if qualification:
            quali = qualification[0]
            return quali.to_object

    def get_object_for_experience(self, experience_id):
        sitter_folder = self.sitter_state.get_sitter_folder()
        all_experiences = sitter_folder.experiences
        experience = [x for x in all_experiences if x.to_object.UID() == experience_id]
        if experience:
            exp = experience[0]
            return exp.to_object

    def get_image_url_for_qualification(self, quali, size):
        if quali.picture:
            scales = quali.restrictedTraverse('@@images')
            return scales.scale('picture', width=size, height=size).url


class SitterView(BaseSitterView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_from_portal_messages(
            ['Artikelstatus geändert.', 'Item state changed.']
        )

    def get_current_registration_step(self):
        sitter_state = self.sitter_state
        current_user = sitter_state.logged_in_member.id
        creator = self.context.get_creator()
        if current_user == creator:
            current_step = sitter_state.get_current_step()
            return current_step
        else:
            return None

    def remove_from_portal_messages(self, messages_to_remove):
        request = self.context.REQUEST
        annotations = IAnnotations(request)
        value = annotations.get(STATUSMESSAGEKEY, request.cookies.get(STATUSMESSAGEKEY))
        if value is None:
            return []

        value = _decodeCookieValue(value)

        if request.response.getStatus() not in (301, 302, 304):
            to_remove = []
            for x in value:
                if x.message in messages_to_remove:
                    to_remove.append(x)

            if not len(to_remove) == 0:
                for to_r in to_remove:
                    value.remove(to_r)
                status_messages = IStatusMessage(request)
                status_messages.show()  # removes all
                # add remaining
                for msg in value:
                    status_messages.add(msg.message, msg.type)

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
        if hasattr(agreement, 'to_object'):
            return '/'.join(agreement.to_object.getPhysicalPath())

    def get_local_referer(self):
        request = self.request
        current_url = self.context.absolute_url()
        referer = request.getHeader('Referer')
        if referer is not None:
            if '?' in referer:
                url_without_params = r'(.*?)\?'
                match_obj = re.search(url_without_params, referer)
                referer_without_params = match_obj.groups()[0]
            else:
                referer_without_params = referer
            came_from_sitterlist = r'^{}'.format(re.escape(referer_without_params))
            if re.search(came_from_sitterlist, current_url):
                return referer
            else:
                return None
        return None

    def get_overview_url(self):
        sitter_folder = self.sitter_state.get_sitter_folder()
        return sitter_folder.absolute_url()


class SitterMailView(BrowserView):

    mail_template = """\
To: "{to_name}" <{to_mail}>
From: "{from_name}" <{from_mail}>
Subject: {subject}

{text}"""

    def __call__(self):
        nickname = self.context.nickname
        sitter_mail = self.context.email

        if not sitter_mail:
            logger.error(
                f'Could not send email because sitter {nickname} has no email address.'
            )
            return (
                'Die E-Mail konnte nicht erfolgreich gesendet werden. '
                'Bitte versuchen Sie es später noch einmal.'
            )

        form = self.request.form

        if 'homepage' in form:
            # homepage is a honeypot field for spammers
            self.request.response.setStatus(202)  # better visibility in logs
            return 'Die E-Mail wurde !erfolgreich versendet'

        sitter_folder = ISitterState(self.context).get_sitter_folder()
        if sitter_folder.agreement and form.get('accepted') != 'True':
            return 'Bitte bestätigen Sie die Nutzungsbedingungen (über dem Textfeld).'

        kontaktname = form.get('kontaktname')
        kontaktemail = form.get('kontaktemail')
        kontakttext = form.get('kontakttext')
        if not all((kontaktname, kontaktemail, kontakttext)):
            return 'Bitte füllen Sie alle Felder aus.'

        subject = api.portal.get_registry_record('sitter.contact_subject')

        text = api.portal.get_registry_record('sitter.contact_sitter_text')
        mail_text = self.mail_template.format(
            to_mail=sitter_mail,
            to_name=nickname,
            from_mail=kontaktemail,
            from_name=kontaktname,
            subject=subject,
            text=text.format(text=kontakttext),
        )

        mail_from = api.portal.get_registry_record('sitter.contact_from')
        mail_from_name = api.portal.get_registry_record('sitter.contact_name')
        copy = api.portal.get_registry_record('sitter.contact_copy_text')
        mail_copy = self.mail_template.format(
            to_mail=kontaktemail,
            to_name=kontaktname,
            from_mail=mail_from,
            from_name=mail_from_name,
            subject=subject,
            text=copy.format(text=kontakttext),
        )

        try:
            logger.info(
                f'Send contact mail to sitter {sitter_mail} and copy to {kontaktemail}.'
            )
            host = api.portal.get_tool('MailHost')
            host.send(mail_text, immediate=True, charset='utf-8')
            host.send(mail_copy, immediate=True, charset='utf-8')
        except Exception as ex:
            # This should only occur while testing
            logger.error(f'Could not send email: {ex}')

        return (
            'Eine E-Mail an den Babysitter wurde erfolgreich versendet. '
            'Sie erhalten eine Kopie dieser E-Mail.'
        )


class AddForm(DefaultAddForm):
    """Custom add form that makes sure of some policies that cannot be expressed by
    permissions alone.
    """

    def render(self):
        sitterstate = ISitterState(self.context)
        sitter = sitterstate.get_sitter()
        if sitter:
            self.request.response.redirect(sitter.getURL() + '/edit')

        elif not sitterstate.has_accepted():
            self.request.response.redirect(self.context.absolute_url() + '/signupview')

        else:
            return super().render()


class AddView(DefaultAddView):
    form = AddForm
