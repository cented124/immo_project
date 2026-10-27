# Architektur und Datenvertrag

## Verantwortlichkeiten

Next.js App Router rendert das öffentliche Grundgerüst serverseitig, ergänzt interaktive Suche/Formulare und liefert den Adminbereich. Same-origin-Rewrites leiten `/api/*` an FastAPI weiter. FastAPI ist alleinige Instanz für Rechte, Konfiguration, Modulstatus, Veröffentlichung, Datei-Freigabe und Zustellung. Direkte Datenbankzugriffe im Browser gibt es nicht.

PostgreSQL ist der vorgesehene Produktionsspeicher. SQLite erleichtert den lokalen Start und wird mit derselben Migration/Suite geprüft. Alembic `0001` erzeugt das Schema, keine automatische `create_all`-Initialisierung im Produktionsstart. Neue Felder der Konfiguration werden beim Start durch validierte Standardwerte ergänzt.

## Persistente Tabellen

| Tabelle | Zweck |
| --- | --- |
| settings | validierter Konfigurationsentwurf, veröffentlichte Config, verschlüsselte Integrationen |
| users | E-Mail, Argon2id-Passworthash, Rolle |
| sessions | SHA-256-Hash eines zufälligen Sitzungstokens, Benutzer, Ablaufzeit |
| properties | eindeutiger Slug, Veröffentlichung, validierter strukturierter Objektinhalt |
| inquiries | Objekt-Fremdschlüssel, Formulartyp, Bearbeitungsstatus, Inhalt, interner Vermerk, Speicherziel |
| submissions | 24-Stunden-Idempotenzkennung mit Inhaltsfingerprint und Annahmereferenz |
| deliveries | persistente Outbox pro Ziel, Status, Versuche, nächster Zeitpunkt, bereinigte Fehlermeldung |
| files | zufällige Datei-ID, Typ, Verwendung, Objekt-/Anfragezuordnung, Größe |
| events | Ereignistyp, begrenzter Seitenpfad, Zeitpunkt; keine IP, Cookies oder Nutzer-ID |
| audit | Akteur, Verwaltungsaktion, Zeitpunkt; keine Anfrageinhalte/Zugangsdaten |
| revisions | letzte 100 Konfigurationsstände, Bezeichnung, Akteur, Zeitpunkt; Vergleich und Wiederherstellung als Entwurf |

Objektinhalte bleiben flexibel als JSON, werden jedoch für jeden Schreibzugriff durch `PropertyData` validiert. Zustands- und Identitätsfelder liegen separat für Integrität/Fremdschlüssel vor. Künftig geänderte Verträge benötigen neue Migrationen und gegebenenfalls JSON-Datenmigrationen.

## Zustände

Objekte: `draft → published/reserved → sold/archived`; Bearbeitung/Rückzug ist jederzeit möglich. Nur `published` und `reserved` sind öffentlich. Bekannte Links zu anderen Zuständen und zugehörigen Bildern liefern 404. Private Dokumente erscheinen nie im öffentlichen Objekt-JSON. Straße/Hausnummer werden bei verborgener Adresse entfernt.

Anfragen: `new`, `processing`, `answered`, `closed`. Standardziel ist dauerhafte Adminspeicherung. Andere Ziele bilden separate Delivery-Zeilen in derselben Annahmetransaktion.

Outbox: `pending → sent` oder `retry → failed`. Ein Testversand läuft synchron und liefert nur dann Erfolg, wenn der Testserver die Nachricht annimmt. Automatische Zustellversuche laufen unabhängig von der ursprünglichen HTTP-Anfrage.

Konfiguration: `draft` bleibt privat; `publish` validiert PDF, Medien, Integrationseinstellungen und Module und ersetzt erst dann den öffentlichen Stand. Vorschau braucht eine bestehende Adminsitzung und ist kein öffentlicher Freigabelink.

Das Frontend-Studio ergänzt strukturierte Rechtstexte/Firmendaten, ein privates KI-Briefing und das versionierte Layoutschema. Direkt importierte Themes werden in den Entwurf übernommen; ausführbarer Fremdcode wird nicht importiert. Das KI-Paket enthält die vollständigen Quellen und tatsächlichen öffentlichen OpenAPI-Definitionen für frei entwickelte Anpassungen samt Build-/Testvertrag.

