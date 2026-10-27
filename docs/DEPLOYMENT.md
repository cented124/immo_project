# Einfacher Livegang auf einem VPS

Ein VPS ist dein Hosting. Du brauchst zusätzlich eine Domain; ein Shared-Hosting-Paket ist nicht erforderlich. Empfohlen: Ubuntu 24.04 LTS, mindestens 2 CPU, 4 GB RAM, genügend Speicher für Bilder und Backups. Für die erste Einrichtung brauchst du SSH-Zugang und das Recht, Docker zu verwenden.

## 1. Fertiges Projekt herunterladen

Im Baukasten Änderungen speichern, die gewünschte Version veröffentlichen und **Export & Livegang** öffnen. Optional deine Domain eintragen und den Plan erzeugen. **Fertiges Projekt exportieren** lädt `Raumwerk-Projekt.zip` herunter.

Enthalten: kompletter Programmcode, veröffentlichte Website, gespeicherter Entwurf, alle Immobilien einschließlich unveröffentlichter Objekte, zugeordnete Bilder und interne Objekt-PDFs, Firmenmedien und die leere Selbstauskunft-Vorlage. Das Archiv vertraulich aufbewahren.

Nicht enthalten: Benutzer/Passwörter, Sitzungsschlüssel, SMTP-/Telegram-Zugangsdaten, echte Anfragen, ausgefüllte Selbstauskünfte, Outbox und Statistik. Am Ziel werden neue Geheimnisse erzeugt und die Integrationen neu eingerichtet. Bis dahin speichern alle Formulare im dortigen Adminbereich. Das ist ein Projektexport für eine neue Instanz. Einen bestehenden Betrieb samt Anfragen und Konten verschiebst du über das verschlüsselte Backup, siehe [OPERATIONS.md](OPERATIONS.md).

## 2. Domain zum Server verbinden

Beim Domainanbieter einen **A-Eintrag** für die gewünschte Domain auf die öffentliche IPv4-Adresse deines VPS setzen. Einen **AAAA-Eintrag** nur setzen, wenn der VPS über IPv6 tatsächlich erreichbar ist. `www` ist eine eigene Domain und wird nicht automatisch mitbestellt oder mitkonfiguriert; zuerst die gewählte Hauptdomain verwenden.

TCP **80** und **443** beim VPS-Anbieter und in der Server-Firewall freigeben. Port 22 nur für den eigenen SSH-Zugang öffnen. PostgreSQL und die interne API haben keine öffentlichen Ports. Docker veröffentlicht Ports teilweise außerhalb von UFW-Regeln; die externe Provider-Firewall ist deshalb maßgeblich.

DNS-Änderungen können Zeit benötigen. Caddy benötigt passende DNS-Auflösung und Erreichbarkeit auf Port 80/443, um ein öffentlich gültiges HTTPS-Zertifikat zu beschaffen. Bereits auf diesen Ports laufende Webserver müssen zuerst auf eine passende gemeinsame Reverse-Proxy-Konfiguration abgestimmt werden.

## 3. Docker auf Ubuntu installieren

Wenn der Anbieter ein aktuelles Docker-Image anbietet, dieses wählen. Sonst die offizielle Anleitung verwenden: <https://docs.docker.com/engine/install/ubuntu/>. Zusätzlich zu Docker Engine werden das **Compose-Plugin**, Python 3 und unzip benötigt. Keine veraltete separate `docker-compose`-Version verwenden.

```bash
sudo apt update
sudo apt install -y python3 unzip
docker --version
docker compose version
```

Docker-Befehle mit einem dafür berechtigten Konto ausführen. Docker-Rechte entsprechen weitgehenden Serverrechten. Keine Passwörter an den Chat oder in GitHub schicken.

## 4. ZIP hochladen und starten

Unter Windows kannst du beispielsweise WinSCP verwenden: mit der VPS-IP, deinem SSH-Benutzernamen und deinem Schlüssel anmelden. ZIP in ein eigenes Projektverzeichnis kopieren. Anschließend per SSH dieses Verzeichnis öffnen:

```bash
unzip Raumwerk-Projekt.zip
cd Raumwerk
bash LIVE-STARTEN.sh
```

Das Startprogramm fragt die Domain ab, legt beim ersten Start eine `.env` mit unabhängigen Zufallsgeheimnissen an und startet Datenbank, API, Website und Caddy. Beim ersten Start werden die exportierten Inhalte aus `project/` einmalig in die frische Datenbank importiert. Danach legst du deinen Administrator mit eigener E-Mail und mindestens 12 Zeichen langem Passwort an. Beim Passwort wird während der Eingabe nichts angezeigt.

Der erste Build kann mehrere Minuten dauern. Wiederholtes `bash LIVE-STARTEN.sh` erhält `.env`, Datenbank, Dateien und Administrator. Ein Projektimport überschreibt keine vorhandenen Benutzer oder Inhalte; ein anderes Exportpaket darf nicht einfach über dieselbe Instanz gelegt werden.

## 5. Website prüfen

Öffne `https://deine-domain.de` und `https://deine-domain.de/admin`. Beide gehören zur selben Installation. Der Adminzugang ist durch Anmeldung geschützt. Das Startprogramm kann ohne einen funktionierenden Domain-/DNS-Zugang keine öffentliche Erreichbarkeit garantieren.

```bash
python3 scripts/check-live.py --domain deine-domain.de
docker compose -f compose.yaml -f compose.production.yaml ps
docker compose -f compose.yaml -f compose.production.yaml logs --tail 50 caddy
```

Der Prüfhelfer ruft Website, Admin und API ausschließlich lesend über HTTPS mit regulärer Zertifikatsprüfung ab. Er verschickt keine E-Mail oder Telegram-Nachricht. Erst nach erfolgreicher Prüfung ist die Erreichbarkeit bestätigt.

## 6. Betrieb fertig einrichten

1. Anmelden, Firma und Rechtstexte prüfen.
2. SMTP und/oder Telegram bei Bedarf neu eintragen. Empfänger kontrollieren.
3. Module und Formularziele einstellen und veröffentlichen.
4. Einen bewussten eigenen Test senden; die tatsächliche Zustellung im Admin prüfen.
5. Verschlüsselte Backups nach [OPERATIONS.md](OPERATIONS.md) auf einem anderen System ablegen. Wiederherstellung regelmäßig prüfen.

Bei den in diesem Chat verwendeten E-Mail-Testdaten bleiben die ursprünglichen Versandgrenzen bestehen. Automatische Einrichtung und Softwaretests versenden keine echten Nachrichten.

## Bestehende lokale Installation auf HTTPS umstellen

Das Startprogramm verändert eine vorhandene `.env` nicht. Vorhandene Daten und Geheimnisse behalten und diese drei Werte bewusst anpassen:

```dotenv
DOMAIN=deine-domain.de
PUBLIC_ORIGIN=https://deine-domain.de
COOKIE_SECURE=1
```

Dann `bash LIVE-STARTEN.sh` starten. Nicht `docker compose down -v` ausführen: `-v` würde die benannten Datenvolumes löschen. Eine Domainänderung erfordert passende DNS-Einträge und einen Neustart der Produktionskonfiguration.
