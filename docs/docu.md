# Babysitterbörse

Die Babysitterbörse dient der ersten Kontaktaufnahme von Eltern mit Babysittern. Dabei können Angehörige der Philipps-Universität-Marburg (Studierende und Mitarbeiter) ihre Dienste als Babysitter anbieten und Eltern dann mit Ihnen Kontakt aufnehmen.

## aus Sicht des Babysitters

Ein Angehöriger der Philipps-Universität Marburg, der seine Dienste als Babysitter anbieten möchte, meldet sich zuerst mit seinem Staff-/Students-Account an der Babysitter an. Danach kann er nähere Angaben zu sich machen:

- Titel der Babysitter-Anzeige
- Details
- Bild
- Wohnort
- Geschlecht
- Betreuungserfahrung
- Mobilität
- Geburtsdatum
- Sprachen
- Qualifikationen und Auszeichnungen
- Sonstige Qualifikationen

Nur die Eingabe eines Titels für die Babysitter-Anzeige ist Pflicht. Alle anderen Felder können, müssen aber nicht, ausgefüllt werden.

![](images/create-sitter.png)

_Bild 1: Anlegen einer Babysitter-Anzeige_

Ist der Babysitter mit der Eingabe der Daten fertig, so ist die Anzeige noch nicht gleich im Internet veröffentlicht. Er muss diese erst noch zur Redaktion einreichen.

![](images/submit-sitter.png)

_Bild 2: Einrichen einer Babysitter-Anzeige_

Die Redaktion prüft die Babysitter-Anzeige und veröffentlicht sie im Internet. Der Babysitter kann später jederzeit seine Babysitter-Anzeige ändern, ohne dass sie erneut eingereicht werden muss. Auch kann er sie löschen. Dabei wird sie zunächst offline gestellt und nach spätestens 7 Tagen endgültig vom Server gelöscht.

## aus Sicht eines Redakteurs

### Eine Babysitter-Anzeige veröffentlichen

Meldet sich eine Redakteurin an der Babysitterbörse an, so sieht sie in der linken Spalte ein Liste aller Babysitter-Anzeigen (Revisionsliste), die auf einen Freigabe warten.

![](images/revision-list.png)

_Bild 3: Revisionsliste_

Öffnet Sie eine solche Anzeige, kann sie oben den Status von "zur Redaktion eingereicht" in "Veröffentlicht" ändern. Danach ist die Anzeige im Internet sichtbar.

![](images/publish-sitter.png)

_Bild 4: einen Babysitter-Eintrag veröffentlichen_

### Menü für Redakteure

![](images/manager-menu.png)

_Bild 5: Menü für Redakteure_

#### Ordner Inhalt anzeigen

Durch einen Klick auf "Ordner Inhalt anzeigen" gelangt man in die Standard-Ordnerauflistung von Plone und sieht dort alle Objekte dieses Ordners.

### Ordner Eigenschaften bearbeiten

Hier können Einstellungen für die Babysitterbörse vorgenommen werden, diese sind als Eigenschaften des Babysitter-Ordners implementiert, u.a. auch welche Erfahrungs- und Qualifikations-Optionen beim Erstellen einer Babysitter-Anzeige zur Auswahl stehen sollen. (siehe unten)

#### Nutzungsbedingungen und Info-Text für angemeldete bzw. unangemeldete Benutzer bearbeiten

Durch einen Klick in der linken Spalte auf "Nutzungsbedingungen bearbeiten", "Info-Text für unangemeldete Benutzer bearbeiten" bzw. "Info-Text für angemeldete Benutzer bearbeiten" können die entsprechenden Texte geändert werden.

#### alte Sitter löschen

Folgt man dem Link "alte Sitter löschen", kommt man zu einer Seite auf der zu sehen ist, wie viele Babysitter-Anzeigen den Status "privat" länger als 90 Tage und "deleting" länger als 7 Tage haben. (Die Anzahl der Tage kann konfiguriert werden - siehe unter "Administration") Mit einem Klick auf den Button "Löschen" unterhalb des jeweiligen Abschnitts können die entsprechenden Anzeigen gelöscht werden. Die Löschung muss aber nicht manuell erfolgen, sondern wird auch automatisch jede Nacht ausgeführt.

![](images/delete-private-deleteting-objects.png)

_Bild 6: Nicht veröffentlichte Babysitter-Anzeigen löschen_

### Babysitter-Erfahrung bzw. Babysitter-Qualifikation abändern/hinzufügen

Sowohl bei dem Feld Erfahrung als auch Qualifikationen handelt es sich um Auswahlfelder. Die jeweils zur Verfügung stehenden Optionen werden wie folgt konfiguriert: Jede Erfahrungs-Option entspricht einem Objekt des Types Babysitter-Erfahrung und jede Qualifikations-Option entspricht einem Objekt des Types Babysitter-Qualifikation. Diese Objekte können wie andere Plone-Objekte auch über den "Hinzufügen ..."-Dialog erstellt werden.

![](images/create-qualification-experience.png)

_Bild 7: Objekte für Babysitter-Erfahrung bzw. Babysitter-Qualifikation erstellen_

Ist ein solches Objekt erstellt, muss es anschließend veröffentlicht werden. Danach muss es unter "Ordner Eigenschaften bearbeiten" der entsprechenden Liste hinzugefügt werden.

![](images/add-qualification-experience.png)

_Bild 8: Qualifikation- bzw. Erfahrungs-Objekte zur jeweiligen Auswahlliste hinzufügen_

### Administration

#### Konfigurationseinträge (portal_registry)

Suchen nach `sitter`:

![](images/configuration-portal-registry.png)

_Bild 9: Konfigurationseinträge ändern_

Durch einen Klick auf die jeweilige Eigenschaft kann der Wert dieser verändert werden.

##### days_until_deletion_of_deleting_sitters

Tage bis zum löschen markierte Sitter-Objekte gelöscht werden.

##### days_until_deletion_of_private_sitters

Tage bis private Sitter-Objekte gelöscht werden

##### reviewer_email

E-Mail-Adressen (durch Komma getrennt) an die die Redaktions-E-Mails versendet werden sollen, z.B. eine E-Mail, dass eine neue Babysitter-Anzeige erstellt wurde.

##### sitters_per_page

Anzahl der Babysitter-Anzeigen auf einer Seite
