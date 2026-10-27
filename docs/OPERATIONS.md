# Betrieb, Backups und Wiederherstellung

## Vor öffentlichem Betrieb

- Eigene Unternehmensangaben statt Musteridentität; eigene rechtlich geprüfte Texte und Kontaktmöglichkeiten veröffentlichen.
- Eigenen Administrator erstellen, Berechtigungen im Team prüfen. Nur vertrauenswürdige Personen erhalten Administratorrechte.
- Gültiges TLS am Reverse-Proxy, `PUBLIC_ORIGIN` exakt konfigurieren, `COOKIE_SECURE=1`. Backend und Datenbank im internen Netz belassen.
- Eigene SMTP-/Telegram-Ziele testen. SPF/DKIM/DMARC und Absenderfreigabe beim Mailanbieter einrichten. Ein Testserver beweist keine spätere Zustellung über einen anderen Anbieter.
- Eigene PDF-Vorlage hochladen, Rückgabe nur bei Bedarf einschalten. Es gibt keine Pflicht zur Selbstauskunft bei Erstkontakt.
- Datenaufbewahrung festlegen, Worker laufen lassen, Zustellfehler beobachten. Technische 24-Stunden-Zustelldaten rechtzeitig bearbeiten.
- Backup erzeugen und eine Wiederherstellung in isolierter Umgebung üben.

## Verschlüsseltes Compose-Backup

Voraussetzungen: GnuPG auf dem Host; verschlüsseltes externes Ziel. Der bereitgestellte Ablauf hält Web/API für einen konsistenten Snapshot kurz an. Das Script startet die Dienste auch nach einem Fehler wieder; keine Sicherung bei unkontrollierten Änderungen parallel ausführen.

```bash
umask 077
bash scripts/backup.sh /sicherer/externer/pfad/raumwerk-backup.tar.gpg
```

GnuPG fragt die Passphrase interaktiv über Pinentry ab. Die Passphrase gehört in einen getrennten Passwortsafe, nicht ins Repository oder Backupverzeichnis. Gesichert werden PostgreSQL-Dump, `/data` und `.env` (darin der zur Entschlüsselung benötigte Fernet-Schlüssel). Das Archiv enthält deshalb besonders schützenswerte Daten. Nur verschlüsselt extern ablegen, Zugriff einschränken, Löschfristen und regelmäßige Restore-Tests festlegen. Backup-Script ist eine Betriebsanleitung; eine externe geschützte Ablage wird nicht automatisch bereitgestellt.

Für einen automatisierten Backupjob kann `BACKUP_PASSPHRASE_FILE` auf eine ausschließlich für den Betreiber lesbare Datei (Modus 0600 oder Secret-Mount) zeigen. Der Inhalt wird nicht als Kommandozeilenargument oder Log ausgegeben. Dies ersetzt keine geschützte externe Ablage.

## Restore in eine isolierte Compose-Installation

Leere isolierte Zielumgebung verwenden. Keinen existierenden Produktivdatenbestand überschreiben. Vorhandene Zielvolumes zuerst separat sichern. Dieselbe Anwendungsversion wie im Backup verwenden und erst nach erfolgreichem Restore migrieren.

```bash
umask 077
mkdir -p /sicherer/restore
gpg --decrypt /sicherer/backup.tar.gpg | tar -xf - -C /sicherer/restore
# Im frischen Zielcheckout:
cp /sicherer/restore/environment.env .env
chmod 600 .env
docker compose up -d db
docker compose exec -T db pg_restore -U raumwerk -d raumwerk --clean --if-exists < /sicherer/restore/database.dump
# API-Container und sein Datenvolume erstellen, aber noch nicht starten:
docker compose create api
docker compose cp /sicherer/restore/files/. api:/data
# docker cp kann Eigentümer verändern; App läuft bewusst ohne root:
docker compose run --rm --no-deps --user 0 --entrypoint sh api -c 'chown -R 10001:10001 /data'
docker compose up -d api web
```

Die mitgesicherte Origin muss für einen Restore auf anderer Domain angepasst werden; sichere Cookies beibehalten. Das ursprüngliche `ENCRYPTION_KEY` nicht ersetzen. Nach Restore: Healthcheck, Login, privater PDF-Zugriff, veröffentlichte Immobilien und Testzustellungen prüfen. Unverschlüsselte temporäre Restore-Dateien anschließend auf geschütztem Datenträger sicher entfernen. SSD/Cloud-Dateisysteme garantieren kein physisches Überschreiben durch `rm`.

## Lokaler SQLite-Bestand

`scripts/dev.sh` beenden und **das gesamte** `.local/data` inklusive Schlüssel sichern. Eine laufende SQLite-Datei nicht einfach unkoordiniert kopieren. Für große/produktive Nutzung PostgreSQL einsetzen. SQLite- und PostgreSQL-Datenbanken werden nicht durch Ändern einer Umgebungsvariable ineinander konvertiert.

## Überwachung und Grenzen

Healthcheck `/api/health` prüft Datenbankzugriff. Im Adminbereich Zustellfehler beobachten; maximal vier automatische Versuche, manuell wiederaufnehmbar. Ein SMTP-Timeout kann trotz späterem Fehler bereits eine Nachricht zugestellt haben; Wiederholung kann dann ein Duplikat erzeugen.

Aktuelle Ratelimits sind pro Backendprozess im Speicher. In der mitgelieferten Produktionskonfiguration überschreibt Caddy `X-Real-IP` mit der echten Verbindungsadresse; nur dort aktiviert die interne API `TRUST_PROXY_HEADERS=1`. API und Next dürfen dafür nicht direkt öffentlich erreichbar sein. Die Standardkonfiguration ignoriert diese Header; dort können Proxy-Anfragen ein gemeinsames Limit haben. Bei eigenen Proxies diese Vertrauensgrenze bewusst konfigurieren. Loginlimits zählen Fehlversuche je IP/Adresse; erfolgreiche Anmeldungen setzen diesen Zähler zurück. Ein zusätzlicher IP-Zähler begrenzt die Gesamtlast. Für stark frequentierten Betrieb vorgeschaltete Ratelimits und Kapazitäten prüfen. Mehrere APIinstanzen erfordern ein gemeinsames Limiter-Konzept. Outbox unter PostgreSQL ist durch Datenbankzeilensperren geschützt; SQLite nur mit einer Instanz betreiben.

Abgelaufene Sitzungen werden im laufenden Bereinigungsjob gelöscht. Eigene Passwörter lassen sich unter „Mein Konto“ ändern. Administratoren verwalten Rollen, Kontosperren, Passwortzurücksetzungen und Benutzerlöschung unter Einstellungen; Änderungen beenden bestehende Sitzungen. Kein offener Passwortreset und keine Selbstregistrierung. Der erste Admin wird per interaktiver CLI erstellt; der Windows-Starter ruft sie beim ersten Start auf. Fehlende MFA, Antivirusprüfung und S3-Anbindung sind dokumentierte Erweiterungspunkte.

## Migrationen und Updates

Vor jedem Update konsistent sichern. Abhängigkeiten aus Lockfile/Requirements installieren, `alembic -c backend/alembic.ini upgrade head` ausführen, Build/Tests und Smokechecks durchführen. Integrationsschlüssel unverändert erhalten. Keine Datenbank mittels `create_all` oder Schema-Drops „reparieren“.
