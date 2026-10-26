# Raumwerk auf deinem Windows-PC testen

Deine ChatGPT-Chatadresse öffnet den Chat. Die Anwendung und ihre Dateien liegen nicht automatisch auf deinem PC. Lade deshalb zuerst das ZIP-Paket von GitHub herunter. Ein eigener öffentlich erreichbarer Webserver wurde noch nicht eingerichtet.

## 1. Paket herunterladen und entpacken

Öffne https://github.com/cented124/immo_project und klicke im README auf **Windows-Testpaket direkt von GitHub herunterladen**. Alternativ wähle auf der Repository-Seite **Code → Download ZIP**. Melde dich bei GitHub an, falls das Repository eine Anmeldung verlangt.

Klicke die heruntergeladene ZIP-Datei mit der rechten Maustaste an und wähle **Alle extrahieren**. Öffne anschließend den Ordner, in dem `STARTEN.cmd` liegt. Starte die Dateien nicht direkt aus der ZIP-Vorschau.

## 2. Docker Desktop installieren

Öffne https://www.docker.com/products/docker-desktop/ und installiere **Docker Desktop für Windows**. Falls der Installer WSL 2 oder einen Neustart verlangt, folge diesen Schritten. Öffne danach Docker Desktop und warte, bis es betriebsbereit ist. Du brauchst für diesen Weg weder Python noch Node.js oder Git auf deinem PC zu installieren.

## 3. Anwendung starten

Doppelklicke im entpackten Ordner auf **STARTEN.cmd**. Beim ersten Mal werden die Programme und die Datenbank vorbereitet; das kann mehrere Minuten dauern. Lass das Fenster geöffnet. Es erzeugt eigene zufällige Installationsschlüssel und verändert keine vorhandene `.env`.

Beim ersten Start fragt das Fenster nach einer E-Mail-Adresse für deinen Administrator. Lege anschließend ein eigenes neues Passwort mit mindestens zwölf Zeichen fest und bestätige es. Beim Tippen werden keine Passwortzeichen angezeigt; das ist beabsichtigt.

## 4. Anmelden

Der Browser öffnet sich automatisch. Melde dich mit dem eben erstellten Administratorkonto an. Nach dem erfolgreichen lokalen Start auf **deinem PC** lautet die Adresse `http://localhost:3000/admin`. Diese Adresse öffnet keine Anwendung in der Cloud.

## 5. Deine Firma einstellen

Klicke links auf **Website gestalten**. Trage Firmenname, Logo, E-Mail, Telefonnummer und Farben ein. Du kannst Aurevia oder jede andere Firma eintragen. Unter **Seiten & Inhalte** bearbeitest du Texte und Navigation. Wähle **Entwurf speichern**, prüfe **Entwurf ansehen** und klicke erst anschließend auf **Veröffentlichen**.

## 6. Dein PDF einbinden

Öffne **Dokumente** und lade aus dem Paketordner **Deine PDF-Vorlage** die Datei `Aurevia_Mieterselbstauskunft.pdf` hoch. Speichere den Entwurf. Aktiviere danach unter **Module & Formulare** die **Selbstauskunft** und veröffentliche die Einstellungen. Für die optionale Rückgabe aktiviere zusätzlich **Sichere Rückgabe** unter Dokumente.

Die Vorlage enthält vier ausfüllbare Seiten. Die im PDF beschriebenen POSTIDENT- und Türcodeverfahren sind externe Verfahren; diese Anwendung führt keine Identitätsprüfung durch und öffnet keine Türen. Das PDF wird unverändert bereitgestellt.

## 7. Telegram und E-Mail einrichten

Das Downloadpaket enthält **keine Zugangsdaten**. Die Cloud-Einstellungen werden absichtlich nicht mitsamt Passwörtern auf deinen PC kopiert. Trage deine vorhandenen Zugangsdaten lokal unter **Integrationen** ein.

- **Telegram:** Bot-Token und Chat-ID deiner Firmengruppe eintragen, speichern und **Testnachricht senden**. Für die im Chat gewählte Gruppe ist der Bot bereits eingerichtet. Aktiviere anschließend das Telegram-Modul und den gewünschten Zustellweg pro Formular.
- **E-Mail:** SMTP-Host `smtp0101.titan.email`, Port **465**, Verschlüsselung **TLS**, den angegebenen Benutzernamen und das Mailpasswort eingeben. Absender ist die Firmenadresse, Empfänger zunächst die von dir genannte Testadresse. IMAP brauchst du für den Versand nicht. Die Eingangsbestätigung für diesen ersten Test ausgeschaltet lassen.
- Klicke im Rahmen dieser Testserie **einmal** auf **Test-E-Mail senden** und warte auf das Ergebnis. Prüfe auch den Spamordner. Es wurden aus der Cloud zwei erfolglose Verbindungs-/Testversuche durchgeführt und keine E-Mail zugestellt. Bis zur Klärung keine wiederholten Versandtests starten. Falls Port 465 auf deinem PC scheitert, bewahre die Fehlermeldung auf; Port 587 mit STARTTLS ist als Alternative konfigurierbar.

Eine erfolgreiche Meldung besagt, dass der Zielserver die Nachricht angenommen hat. Den tatsächlichen Postfacheingang prüfst du im Empfängerpostfach. Bei der Cloud-Prüfung waren beide SMTP-Ports vor der Anmeldung nicht erreichbar; deshalb ist ein erfolgreicher E-Mail-Livetest noch offen.

## 8. Eine Immobilie ausprobieren

Unter **Immobilien** auf **Immobilie anlegen** klicken. Fülle die Schritte aus, lade eigene Bilder hoch und speichere zunächst als Entwurf. Prüfe das Exposé über die Vorschau. Zur Veröffentlichung benötigst du die tatsächlichen Pflichtangaben; Energieangaben dürfen nicht erfunden werden. Nach der Veröffentlichung findest du das Objekt unter **Website ansehen → Immobilien**. Eine abgesendete Bewerbung erscheint unter **Anfragen** mit dem richtigen Objektbezug.

## 9. Stoppen und später weitermachen

Zum Beenden **STOPPEN.cmd** doppelklicken. Daten bleiben erhalten. Für den nächsten Start Docker Desktop öffnen und wieder **STARTEN.cmd** doppelklicken. Lösche weder die Datei `.env` noch die Docker-Datenvolumes. Die Datei `.env` enthält Installationsgeheimnisse und gehört nicht in eine öffentliche Dateiablage.

## Wenn etwas nicht funktioniert

Notiere, bei welchem Schritt es scheitert, und kopiere den sichtbaren Fehlertext. Teile dabei keine Passwörter oder Tokens. Häufige Ursachen sind ein noch nicht gestartetes Docker Desktop, ein notwendiger Windows-Neustart oder ein bereits belegter Port 3000. Das Startfenster bleibt geöffnet, damit eine Fehlermeldung nicht sofort verschwindet.

Das Paket startet eine lokale Testinstallation. Für einen öffentlichen Internetauftritt brauchst du anschließend ein Hostingziel mit HTTPS und deine geprüften Anbieter-/Datenschutzangaben. Ein Domainwechsel oder eine Veröffentlichung deiner bestehenden Website wird dadurch nicht automatisch vorgenommen.
