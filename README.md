# Raumwerk – firmenneutraler Immobilien-Baukasten

Eine selbst hostbare Anwendung für **ein beliebiges Unternehmen und eine Website**. Firmenname, Logo, Farben, Schriften, Kontaktdaten, Inhalte und Template sind Einstellungen. Der Startwert „RAUM & WERT“ ist eine austauschbare Musteridentität; Aurevia ist keine fest eingebaute Firma. Es gibt keine Mehrmandantenverwaltung oder Abrechnung.

## Was enthalten ist

- Next.js 16 / React 19 / TypeScript: responsive Website, geschützter Adminbereich, Template „Atelier“ und zweiter Adapter „Editorial“.
- Frontend-Studio mit Firmen-/Registerdaten, KI-unabhängigem Prompt, exportierbarem vollständigem Referenzprojekt, versioniertem Designimport, Vorschau und Prüfung.
- Konfigurationsvergleich und Wiederherstellung; fertiger Projektexport inklusive Inhalten/Medien und geführtem VPS-Livegang mit Caddy/HTTPS.
- FastAPI, SQLAlchemy, Alembic; PostgreSQL 17 im Compose-Betrieb. SQLite als bewusst einfache lokale Entwicklungsoption.
- Konfigurationsentwurf, authentifizierte Vorschau und explizite Veröffentlichung. Module sperren Darstellung **und öffentliche API-/Dateizugriffe**.
- Login mit Argon2id, serverseitige Sitzungen, Administrator-/Mitarbeiterrollen.
- Immobilienassistent, Entwürfe, Veröffentlichung, Rückzug, Duplizieren, Medien, Suchfilter, Pagination und Detailseiten.
- Kontakt und objektgebundene Bewerbungen; Anfragenstatus, Notizen, Filter, CSV-Export und Löschung.
- Verschlüsselte SMTP-/Telegram-Einstellungen, echte Verbindungstests, persistente Outbox mit begrenzten Wiederholungen und manueller Wiederaufnahme.
- Eigenes PDF hochladen/austauschen; optionale private Rückgabe zu einer bestehenden Anfrage. Die bereitgestellte leere Originalvorlage liegt unter **Deine PDF-Vorlage**; es wurde kein Ersatzdokument erfunden.
- Eigene Ereigniserfassung und Dashboard mit tatsächlichen Daten. Ohne externe Tracker und ohne Fingerprinting.

## Einfacher Start unter Windows

Ein vollständiger Durchlauf mit Musterfirma, Wohnung, eigenem Frontend, Docker-Deployment, echter Telegram-Zustellung und Adminbearbeitung ist unter [Simulation mit Screenshots und Demo-Download](docs/SIMULATION.md) dokumentiert.

