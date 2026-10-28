# Raumwerk 1.0.0

Der firmenneutrale Baukasten für eine Immobilienwebsite mit eigenem Adminbereich. Firma und Rechtstexte eintragen, Frontend gestalten oder als fertiges ZIP importieren, Immobilien veröffentlichen und Anfragen bearbeiten.

## Fertige Version herunterladen

**[Fertige Version – Downloads und kurze Anleitung](fertige-version/README.md)**

Für Windows 10/11 x64 gibt es ein vollständiges Paket **ohne Docker**. ZIP entpacken und `STARTEN.cmd` öffnen. Python, Node.js und das gebaute Frontend sind im fertigen Windows-Paket enthalten. Die erste Administratoranlage erfolgt im Browser. Es gibt kein Standardpasswort.

Die frühere Entwicklungsversion bleibt separat unter **[Branch entwicklung](https://github.com/cented124/immo_project/tree/entwicklung)** und als [Entwicklungs-ZIP](https://github.com/cented124/immo_project/archive/refs/heads/entwicklung.zip) verfügbar. Die feste Ausgabe 1.0.0 liegt im eigenen Ordner `fertige-version/1.0.0` und als GitHub Release vor.

## Im Alltag

1. **Firma & Rechtliches:** Namen, Kontakt, Registerdaten und geprüfte Rechtstexte eintragen.
2. **Frontend-Studio:** Design gestalten oder ein vollständiges Frontend-ZIP auswählen, Vorschau prüfen und veröffentlichen. [Importanleitung](docs/FRONTEND-IMPORT.md).
3. **Immobilien:** Objekte mit Bildern anlegen und veröffentlichen. Entwürfe und archivierte Angebote bleiben privat.
4. **Anfragen:** Neue Interessenten sehen, Notizen und Bearbeitungsstatus pflegen. SMTP und Telegram sind optionale Zustellwege mit Fehleranzeige und Wiederholungen.
5. **Einstellungen:** Betriebsstatus und Startprüfung öffnen; anschließend regelmäßig sichern.

**Lokal und Server sind getrennte Installationen.** Nach dem Livegang legst du neue Inserate direkt im Adminbereich deiner Domain an. Sie erscheinen beim nächsten Laden auf derselben Website. Dafür brauchst du keinen erneuten Export. Eine automatische Synchronisierung mit deinem Windows-Computer gibt es nicht.

## Sichern, aktualisieren und Zugang wiederherstellen

- `SICHERN.cmd`: stoppt Raumwerk und erstellt eine vollständige lokale Sicherung mit Prüfsummen.
- `WIEDERHERSTELLEN.cmd`: ZIP auswählen, Prüfung abwarten und Wiederherstellung bestätigen. Der bisherige Stand wird zusätzlich gesichert. Alte Sitzungen werden beendet und wartende Zustellungen zur manuellen Prüfung pausiert.
- `PASSWORT-ZURUECKSETZEN.cmd`: mit Zugriff auf diesen Computer das Passwort eines vorhandenen Administrators neu setzen.
- `STOPPEN.cmd`, `DIAGNOSE.cmd`, `REPARIEREN.cmd`: Anwendung beenden, Status prüfen oder Programme reparieren.

Sicherungen enthalten private Daten und den Schlüssel. Geschützt aufbewahren und auf ein anderes Laufwerk kopieren. Zum Update zuerst sichern, neue Version in einen **neuen Ordner** entpacken und den vollständigen alten Ordner `DATEN` übernehmen. [Windows-Anleitung](ANLEITUNG-WINDOWS.md).

## Auf einer eigenen Domain betreiben

**Export & Livegang** erzeugt das Projekt für eine frische VPS-Installation. [Einfache VPS-Anleitung](docs/DEPLOYMENT.md). Der lokale Windows-Baukasten bleibt ohne Docker; der bereitgestellte VPS-Weg nutzt Docker Compose, PostgreSQL und Caddy mit HTTPS.

Ein Projektexport enthält Website, Konfiguration, Immobilien und zugehörige Medien. Anfragen, Benutzer und Geheimnisse werden nicht exportiert. Integrationen und einen neuen Administrator richtest du am Server ein. Für einen vollständigen Betriebsumzug brauchst du eine Betriebssicherung, siehe [Betrieb und Wiederherstellung](docs/OPERATIONS.md).

## Enthaltene Funktionen

- Firmenprofil, Registerdaten, Rechtstexte, Module, Seiten, Navigation, Theme, Medien und Versionen.
- Responsive Standardfrontends sowie vollständiger HTML-/CSS-/JavaScript-ZIP-Import mit Bildern und Schriften; KI-Prompt und kompatibles Beispiel.
- Immobilienassistent, Bilder, Preis-/Energieangaben, Entwürfe, Veröffentlichung, Rückzug, Duplizieren, Suche und Exposés.
- Kontakt- und Objektanfragen, private PDF-Rückgabe, Rollen, Kontoverwaltung, CSV-Export und Aufbewahrung.
- Verschlüsselte Integrationseinstellungen, persistente Zustellwarteschlange und Betriebsprüfung.
- Automatische Sitemap, robots.txt und objektbezogene Seitentitel. Das SEO-Limit von Frontends im Sandbox-Iframe ist [dokumentiert](docs/FRONTEND-PACKAGES.md).
- Nativer Windows-Start, Backup/Restore und Projektexport mit VPS-Anleitung.

Eine Installation verwaltet eine Firma und eine Website. Automatische Portal-Synchronisierung, lokale/Server-Datensynchronisierung, Mehrmandantenbetrieb und MFA sind nicht enthalten. Eigene Unternehmensdaten, rechtliche Prüfung, Domain, Server und Mail-/Telegram-Zugänge bleiben Teil deiner Einrichtung.

[Testbericht und zwei Simulationen](docs/RELEASE-1.0.0.md) · [Entwicklerunterlagen und Tests](docs/ENTWICKLUNG.md) · [Technische Architektur](docs/ARCHITECTURE.md)
