# Raumwerk unter Windows – ohne Docker

Für Windows 10/11 **x64**. Du brauchst einen aktuellen Browser. Docker, WSL und eine eigene Python-/Node-Installation sind für diesen Startweg nicht erforderlich.

## 1. Das richtige ZIP herunterladen

Empfohlen: **[Fertiges Windows-Paket mit Laufzeiten](https://github.com/cented124/immo_project/releases/download/v1.0.0/Raumwerk-Windows-ohne-Docker.zip)**. Es enthält Python, Node.js, Backend-Pakete und das gebaute Frontend. Der erste lokale Start benötigt damit keine Internetverbindung. Telegram, E-Mail und externe KI-Dienste benötigen für ihre jeweilige Nutzung weiterhin Internet.

Alternative: **[Kleines Windows-Quellpaket](https://github.com/cented124/immo_project/raw/refs/heads/main/downloads/Raumwerk-Windows.zip)** oder GitHub **Code → Download ZIP**. Hier richtet der erste Start die Programme automatisch ein und lädt die Abhängigkeiten herunter; dafür wird Internet benötigt. Mehrere Minuten Wartezeit beim ersten Mal sind normal.

Bei einem privaten Repository musst du bei GitHub mit dem berechtigten Konto angemeldet sein.

## 2. Vollständig entpacken

Rechtsklick auf die ZIP-Datei → **Alle extrahieren**. Öffne den enthaltenen Ordner **Raumwerk**. Darin liegt `STARTEN.cmd`.

Verwende einen kurzen lokalen Ordner, zum Beispiel `C:\Users\DEINNAME\Raumwerk`. Starte nicht aus der ZIP-Vorschau. Ein Netzlaufwerk oder synchronisierter OneDrive-Ordner ist für eine laufende Datenbank ungeeignet. Mindestens 2 GB freien Platz für die Quellpaket-Einrichtung bereithalten; zusätzlich Speicher für eigene Bilder und Sicherungen.

## 3. STARTEN öffnen

`STARTEN.cmd` doppelklicken. Im kleinen Quellpaket werden die festgelegten offiziellen Laufzeiten heruntergeladen und ihre SHA-256-Prüfsummen kontrolliert. Es werden keine Programme systemweit installiert und keine Administratorrechte angefordert.

Danach öffnet sich der Browser. Wenn er nicht automatisch aufgeht, steht die lokale Adresse im Startfenster. Nutze genau diese Adresse; bei einem bereits belegten Port wählt das Programm automatisch einen freien. Fremde Programme werden nicht beendet.

Das Startfenster kannst du nach erfolgreichem Start schließen. Die Anwendung läuft im Hintergrund weiter. Ein erneuter Doppelklick auf STARTEN öffnet dieselbe laufende Installation.

## 4. Einmal den Administrator anlegen

Beim allerersten Start erscheint **„Dein Baukasten. Ohne Docker.“**:

1. Eigene E-Mail-Adresse eingeben. Sie dient der Anmeldung; es wird dadurch keine E-Mail gesendet.
2. Eigenes Passwort mit mindestens zwölf Zeichen eingeben und wiederholen.
3. **Administrator anlegen** anklicken.
4. Anschließend im normalen Adminbereich anmelden.

Es gibt kein Standardpasswort. Die Einrichtungsseite wird nach der ersten erfolgreichen Anlage gesperrt. Wenn der Einrichtungslink durch ein Neuladen verloren geht, STARTEN.cmd erneut öffnen.

## 5. Den Baukasten verwenden

- **Firma & Rechtliches:** Firmenname, Anschrift, Vertretung und zutreffende Registerdaten eintragen; Impressum und Datenschutz fachlich prüfen.
- **Design & Medien / Seiten & Inhalte:** Bilder, Farben, Texte, Navigation und Abschnitte einstellen.
- **Frontend-Studio:** Das KI-Referenzpaket exportieren und von der KI ein fertiges Frontend-ZIP mit Bildern und Schriften liefern lassen. ZIP auswählen, automatische Prüfung abwarten, als Entwurf übernehmen, Vorschau ansehen und veröffentlichen. [Einfache Importanleitung](docs/FRONTEND-IMPORT.md).
- **Immobilien:** Objekt zunächst als Entwurf anlegen, echte Angaben und eigene Bilder ergänzen, prüfen und veröffentlichen.
- **Dokumente / Module & Formulare:** Eigenes PDF hochladen, benötigte Module und Formularziele einstellen.
- **Anfragen / Versionen:** Anfragen bearbeiten und gespeicherte Konfigurationen vergleichen oder als Entwurf wiederherstellen.

Der [vollständige Beispieldurchlauf](docs/SIMULATION.md) zeigt diese Schritte mit einer erfundenen Firma und Wohnung.

## 6. Telegram und E-Mail bei Bedarf einrichten

Die Downloads enthalten keine Zugangsdaten. Unter **Integrationen** die eigenen Daten eintragen, speichern, danach das passende Modul und die Formularziele aktivieren und veröffentlichen. Ohne Zustelldienst landen Anfragen bereits im Adminbereich.

Ein Klick auf **Testnachricht senden** oder **Test-E-Mail senden** versendet tatsächlich eine Nachricht. Empfänger vorher kontrollieren und den Eingang am Ziel prüfen.

## 7. Stoppen, sichern, später starten

**STOPPEN.cmd** beendet diese Installation. Das kann während laufender Arbeit kurz dauern. Daten bleiben erhalten. Beim nächsten Mal genügt **STARTEN.cmd**.

**SICHERN.cmd** stoppt die Anwendung und legt eine ZIP-Sicherung unter **SICHERUNGEN** an. Sie enthält die Datenbank, Dateien und den Integrationsschlüssel. Diese Sicherung ist nicht passwortverschlüsselt; privat aufbewahren und nicht in GitHub oder im Chat hochladen. Zum Weiterarbeiten wieder STARTEN öffnen.

Alle lokalen Nutzdaten liegen in **DATEN**. Die Programme liegen getrennt unter **.runtime**. Lösche niemals DATEN, um ein Programmproblem zu beheben.

## 8. Bei Problemen

**DIAGNOSE.cmd** zeigt Status, Laufzeit und Speicherplatz. Technische Protokolle liegen unter **.runtime/logs**. Teile zur Fehlersuche den Fehlertext, keine Datenbank, Schlüssel oder Passwörter.

**REPARIEREN.cmd** stoppt die Installation, prüft/installiert die Programme neu und baut das Frontend neu. **DATEN bleibt erhalten.** Für erneute Downloads wird Internet benötigt.

Wenn Windows oder eine Firmenrichtlinie die Programmausführung blockiert, die konkrete Meldung prüfen und gegebenenfalls die zuständige IT einbeziehen. Schutzprogramme müssen für Raumwerk nicht generell ausgeschaltet werden.

## Update oder Umzug

Vor einem Update STOPPEN und SICHERN verwenden. Neue Programmdateien in einen neuen lokalen Ordner entpacken und den bisherigen Ordner **DATEN vollständig** übernehmen. Er enthält auch den Schlüssel für gespeicherte Integrationen. Anschließend STARTEN öffnen. Eine bestehende Docker-/PostgreSQL-Datenbank wird dadurch nicht automatisch in SQLite umgewandelt; dafür den bisherigen Projektexport oder den dokumentierten vollständigen Betriebsumzug verwenden.

## Die fertige Website ins Internet bringen

**Export & Livegang** erstellt ein Projektpaket mit Website, Admin, Immobilien und zugeordneten Medien. Dieses Paket lässt sich unter Windows ebenfalls mit STARTEN testen. Die hier gestartete Desktop-Version ist ausschließlich lokal erreichbar.

Für den öffentlichen Betrieb mit Domain und HTTPS bleibt die [VPS-Anleitung](docs/DEPLOYMENT.md) der vorgesehene Weg. Der optionale Docker-Start heißt unter Windows jetzt **STARTEN-DOCKER.cmd** / **STOPPEN-DOCKER.cmd**; er gehört nicht zum normalen Desktop-Start.

## Sicherung wiederherstellen

1. `WIEDERHERSTELLEN.cmd` öffnen und deine ZIP-Sicherung auswählen.
2. Raumwerk prüft die Dateien, die Datenbank, den Integrationsschlüssel und importierte Frontends.
3. Mit der angezeigten Eingabe bestätigen. Der bisherige Stand wird vor dem Austausch zusätzlich unter `SICHERUNGEN` gesichert, auch wenn seine Datenbank beschädigt ist.
4. `STARTEN.cmd` öffnen und mit den Konten/Passwörtern der Sicherung anmelden.

Alte Anmeldungen werden ungültig. Zum Zeitpunkt der Sicherung wartende Nachrichten stehen nach der Rückspielung als pausierte Fehler unter **Integrationen**. Vor einer manuellen Wiederaufnahme prüfen, ob sie bereits beim Empfänger angekommen sind. Ältere DATEN-ZIPs ohne Prüfsummenmanifest sind nach Datenbank-/Medienprüfung weiterhin unterstützt. Maximal 2 GB entpackte Sicherungsdaten und 20000 Archiveinträge.

## Passwort vergessen

`PASSWORT-ZURUECKSETZEN.cmd` öffnen. Die vorhandene Administrator-E-Mail und zweimal ein neues Passwort mit 12 bis 200 Zeichen eingeben. Passwörter werden bei der Eingabe nicht angezeigt. Das Programm stoppt Raumwerk und beendet alte Sitzungen. Anschließend `STARTEN.cmd` öffnen und neu anmelden. Zugriff auf deinen lokalen Computer und Datenordner ist dafür erforderlich.

## Lokale und öffentliche Inserate

Die obere Leiste zeigt **Lokal auf diesem Computer** oder **Server-Installation** und die Version. Nach dem VPS-Livegang neue Angebote direkt unter `https://deine-domain.de/admin` anlegen, ändern oder zurückziehen. Änderungen in einem lokalen DATEN-Ordner werden nicht automatisch zum VPS übertragen.