**Ohne Docker:** Lade das **[fertige Windows-Paket mit Laufzeiten](https://github.com/cented124/immo_project/releases/latest/download/Raumwerk-Windows-ohne-Docker.zip)** herunter, entpacke es und öffne `STARTEN.cmd`. Python, Node.js und das gebaute Frontend sind enthalten; die erste Administratoranlage erfolgt im Browser. Für Windows 10/11 x64. Falls GitHub eine Anmeldung verlangt, das Konto mit Repositoryzugriff verwenden.

Alternativ richtet das **[kleine Windows-Quellpaket](https://github.com/cented124/immo_project/raw/refs/heads/main/downloads/Raumwerk-Windows.zip)** die festgelegten Laufzeiten beim ersten Start automatisch über das Internet ein. Es installiert nichts systemweit. Details: [einfache Windows-Anleitung](ANLEITUNG-WINDOWS.md).

Lokale Daten liegen unter `DATEN`, Programme getrennt unter `.runtime`. `STOPPEN.cmd`, `SICHERN.cmd`, `DIAGNOSE.cmd` und `REPARIEREN.cmd` unterstützen den Betrieb. Docker-/WSL-Dienste und eine separate Datenbank werden für diesen lokalen Startweg nicht benötigt. Der VPS-Start bleibt unabhängig davon verfügbar.

Alternativ auf dieser Repository-Seite **Code → Download ZIP** auswählen. Öffne nach dem Entpacken den Ordner, in dem `STARTEN.cmd` liegt. `STARTEN.cmd` richtet die lokale Anwendung ohne Docker ein; `STOPPEN.cmd` erhält deine Daten. Die Downloads enthalten vollständigen Quellcode und die leere PDF-Vorlage, aber keine Zugangsdaten oder Kundendatenbanken.

## Schnellstart: lokal

Voraussetzungen: Python 3.12+, Node 24, npm. Aus dem bestehenden Checkout arbeiten; eine Cloud-Aufgabe ist bereits isoliert und braucht keinen weiteren Git-Worktree.

```bash
cd /workspace/immo_project
bash scripts/install.sh
PYTHONPATH=backend .venv/bin/python -m app.cli create-admin --email sie@unternehmen.de
bash scripts/dev.sh
```

Der CLI-Dialog fragt das Passwort zweimal verdeckt ab; mindestens zwölf Zeichen. Es gibt im Quellcode **kein allgemeingültiges Standardpasswort**. Website lokal auf Port 3000, Adminpfad `/admin`. Die API wird über dieselbe Origin unter `/api` angesprochen. `scripts/dev.sh` startet Backend und Website, installiert aber nichts nach.

Für den bereits vorbereiteten Cloud-Arbeitsbereich wurde ein zufälliger lokaler Zugang angelegt. Er liegt ausschließlich in der ignorierten Datei `.local/zugang.txt` mit Modus 0600; er ist nicht Bestandteil der Auslieferung oder des Images. Verwenden Sie für einen eigenen Betrieb Ihren eigenen Administrator.

Lokale Daten: `.local/data/app.db`, `.local/data/files/` und `.local/data/encryption.key`. Diese Dateien überleben Prozessneustarts. Die Schlüsseldatei ist zum Entschlüsseln der Integrationseinstellungen notwendig. Änderungen an `DATABASE_URL` oder `DATA_DIR` wählen einen anderen Datenbestand; SQLite wird nicht automatisch nach PostgreSQL kopiert.

## Reproduzierbarer Betrieb mit Docker Compose

```bash
python3 scripts/configure.py --origin http://localhost:3000
docker compose up -d --build
docker compose exec api python -m app.cli create-admin --email sie@unternehmen.de
```

`configure.py` erzeugt einmalig eine `.env` mit zufälligem Datenbankpasswort und Fernet-Schlüssel und überschreibt keine bestehende Datei. Die Datenbankmigration läuft beim Backendstart. Persistente Volumes: `database` und `files`. Nur die Website wird an `127.0.0.1:3000` gebunden; weder PostgreSQL noch das Backend besitzen im Compose-Betrieb einen öffentlichen Host-Port.

Für eine echte Domain: **Export & Livegang** im Admin öffnen und der [VPS-Anleitung](docs/DEPLOYMENT.md) folgen. `bash LIVE-STARTEN.sh` startet zusätzlich Caddy mit automatischem HTTPS. Die mitgelieferte Produktionskonfiguration überschreibt Client-IP-Header am öffentlichen Proxy und vertraut ihnen ausschließlich in der internen API. Bei einer eigenen Proxykonfiguration gelten die [Betriebsgrenzen](docs/OPERATIONS.md).

```bash
docker compose logs --tail=50 api web
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').status)"
docker compose restart api web
```

`docker compose down` erhält Volumes; **`down -v` löscht Daten**. Produktion mit separater Domain und Administrator einrichten; niemals den isolierten E2E-Testserver veröffentlichen.

## Erste Einrichtung ohne Programmierung

1. Unter `/admin` anmelden. **Firma & Rechtliches**: Unternehmensprofil einschließlich Registerdaten und Rechtstexten eintragen. **Design & Medien**: Logo, Farben, Schrift und Bilder einstellen.
2. **Seiten & Inhalte**: Startseite, Titelbild, Leistungen, Vorstellung, Seiten, Navigation, Footer und SEO anpassen. Abschnitte verschieben und ausblenden.
3. **Entwurf speichern**, anschließend **Entwurf ansehen**. Veröffentlichung ist ein separater Schritt.
4. **Module & Formulare**: benötigte Funktionen aktivieren und pro Kontakt-/Bewerbungsformular Speicher- und Zustellziele wählen. Ohne dauerhaftes Speichern werden technische Zustelldaten nach höchstens 24 Stunden gelöscht.
5. **Integrationen** einrichten und testen. Ohne SMTP/Telegram funktioniert die Speicherung im Adminbereich bereits.
6. **Immobilien**: Entwurf anlegen, echte Angaben und eigene Bilder ergänzen, gespeichertes Exposé prüfen und veröffentlichen. Der Assistent prüft fehlende Veröffentlichungsangaben.
7. **Dokumente**: Ihr eigenes Selbstauskunft-PDF hochladen und anschließend das Modul einschalten. Sichere Rückgabe nur bei Bedarf separat aktivieren.
8. **Firma & Rechtliches**: Impressum und Datenschutz fachlich/rechtlich prüfen; unter Einstellungen die Aufbewahrung festlegen. Empfänger und Aufbewahrung müssen zum tatsächlichen Betrieb passen.

Für KI-Designs öffne das **Frontend-Studio**: Firmendaten → Prompt und Referenzpaket → Design importieren → prüfen → veröffentlichen. Direkt importierbare Pakete steuern den bestehenden Renderer; freie React-Quelltexte aus dem vollständigen Referenzprojekt benötigen Einbau, Build und Tests. Details: [Frontend-Studio](docs/FRONTEND-STUDIO.md). Gespeicherte Konfigurationen können unter **Versionen** verglichen und als Entwurf wiederhergestellt werden.

**Export & Livegang** erzeugt das vollständige neue Projekt mit veröffentlichtem Stand, gespeichertem Entwurf, allen Immobilien und zugeordneten Medien. Der Erststart übernimmt diese Daten einmalig in die frische Instanz. Nutzer, echte Anfragen, ausgefüllte Selbstauskünfte und Geheimnisse werden nicht exportiert; Kontakte werden am Ziel zunächst im Admin gespeichert. Vollständige Betriebsumzüge bleiben Aufgabe des verschlüsselten Backups.

Mitarbeiter können Immobilien, Anfragen und private Unterlagen verwalten, aber keine Integrationseinstellungen, Benutzer oder Sicherheits-/Websitekonfiguration ändern. Benutzer werden unter **Einstellungen** angelegt.

## SMTP

In **Integrationen → E-Mail / SMTP** Host, Port, Verschlüsselung, Anmeldung, verifizierte Firmen-Absenderadresse und Empfänger hinterlegen. Üblich sind STARTTLS/587 oder TLS/465. TLS-Zertifikate werden geprüft. Unverschlüsseltes SMTP ist standardmäßig verboten; `ALLOW_INSECURE_SMTP=1` ist ausschließlich für lokale Testserver vorgesehen.

Interessentenadressen werden als **Reply-To**, nie als Firmen-Absender verwendet. Die Absenderfreigabe muss beim eigenen Mailanbieter erfolgen. „Test-E-Mail senden“ führt einen wirklichen SMTP-Versand durch; Erfolg bedeutet Annahme durch den SMTP-Server, nicht nachgewiesenen Postfacheingang. Eine optionale Eingangsbestätigung wird als eigenständiger Outbox-Auftrag verarbeitet. IMAP ist nicht erforderlich und nicht implementiert.

Geheimnisse werden mit Fernet verschlüsselt gespeichert. Das Admin-API gibt Passwörter und Bot-Tokens nicht zurück. Ein leeres Geheimnisfeld behält den gespeicherten Wert. Konfiguration des Zielkanals aktivieren und in jedem gewünschten Formular auswählen; ein bloß gespeicherter SMTP-Host aktiviert keinen Versand.

## Telegram

1. Über den offiziellen **@BotFather** einen Bot erstellen.
2. Mit dem Firmenaccount den Bot öffnen und `/start` senden. Für Gruppen: Bot der Firmengruppe hinzufügen und passende Rechte erteilen.
3. Die Chat-ID über die offizielle Bot API ermitteln. Ein Bot kann keinen beliebigen Account ohne vorherige Interaktion anschreiben.
4. In **Integrationen → Telegram** Bot-Token und Chat-ID speichern, Nachrichtentypen wählen, Testnachricht senden.
5. Telegram-Modul und Ziele je Formular aktivieren.

Standardmäßig gehen nur Anfrageart und Objektbezug an Telegram. Kontaktdaten/Nachricht sind separat einschaltbar. PDFs werden niemals an Telegram weitergeleitet. Die Produktionsadresse ist fest `https://api.telegram.org`; `TELEGRAM_API_BASE` ist nur ein serverseitiger Test-Override und wird nicht im öffentlichen Frontend angeboten.

## Zuverlässigkeit und Aufbewahrung

- Formularannahme und Outbox-Aufträge werden in **einer Datenbanktransaktion** gespeichert. HTTP 202 bedeutet „angenommen“, nicht „extern zugestellt“.
- Eine Idempotenzkennung verhindert für 24 Stunden eine versehentliche doppelte Annahme desselben Requests; abweichende Nutzdaten mit gleicher Kennung werden abgewiesen.
- Maximal vier automatische Versuche. Nach Fehlern wird mit wachsender Verzögerung wiederholt; danach bleibt der Fehler zur manuellen Bearbeitung sichtbar.
- Ein Worker arbeitet die Outbox ab. PostgreSQL verwendet Zeilensperren (`FOR UPDATE SKIP LOCKED`). Lokal SQLite nur mit einer API-Instanz und einem Worker betreiben.
- Ein SMTP-/Telegram-Timeout nach tatsächlicher Annahme kann bei Wiederholung zu einer doppelten Zustellung führen: die externen Protokolle bieten hier keine Exactly-once-Garantie.
- `store=false`: technische Anfrage und ihre Jobs maximal 24 Stunden, keine Anzeige als dauerhafter Interessent. Noch ausstehende Zustellungen werden nach Ablauf ebenfalls gelöscht; Zustellfehler rechtzeitig bearbeiten.
- Gespeicherte Anfragen, zugehörige private Rückgaben und Ereignisse werden nach der konfigurierten Frist bereinigt. Der laufende Worker prüft minütlich. Ohne laufenden Worker findet keine automatische Bereinigung statt.
- Deaktivierter Zustellkanal sperrt auch wartende Jobs. Nach erneuter Aktivierung können fehlgeschlagene Jobs manuell wiederaufgenommen werden.

## Dokumente und Energieangaben

Uploads: maximal 10 MB, Rasterbilder JPEG/PNG/WebP werden dekodiert, begrenzt und zu WebP optimiert; SVG/HTML werden nicht akzeptiert. PDFs werden auf Header und Abschluss geprüft, nur als Attachment mit Sandbox-Header ausgeliefert. Private Dokumente sind auch bei bekannter Datei-ID ohne Sitzung nicht abrufbar. Öffentliche Bilder sind nur bei veröffentlichten/reservierten Objekten oder aktiv referenzierten Designmedien verfügbar. Das aktuelle Vorlagen-PDF ist nur bei aktivem Modul öffentlich; ersetzte Versionen verlieren ihren öffentlichen Link.

Private PDF-Rückgabe benötigt die Kennung einer bestehenden Anfrage, einen persönlichen Rückgabecode, die passende E-Mail und Zustimmung. Diese Zuordnung bestätigt keine Identität und gibt keinen Zugriff auf vorhandene Unterlagen. Es wird kein automatischer Bonitäts- oder Besichtigungsprozess unterstellt.

Unbekannte Energiewerte sind in Entwürfen erlaubt. Veröffentlichung verlangt entweder vollständige Energieangaben oder eine begründete Ausnahme. Die Software kann keine rechtliche Zulässigkeit einer behaupteten Ausnahme garantieren. Warmmiete = Kaltmiete + Nebenkosten + Heizkosten nur dann, wenn diese nicht bereits in Nebenkosten enthalten sind. Parkplatz/Möblierung erscheinen zusätzlich und werden nicht heimlich in die Warmmiete eingerechnet.

## Entwicklung und Tests

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
npm --prefix frontend run typecheck
npm --prefix frontend run build
# Einmalig, falls Chromium nicht vorhanden:
cd frontend && npx playwright install chromium && cd ..
npm --prefix frontend run test:e2e
# Alternativ vorhandenes Chromium:
CHROMIUM_PATH=/usr/bin/chromium npm --prefix frontend run test:e2e
```

Die Python-Suite benutzt eine separate temporäre Datenbank. Für PostgreSQL `TEST_DATABASE_URL` auf eine **dedizierte Testdatenbank** setzen; diese wird bei jedem Test geleert. Die Browser-Suite startet getrennte Prozesse auf 3001/8001 mit `.local/e2e`; synthetische Objekte werden dort ausdrücklich als Tests markiert. Tests verwenden lokale SMTP-/HTTP-Testdienste, keine echten Empfänger.

Details: [Testnachweis](docs/VALIDATION.md), [Architektur](docs/ARCHITECTURE.md), [Templates / vorhandenes Frontend](docs/TEMPLATES.md), [Betrieb und Wiederherstellung](docs/OPERATIONS.md), [Umsetzungsstand](docs/STATUS.md).

## Bewusste Grenzen

Lokale Dateiablage ist enthalten; S3, Online-HTML-/React-Codeimport, Drag-and-drop-Seiteneditor, automatische Immobilienportal-Synchronisation, digitale Bonitätsprüfung und kontaktlose Besichtigung sind nicht implementiert. Fremde Frontends benötigen einen geprüften Adapter. Beispieltexte im Impressum/Datenschutz sind ausdrücklich **nicht veröffentlichungsfertig**. Ein öffentlicher Produktivbetrieb ist nicht eingerichtet. Das kundeneigene PDF ist inzwischen bytegleich geprüft und Telegram live in der gewünschten Gruppe bestätigt. Externe SMTP-Zustellung bleibt wegen der abgelehnten Cloud-Verbindungen zu Port 465/587 unbestätigt.

Der vollständige [Auftragsabgleich](docs/AUFTRAGSABGLEICH.md) dokumentiert Ergänzungen, Nachweise und offene externe Voraussetzungen. Unter **Mein Konto** lassen sich Passwörter ändern; Administratoren können Konten sperren, Rollen ändern, Passwörter zurücksetzen und Benutzer löschen. Bestehende Sitzungen werden widerrufen; der letzte aktive Administrator ist geschützt.