Projektexport und Betriebsbackup sind getrennt: Der Export enthält Programmcode, beide Konfigurationsstände, Immobilien und zugeordnete Medien mit SHA-256-Prüfsummen. Seeddateien werden im Zielimage mit App-Eigentümer nach `/seed` kopiert und nach Migration einmalig in eine frische Datenbank und `/data/files` übernommen. Ein Datenbankmarker verhindert Überschreiben beim Neustart; PostgreSQL-Sequenzen werden fortgeführt. Anfragen, Benutzer und Geheimnisse werden nicht exportiert; externe Formularziele werden beim Export auf Adminspeicherung umgestellt. Das Backup sichert dagegen den vollständigen laufenden Betrieb einschließlich Schlüssel.

## Analytics: Definitionen

- **Seitenaufruf**: ein `pageview`-Ereignis bei Seitenaufruf im Browser.
- **Exposéaufruf**: ein erfolgreich geladenes öffentliches Exposé erzeugt zusätzlich `property_view`.
- **Anfrageklick**: Klick auf „Interesse an dieser Immobilie“ erzeugt `inquiry_click`.
- **Angenommenes Formular**: serverseitiges `submission` erst nach erfolgreicher Anfrageannahme, nie bei Validierungsfehler oder Idempotenz-Replay.
- Dashboard zählt Ereignisse innerhalb der laufenden Aufbewahrungsfrist seit Erfassungsbeginn, keine eindeutigen Besucher. Anfrage-Tageswerte: gespeicherte Anfragen der letzten 30 Tage nach UTC-Kalendertag. Anfragezahlen je Objekt/Formular: noch gespeicherte Datensätze.

Bei deaktiviertem Analytics-Modul stehen Ereigniszahlen auf `null`/„—“, nicht auf einer erfundenen Null. Clientereignisse sind durch Bots/Reloads beeinflussbar und keine abrechnungsfesten Metriken. Es gibt kein Tracking über Websites hinweg und keine Verknüpfung zu einem Besucherprofil.

## Sicherheitsmodell

Argon2id; zufällige 12-Stunden-Sitzung in HttpOnly/SameSite=Strict-Cookie, serverseitig nur Tokenhash. Secure-Cookie im HTTPS-Betrieb. Schreibende Adminrequests verlangen einen besonderen Header; Origin wird gegen die konfigurierte öffentliche Origin geprüft. Keine Cross-origin-CORS-Freigabe. React escaped Textinhalte; kein Rich-HTML, `dangerouslySetInnerHTML`, beliebiger Scriptimport oder SQL-Stringbau.

Kennungen von Dateien werden ausschließlich zufällig erzeugt. Originalnamen beeinflussen keine Dateipfade. Öffentliches File-API prüft Modul, Verwendung und aktuelle Referenz/Veröffentlichung; privates File-API prüft Sitzung/Rolle. PDFs werden als Attachment mit Sandbox ausgeliefert; Bilder serverseitig dekodiert und neu kodiert. Größen-/Pixelprüfungen begrenzen Ressourcenverbrauch.

Integrationseinstellungen sind Fernet-verschlüsselt; Schlüssel außerhalb der Datenbank. Niemand erhält Passwörter/Bot-Tokens per GET zurück. Fehlermeldungen sind bereinigt; Uvicorn-Accesslogs sind aus, insbesondere keine Telegram-URLs oder Formularinhalte. Administratoren dürfen bewusst externe SMTP-Ziele konfigurieren und besitzen daher entsprechende Netzwerkrechte.

Grenzen: keine MFA/SSO, kein Antivirus-/CDR-Scanner, keine automatische juristische Energie-/Datenschutzprüfung, keine verteilten Ratelimits. Deshalb sind TLS, vertrauenswürdiger Reverse-Proxy, getrennte Backups, begrenzte Netzfreigaben und betriebliche Überwachung notwendig. Siehe Betriebsdokumentation; diese Grenzen sind keine pauschale Rechtskonformitätszusage.
