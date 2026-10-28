# Nachweis der lokalen Abnahme

Stand: 28.10.2026. Alle Daten in automatisierten Tests sind ausdrücklich synthetisch. Keine Beispielimmobilie wurde im eigentlichen Entwicklungsdatenbestand veröffentlicht.

| Prüfung | Ergebnis |
| --- | --- |
| Python-Integrationstests mit temporärem SQLite | **37 bestanden** (einschließlich 6 Desktop-Grenzprüfungen) |
| Dieselbe Suite mit echtem PostgreSQL 17 (Docker) | **31 bestanden** |
| Playwright / Chromium – Desktop und mobile Ansicht | **16 bestanden** |
| TypeScript `tsc --noEmit` | bestanden |
| Next.js Produktionsbuild | bestanden |
| `docker compose config --quiet` | bestanden |
| API- und Web-Images bauen | bestanden |
| Compose: PostgreSQL, API, Web | gestartet, Datenbank-/API-Healthchecks bestanden |
| Compose: Login, geschützter Bild-Upload und anonymer Zugriff | Login/Upload erfolgreich; anonymer Abruf **401** |
| Compose: API/Web-Neustart | Anmeldung und Dateiprüfsumme erhalten |
| Verschlüsseltes Backup und isolierte PostgreSQL-Wiederherstellung | AES256-Archiv entschlüsselt, Datenbank separat wiederhergestellt, Benutzeranzahl und Dateiprüfsumme geprüft |
| Vollständiger Restore in frischen Compose-Volumes | Datenbank und Dateien zurückgespielt, Dateieigentümer korrigiert, restaurierte Anwendung gestartet, Login und geschützter Dateiabruf mit identischer Prüfsumme erfolgreich |
| Gespeicherte Installations-/Startscripts | `scripts/install.sh` und `scripts/dev.sh` tatsächlich ausgeführt |
| Desktop-/Mobil-Sichtprüfung | Startseite und Admin gesichtet; kein horizontaler Überlauf der mobilen Startseite |

## Inhalt der ursprünglichen 14 Backendtests

1. Login, fehlende Sitzung, Rollen, CSRF-Originprüfung, Logout.
2. Beliebiger Firmenname, unveröffentlichter Entwurf, Veröffentlichung und Erhalt nach neuem App-Lebenszyklus.
3. Modulabschaltung sperrt Immobilien-API, Detail-API, öffentliche Bilder und Kontaktannahme.
4. Entwurf → Veröffentlichung → objektgebundene Bewerbung → Archivierung; verborgene Straßenadresse, Suchfilter, zurückgezogene bekannte Links.
5. Veröffentlichungsprüfung, Warmmietenberechnung ohne doppelte Heizkosten und private Duplikate.
6. Idempotenz, widersprechende Mehrfachübermittlung, Datenschutzpflicht, Honeypot, ungültige E-Mail und Ratelimit.
7. Anfragenfilter, interner Vermerk, Status, CSV-Formelinjection-Schutz und Löschung.
8. PDF-Austausch, aktueller Download, private Rückgabe mit persönlichem Rückgabecode, falscher Code, Zugriff ohne Sitzung und Moduldeaktivierung.
9. Unzulässige Uploads und Template-Manifeste; beide mitgelieferten Adapter.
10. Tatsächlich gespeicherte Ereignisse, Formulare, Tageswerte und fehlende Analyticsdaten bei deaktiviertem Modul.
11. **Echter lokaler SMTP-Testserver**: Testmail, Outbox-Zustellung, Firmen-Absender, Reply-To und verschlüsselte/maskierte Zugangsdaten.
12. **Lokaler HTTP-Testserver für die Telegram Bot API**: reale HTTP-Anfrage, Antwortauswertung, Testnachricht, Outbox und datensparsame Benachrichtigung.
13. Erreichbarkeitsfehler, maximal vier Versuche, manueller Retry und Löschung ausschließlich technischer Anfragedaten nach 24 Stunden.
14. Einstellbare Telefonpflicht, ungültige Konfiguration und fehlendes eigenes PDF als Veröffentlichungsblocker.

Die Suite erzeugt ihr Schema durch Alembic. PostgreSQL-Testdatenbank und E2E-Datenbank sind vom lokalen Entwicklungsbestand getrennt. Eine DeprecationWarning aus Starlette/AnyIO ist sichtbar; sie hat keinen Test übersprungen.

## Inhalt der zehn Browserprüfungen

Je fünf Durchläufe auf Desktop und emulierter mobiler Chromium-Ansicht:

