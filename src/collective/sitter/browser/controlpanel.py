from .. import _
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform.directives import widget
from plone.supermodel import model
from plone.z3cform import layout
from zope import schema
from zope.interface import Interface


default_sitter_msg_create_text = """\
Vielen Dank für Ihre Registrierung bei der Babysitterbörse.

Falls nicht bereits geschehen, reichen Sie bitte Ihren Babysitter-Eintrag nach
der Erstellung zur Redaktion ein. Er wird dann geprüft und freigegeben.

{url}

--
Mit freundlichen Grüßen
"""

default_sitter_msg_publish_text = """\
Ihr Babysitter-Eintrag bei der Betreuungsbörse wurde freigegeben und ist unter
folgendem Link sichtbar:

{url}

--
Mit freundlichen Grüßen
"""

default_contact_sitter_text = """\
{text}
"""

default_contact_copy_text = """\
Diese Nachricht wurde an den Babysitter gesendet. Bei Interesse wird er/sie
sich mit Ihnen in Verbindung setzen.

{text}
"""


class ISitterFaqConfig(Interface):
    question = schema.TextLine(title='Frage')
    answer = schema.Text(title='Antwort')


class ISitterSettings(Interface):

    days_until_deletion_of_private_sitters = schema.Int(
        title='Tage bis private Sitter-Objekte gelöscht werden',
        default=90,
    )
    days_until_deletion_of_deleting_sitters = schema.Int(
        title='Tage bis zum löschen markierte Sitter-Objekte gelöscht werden.',
        default=30,
    )
    sitters_per_page = schema.Int(
        title='Babysitter Anzahl pro Seite',
        description='Anzahl der Babysitter, die auf der Übersichtsseite aufeinmal '
        'angezeigt werden sollen.',
        default=20,
    )
    list_deleted_users_web_service_url = schema.TextLine(
        title='Url des Webservices, der gelöschte Benutzer-Accounts auflistet.',
    )
    remove_deleted_users_web_service_url = schema.TextLine(
        title=(
            'Url des Webservices, mit dem Benutzer aus der Liste '
            'der gelöschten Benutzer-Accounts entfernt werden können.'
        ),
    )
    district_taxonomy = schema.Choice(
        title='Taxonomie für die Ortsteile',
        vocabulary='collective.taxonomy.taxonomies',
        default='collective.taxonomy.district',
    )

    model.fieldset(
        'review',
        label='Redaktionsprozess für Sitter',
        fields=[
            'review_from',
            'reviewer_email',
            'reviewer_msg_create_subject',
            'reviewer_msg_create_text',
            'reviewer_msg_submit_subject',
            'reviewer_msg_submit_text',
            'reviewer_msg_modify_subject',
            'reviewer_msg_modify_text',
            'sitter_msg_create_subject',
            'sitter_msg_create_text',
            'sitter_msg_publish_subject',
            'sitter_msg_publish_text',
        ],
    )

    review_from = schema.TextLine(
        title='Absenderadresse der Redaktion',
        description='Absender-E-Mail-Adresse für Review-Nachrichten',
    )
    reviewer_email = schema.TextLine(
        title='Empfängeradresse der Redaktion',
        description='E-Mail-Adresse der Reviewer',
    )
    reviewer_msg_create_subject = schema.TextLine(
        title='Mail an Redaktion bei Erstellung: Betreff',
        description='Betreff der Mail an Redaktion, wenn ein Sitter erstellt wurde.',
        default='Babysitter-Eintrag erstellt',
    )
    reviewer_msg_create_text = schema.Text(
        title='Mail an Redaktion bei Erstellung: Text',
        description='Text der Mail an Redaktion, wenn ein Sitter erstellt wurde.',
        default='Ein neuer Babysitter-Eintrag wurde erstellt.',
    )
    reviewer_msg_submit_subject = schema.TextLine(
        title='Mail an Redaktion bei Einreichung: Betreff',
        description='Betreff der Mail an Redaktion, wenn ein Sitter eingereicht wurde.',
        default='Babysitter-Eintrag eingereicht',
    )
    reviewer_msg_submit_text = schema.Text(
        title='Mail an Redaktion bei Einreichung: Text',
        description='Text der Mail an Redaktion, wenn ein Sitter eingereicht wurde.',
        default='Ein neuer Babysitter-Eintrag wurde eingereicht.',
    )
    reviewer_msg_modify_subject = schema.TextLine(
        title='Mail an Redaktion bei Änderung: Betreff',
        description='Betreff der Mail an Redaktion, wenn ein Sitter geändert wurde.',
        default='Babysitter-Eintrag geändert',
    )
    reviewer_msg_modify_text = schema.Text(
        title='Mail an Redaktion bei Änderung: Text',
        description='Text der Mail an Redaktion, wenn ein Sitter geändert wurde.',
        default='Ein neuer Babysitter-Eintrag wurde geändert.',
    )
    sitter_msg_create_subject = schema.TextLine(
        title='Mail an Sitter bei Erstellung: Betreff',
        description='Betreff der Mail an einen neu erstellten Sitter.',
        default=('Ihre Registrierung bei der Babysitterbörse'),
    )
    sitter_msg_create_text = schema.Text(
        title='Mail an Sitter bei Erstellung: Text',
        description=(
            'Text der Mail an einen neu erstellten Sitter. '
            '{url} ist der Platzhalter für den Link zum Eintrag.'
        ),
        default=default_sitter_msg_create_text,
    )
    sitter_msg_publish_subject = schema.TextLine(
        title='Mail an Sitter bei Veröffentlichung: Betreff',
        description='Betreff der Mail an einen Sitter, wenn er veröffentlicht wurde.',
        default=('Freigabe Ihres Babysitter-Eintrages bei der Betreuungsbörse.'),
    )
    sitter_msg_publish_text = schema.Text(
        title='Mail an Sitter bei Veröffentlichung: Text',
        description=(
            'Text der Mail an einen Sitter, wenn er veröffentlicht wurde.'
            '{url} ist der Platzhalter für den Link zum Eintrag.'
        ),
        default=default_sitter_msg_publish_text,
    )

    model.fieldset(
        'contact',
        label='Kontaktaufnahme',
        fields=[
            'contact_from',
            'contact_name',
            'contact_subject',
            'contact_sitter_text',
            'contact_copy_text',
        ],
    )

    contact_from = schema.TextLine(
        title='Absenderadresse der Börse',
        description='Absender-E-Mail-Adresse, nicht antwortfähig',
    )
    contact_name = schema.TextLine(
        title='Absendername der Börse',
        description='Absendername für die Kontakt-E-Mail',
        default='Babysitterbörse',
    )
    contact_subject = schema.TextLine(
        title='Kontakt-E-Mail: Betreff',
        description='Betreff der Kontakt-E-Mail an den Sitter und den Anfragenden.',
        default='Kontaktaufnahme Anzeige Babysitterbörse',
    )
    contact_sitter_text = schema.Text(
        title='Kontakt-E-Mail an Sitter: Text',
        description=(
            'Text der Kontakt-E-Mail an den Sitter.'
            '{text} ist der Platzhalter für den Text der Anfrage.'
        ),
        default=default_contact_sitter_text,
    )
    contact_copy_text = schema.Text(
        title='Kontakt-E-Mail an Anfragenden: Text',
        description=(
            'Text der Kontakt-E-Mail an den Anfragenden.'
            '{text} ist der Platzhalter für den Text der Anfrage.'
        ),
        default=default_contact_copy_text,
    )

    model.fieldset(
        'sitteraccount',
        label='Sitter account page',
        fields=[
            'sitteraccount_faq_sitter',
            'sitteraccount_faq_manager',
            'sitteraccount_intro_text_sitter',
            'sitteraccount_intro_text_manager',
        ],
    )
    sitteraccount_faq_sitter = schema.List(
        title='FQA (für Sitter)',
        description='Häufig gestellte Fragen (für die Sitter)',
        value_type=DictRow(title='tablerow', schema=ISitterFaqConfig),
        default=[
            {
                'question': 'Wie lege ich einen Eintrag an',
                'answer': 'Nach der Registrierung musst du noch die Nutzungsbedingungen akzeptieren. Danach kannst du einen Eintrag anlegen.',
            },
            {
                'question': 'Warum ist mein Eintrag nicht sichtbar',
                'answer': 'Nachdem du den Eintrag erstellt hast. Musst du diesen noch zur Kontrolle einreichen. Danach werden sich die Sittermanager darum kümmern dass der Eintrag freigeschaltet wird.',
            },
        ],
    )
    widget(sitteraccount_faq_sitter=DataGridFieldFactory)

    sitteraccount_faq_manager = schema.List(
        title='FQA (für Sitter)',
        description='Häufig gestellte Fragen (für die Sittermanager)',
        value_type=DictRow(title='tablerow', schema=ISitterFaqConfig),
        default=[],
    )
    widget(sitteraccount_faq_manager=DataGridFieldFactory)

    sitteraccount_intro_text_sitter = schema.Text(
        title='Sitteraccount Seite Intro Text',
        default='Von hier aus kannst du den Anmeldeprozess abschließen, deinen Eintrag bearbeiten und zur Prüfung durch die Redaktion einreichen.',
    )

    sitteraccount_intro_text_manager = schema.Text(
        title='Sittermanager Seite Intro Text',
        default='',
    )


class SitterSettingsForm(RegistryEditForm):
    schema = ISitterSettings
    schema_prefix = 'sitter'
    label = _('Sitter agency')


SitterSettingsView = layout.wrap_form(SitterSettingsForm, ControlPanelFormWrapper)
