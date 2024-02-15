from .. import _
from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from datetime import date
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform.directives import widget
from plone.supermodel import model
from plone.z3cform import layout
from zope import schema
from zope.interface import Interface


default_sitter_msg_create_text = """\
Vielen Dank für Ihre Registrierung bei der Babysitterbörse.

Falls nicht bereits geschehen, reichen Sie bitte Ihren Babysittereintrag nach
der Erstellung zur Redaktion ein. Er wird dann geprüft und freigegeben.

{url}

--
Mit freundlichen Grüßen
"""

default_sitter_msg_publish_text = """\
Ihr Babysittereintrag bei der Betreuungsbörse wurde freigegeben und ist unter
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

default_renewal_reminder_text = """\
Guten Tag {toname},

die Betreuungsbörse wird zum Monatsende inaktive Nutzer und Anzeigen löschen.

Um Ihre bestehende Anzeige weiter zu nutzen, melden Sie sich bitte vor Monatsende
einmal am Portal an: {portal_url}

Mit freundlichen Grüßen
"""


def check_renewal_schedule(value):
    year = date.today().year
    prev_deletion = None
    for line in value.splitlines():
        if not (line := line.strip()):
            continue
        items = line.split(',')
        if len(items) != 4:
            return False
        try:
            login_after, reminder1, reminder2, deletion = [
                date.fromisoformat(f'{year}-{item.strip()}') for item in items
            ]
        except ValueError:
            return False
        if not login_after <= reminder1 < reminder2 < deletion:
            return False
        if prev_deletion and prev_deletion > login_after:
            return False
        prev_deletion = deletion

    else:
        return True


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
        default='Babysittereintrag erstellt',
    )
    reviewer_msg_create_text = schema.Text(
        title='Mail an Redaktion bei Erstellung: Text',
        description='Text der Mail an Redaktion, wenn ein Sitter erstellt wurde.',
        default='Ein neuer Babysittereintrag wurde erstellt.',
    )
    reviewer_msg_submit_subject = schema.TextLine(
        title='Mail an Redaktion bei Einreichung: Betreff',
        description='Betreff der Mail an Redaktion, wenn ein Sitter eingereicht wurde.',
        default='Babysittereintrag eingereicht',
    )
    reviewer_msg_submit_text = schema.Text(
        title='Mail an Redaktion bei Einreichung: Text',
        description='Text der Mail an Redaktion, wenn ein Sitter eingereicht wurde.',
        default='Ein neuer Babysittereintrag wurde eingereicht.',
    )
    reviewer_msg_modify_subject = schema.TextLine(
        title='Mail an Redaktion bei Änderung: Betreff',
        description='Betreff der Mail an Redaktion, wenn ein Sitter geändert wurde.',
        default='Babysittereintrag geändert',
    )
    reviewer_msg_modify_text = schema.Text(
        title='Mail an Redaktion bei Änderung: Text',
        description='Text der Mail an Redaktion, wenn ein Sitter geändert wurde.',
        default='Ein neuer Babysittereintrag wurde geändert.',
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
        default=('Freigabe Ihres Babysittereintrages bei der Betreuungsbörse.'),
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
        'renewal',
        label='Erneuerung der Anzeigenaktivität',
        fields=[
            'renewal_schedule',
            'renewal_reminder_subject',
            'renewal_reminder_text',
        ],
    )

    renewal_schedule = schema.Text(
        title='Zeitplan für Erneuerung',
        description=(
            'Zeitplan für die Erneuerung der Anzeigenaktivität. '
            'Jede Zeile ist ein Lauf mit vier Daten im Format '
            '"MM-TT,MM-TT,MM-TT,MM-TT". Die Daten sind Beginn des Anmeldezeitraums, '
            'Tag der ersten und zweiten Erinnerungs-E-Mail und Tag der Löschung.'
            'Die Datumsangaben müssen über alle Läufe hinweg aufsteigend geordnet sein, '
            'und die Erinnnerungs-E-Mails eines Laufs dürfen nicht auf denselben Tag '
            'oder den Tag der jeweiligen Löschung fallen.'
        ),
        default="03-01,03-01,03-15,04-01\n09-01,09-01,09-15,10-01",
        constraint=check_renewal_schedule,
    )
    renewal_reminder_subject = schema.TextLine(
        title='Erinnerungs-E-Mail für Erneuerung: Betreff',
        description='Betreff der Erinnerungs-E-Mail, sich am Portal anzumelden.',
        default='Erneuerung Anzeige Babysitterbörse',
    )
    renewal_reminder_text = schema.Text(
        title='Erinnerungs-E-Mail für Erneuerung: Text',
        description=(
            'Text der Erinnerungs-E-Mail, sich am Portal anzumelden.'
            '{toname} ist der Platzhalter für den Namen des Nutzers, '
            '{portal_url} für die Basis-URL des Portals.'
        ),
        default=default_renewal_reminder_text,
    )

    model.fieldset(
        'sitteraccount',
        label=_('sitter_account_page'),
        fields=[
            'sitteraccount_faq_sitter',
            'sitteraccount_faq_manager',
            'sitteraccount_intro_text_sitter',
            'sitteraccount_intro_text_manager',
        ],
    )
    sitteraccount_faq_sitter = schema.List(
        title=_('faq_sitter_label'),
        description=_('faq_sitter_description'),
        value_type=DictRow(title='tablerow', schema=ISitterFaqConfig),
        default=[],
    )
    widget(sitteraccount_faq_sitter=DataGridFieldFactory)

    sitteraccount_faq_manager = schema.List(
        title=_('faq_sittermanager_label'),
        description=_('faq_sittermanager_description'),
        value_type=DictRow(title='tablerow', schema=ISitterFaqConfig),
        default=[],
    )
    widget(sitteraccount_faq_manager=DataGridFieldFactory)

    sitteraccount_intro_text_sitter = schema.Text(
        title=_('sitteraccont_intro_label'),
        default='',
    )

    sitteraccount_intro_text_manager = schema.Text(
        title=_('sittermanager_intro_label'),
        default='',
    )


class SitterSettingsForm(RegistryEditForm):
    schema = ISitterSettings
    schema_prefix = 'sitter'
    label = _('Sitter agency')


SitterSettingsView = layout.wrap_form(SitterSettingsForm, ControlPanelFormWrapper)