- Öffentliche Startseite, CTA, responsive Breite, echte Kontaktannahme und Annahmebestätigung.
- Adminlogin, anderer Firmenname in geschützter Entwurfsvorschau, Anfragebearbeitung, interner Vermerk, Logout.
- Immobilienassistent, Bild-Upload, privater gespeicherter Entwurf und öffentlich weiterhin leere Liste.
- Vollständiger Inseratsassistent bis Veröffentlichung; öffentliches Exposé; Bewerbung mit korrekter Objekt-ID; Modul per Adminoberfläche abschalten, Navigation und API prüfen; wieder aktivieren und Inserat zurückziehen.

Ein mobiler Menüfehler wurde dabei gefunden und korrigiert: Die lange Adminnavigation ist jetzt scrollbar, sodass auch „Abmelden“ erreichbar bleibt. Zusätzliche Testfehler durch zu strikte Select-Locators wurden durch semantische Combobox-Locators behoben; keine Prüfungen wurden dafür entfernt.

## Docker und Cloud-Netzwerk

Der erste Cloud-Build scheiterte an der DNS-Auflösung des Cloudproxies innerhalb der Buildcontainer. Für die lokale Abnahme wurde ein **temporärer, nicht ausgelieferter** Compose-Buildoverride mit Proxy-Hostzuordnung und dem bereits bereitgestellten Cloud-CA-Zertifikat als BuildKit-Secret verwendet. Python/npm verifizierten TLS weiterhin. Es wurden weder Zertifikats- noch Signaturprüfungen abgeschaltet.

Ein anschließend gefundener Dateirechtefehler im API-Image wurde durch `COPY --chown=app:app` behoben. Das ausgelieferte Image läuft als unprivilegierter Benutzer. Die regulären Dockerfiles sind für einen normalen Dockerhost ohne diese Cloud-spezifische Proxyhilfe ausgelegt. Der Validierungsverbund lief getrennt auf Port 3002; die Entwicklung auf Port 3000.

## Nicht behauptete Ergebnisse

- **SMTP extern nicht bestätigt**: zwei Anwendungstests, Port 465/TLS und 587/STARTTLS; Verbindungen vor der Anmeldung abgelehnt. Keine E-Mail angenommen oder zugestellt. Kein weiterer Live-Mailtest gestartet. Telegram ist dagegen mit drei bestätigten Nachrichten live geprüft.
- Das jetzt gelieferte Original-PDF wurde zusätzlich geprüft: vier Seiten, 27 leere AcroForm-Felder, kein JavaScript, identischer Download-Hash. Synthetische PDF-Fixtures bleiben ausschließlich in Tests.
- **Keine öffentliche Bereitstellung**, Domain-/TLS-Konfiguration oder Veröffentlichung eines neuen Cloud-Snapshots nachgewiesen.
- **Keine externe Backupablage eingerichtet**; lokale Verschlüsselung und Restore wurden geprüft.
- Mobile Browsertests emulieren eine mobile Ansicht in Chromium; kein Test auf einem physischen iPhone/Safari.
- Template-Manifestprüfung bedeutet keine automatische Kompatibilität mit beliebigem fremden HTML/React.
- Impressum/Datenschutz sind gekennzeichnete Muster und benötigen rechtliche Prüfung.

## Ergänzte Nachweise dieser Nachprüfung

Neun zusätzliche Backendtests prüfen persistenten Template-Import und Script-Abweisung, Seitenformularziele/-statistik, Kontosperren/letzten Administrator, Passwortänderung/Sitzungswiderruf, atomare deduplizierte Dokumentannahme mit eigenen Jobs, private Modulvorschau, Chunked-Uploadlimit, Umlaut-/Notizensuche mit gefiltertem CSV sowie temporäre Telegram- und permanente SMTP-Fehler. Diese damaligen 23 Fälle wurden auf SQLite und echtem PostgreSQL ausgeführt.

Zwei zusätzliche Browserdurchläufe prüfen auf Desktop und Mobilgerät: Manifest importieren, Editorial-Vorschau, Navigation erhält preview=1, Vorschauformulare sind gesperrt, eigene Formularziele speichern und Kontoseite anzeigen. Insgesamt zehn Browserfälle bestanden.

Live: Der vom Benutzer vorgegebene Gruppenchat wurde vor Zustellung geprüft. Eine echte Testnachricht sowie zwei Outbox-Jobs (Kontakt und private PDF-Rückgabe) wurden von Telegram bestätigt. Der identische PDF-Rückgabeversuch erzeugte weder eine zweite Datei noch einen zweiten Zustellauftrag. Keine PDF-Datei wurde an Telegram übertragen. Die E-Mail-Zustellung für die Testserie bleibt deaktiviert; das Empfängerpostfach wurde nicht per IMAP gelesen.

Windows-Hilfe: PowerShell-Syntax und kontrollierte Trockenläufe unter PowerShell im offiziellen Linux-Container bestanden. Geprüft wurden Erstinstallation, zufällige Installationsschlüssel, Erstadmin-Zweig, Wiederholungsstart und Erhalt einer bestehenden .env. Docker wurde dabei simuliert; eine echte Windows-/Docker-Desktop-GUI-Prüfung wird nicht behauptet. Zusätzlich wurden Migrationen und die Erstadmin-Erkennung des tatsächlichen neuen API-Images ohne vorhandenes Konto geprüft.

## Frontend-Studio und Projektexport, 27.10.2026

Acht neue Backendfälle prüfen strukturierte Firmen-/Registerdaten im Prompt, tatsächlichen vollständigen Referenzexport ohne gespeicherte Betriebsgeheimnisse, JSON-/ZIP-Designimport und Script-/Pfadabweisung, private Entwurfsaktivierung vor Veröffentlichung, fehlende Medien und Kontrastwarnungen, Versionsvergleich/Wiederherstellung ohne sofortige Veröffentlichung, Adminrechte, Domainvalidierung, Loginlimits und explizite Proxy-Vertrauensgrenze.

Der Projektexport wird mit Immobilienbild, interner Objekt-PDF, Selbstauskunft-Vorlage, synthetischer Anfrage und synthetischem Integrationstoken erzeugt. Das Archiv wird auf fehlende Geheimnisse/Anfragedaten geprüft und in einer separaten leeren Installation nach echten Alembic-Migrationen importiert. Geprüft werden öffentliche Config/Immobilie/Bild, private Dokumente, fehlende Benutzer/Anfragen/Outbox, deaktivierte externe Zustellung, wiederholter Start ohne Überschreiben und Abweisung veränderter Medienprüfsummen vor jeder Datenübernahme.

Vier neue Browserfälle (je zwei auf Desktop und Mobilgerät) bedienen das Firmenformular, generieren den Prompt, laden das Referenz-ZIP herunter, prüfen/importieren ein Version-2-Design, zeigen die echte Split-/Listen-Vorschau, erzeugen den Domainplan, laden das Projekt-ZIP herunter und stellen eine verglichene Konfiguration nur als Entwurf wieder her. Beide Ansichten werden auf seitliches Überlaufen geprüft. [Echte Screenshots](screenshots/README.md) liegen im Repository. Jede Browser-Suite bekommt einen eigenen isolierten Datenordner und versendet keine externen Nachrichten.

Nicht als geprüft ausgegeben werden ein fremder noch nicht bereitgestellter VPS, öffentliche DNS-Umstellung, öffentlich ausgestelltes Zertifikat für eine Kundendomain oder beliebiger von Dritten veränderter React-Code. Dafür werden Startprogramm, HTTPS-Prüfhelfer und die dokumentierte Abnahme geliefert. Es wurden in dieser Erweiterung keine weiteren echten E-Mails oder Telegram-Nachrichten gesendet.

Zusätzliche Abnahme mit gebauten Docker-Images: Ein synthetisches Projekt wurde exportiert, mit restriktiven Host-Dateirechten in ein eigenes API-Image eingebaut und in einem separaten frischen Compose-Projekt mit PostgreSQL gestartet. Bestanden: automatischer Erstimport, Website/öffentliche API/Bild, Authentifizierung, KI-Referenzexport inklusive öffentlichem OpenAPI-Vertrag, erneuter Projektexport aus dem Container, fortlaufende PostgreSQL-Immobilien-ID, echte Anfrageannahme ohne externe Zustelljobs sowie Neustart mit erhaltenen Inhalten und Sitzungen. Die Seeddateien werden beim Build dem App-Benutzer zugeordnet; die API läuft ohne root. Caddy-Konfiguration im offiziellen Container validiert; HTTPS und Redirect sind konfiguriert. Keine öffentliche Kundendomain wurde dafür verwendet.

GitHub Actions ist für Backendtests, Produktionsbuild, Desktop-/Mobiltests, Compose-Konfiguration und Downloadprüfsumme eingerichtet. Ein erfolgreicher GitHub-Lauf wird erst durch den tatsächlichen Status auf GitHub nachgewiesen; lokale Ergebnisse sind davon getrennt.

## Vollständige Nutzersimulation

Am 27.10.2026 wurde der Ablauf mit zwei getrennten Browsersitzungen und der fiktiven Küstenklar Immobilien GmbH vollständig über die Oberfläche durchgespielt: Firmendaten, Seiten, PDF, Immobilienassistent, Prompt/Referenz, eigenes Designpaket, Prüfung/Import/Veröffentlichung und Projektexport. Das Exportprojekt wurde als separate Docker-Installation mit PostgreSQL, Admin und lokalem HTTPS gestartet. Eine zweite Person suchte die Wohnung und stellte eine Objektanfrage; genau eine echte Telegram-Nachricht wurde von der offiziellen API für B1 Gruppe angenommen, Outbox `sent` nach einem Versuch. Anschließend erfolgten Adminprüfung, Notiz, Statusänderung und CSV-Export. Keine E-Mail wurde verschickt. [Bebilderter Nachweis und Demo-Download](SIMULATION.md).

Dabei wurde ein Fehler beim schnellen Wechsel der Integrationstabs gefunden und behoben. Zwei zusätzliche Browserfälle mit bewusst verspäteter Antwort (Desktop/Mobil) sichern ihn ab. Die vollständige Suite mit nun 16 Fällen besteht; der korrigierte Produktionsbuild wurde ebenfalls in der tatsächlichen Simulation verwendet.

## Windows ohne Docker, 28.10.2026

Der echte [Windows-/Edge-Lauf 40606056994](https://github.com/cented124/immo_project/actions/runs/40606056994) ist erfolgreich. Er verwendet Windows PowerShell 5.1, eingebettetes CPython 3.13.17 x64 und Node 24.19.0 für Windows. Der Arbeitsordner enthält Leerzeichen, Umlaut und Apostroph. Browser-Ersteinrichtung, Login, Mehrfachstart, belegter Port, Bild-Upload, veröffentlichte Immobilie, anonyme Objektanfrage, Adminsicht, Neustart, erhaltener Verschlüsselungsschlüssel und ZIP-Sicherung sind bestanden. Es wurden keine externen Nachrichten gesendet.

Das anschließend gebaute Laufzeitpaket wurde in einen anderen Ordner entpackt. Der ursprüngliche Buildordner wurde umbenannt, damit alte absolute Pfade tatsächlich ungültig sind. Mit auf einen nicht erreichbaren Proxy gesetztem externen HTTP(S)-Zugriff bestand derselbe vollständige Browserdurchlauf erneut. Python, Node, Backend-Pakete und Frontend mussten dabei nicht erneut heruntergeladen werden. [Screenshots der Windows-Einrichtung und Adminsicht](screenshots/README.md).

Der entsprechende [Linux-GitHub-Lauf 40606056954](https://github.com/cented124/immo_project/actions/runs/40606056954) bestand ebenfalls: 37 Backendfälle, Produktionsbuild, 16 Desktop-/Mobilbrowserfälle, Compose-Konfiguration und Download-Prüfsummen. Die sechs zusätzlichen Desktopfälle prüfen begrenzte Chunked-Anfragen, Setup-/Origin-/Host-Schutz, Steuerungszugriff, Cookie-/Downloadweitergabe, Prozesssperren und die Ablehnung externer Steuerungsadressen.

Im abschließenden lokalen nativen Browserdurchlauf wurde außerdem ein vollständiges Projekt-ZIP über die laufende Anwendung exportiert und nach echten Migrationen in eine leere separate SQLite-Datenbank übernommen: Firma, Immobilie und Bild vorhanden, keine Benutzer/Anfragen/Zustelljobs/Integrationsgeheimnisse, zweiter Import ohne Überschreiben. Derselbe Export-/Importnachweis ist im Windows-Workflow eingebaut. Eine gemeinsame Startsperre verhindert das Wiederöffnen der Datenbank während der Desktop-Sicherung.

Der [Windows-Workflow](https://github.com/cented124/immo_project/actions/workflows/windows.yml) veröffentlicht auf `main` das fertige ZIP erst nach erfolgreichem Browser-, Export-/Import- und Offline-Umzugstest. Windows-Runner sind keine Prüfung jeder Windows-10/11-Hardware, ARM-Plattform oder Firmenrichtlinie. Die Desktop-Installation ist lokal gebunden; ein öffentlicher Domain-/VPS-Livegang wird daraus nicht abgeleitet. Architektur und Grenzen: [WINDOWS-DESKTOP.md](WINDOWS-DESKTOP.md).
