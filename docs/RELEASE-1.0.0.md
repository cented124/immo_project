# Raumwerk 1.0.0 – Ergebnisse der Freigabeprüfung

Stand: 28.10.2026. [Fertige Version und kurze Startanleitung](../fertige-version/README.md). Die vorherige Entwicklungsausgabe bleibt im [Branch entwicklung](https://github.com/cented124/immo_project/tree/entwicklung) samt ihren damaligen Demo-Paketen erhalten.

## Ergänzt

- **Betriebsstatus und Startprüfung** des veröffentlichten Stands: lokale/Server-Installation, Version, Medien und Frontend-Pakete, Hintergrunddienst, Zustellfehler und Speicher. Der Unterschied zwischen lokalen und live gepflegten Inseraten wird direkt erklärt.
- **Vollständige lokale Sicherung und Wiederherstellung:** Dateiprüfsummen, Prüfung von Datenbank, Schlüssel und Paketdateien, private Zwischenablage und zusätzlicher Sicherungsstand vor dem Austausch. Auch ein beschädigter bisheriger Datenbestand wird unverändert aufgehoben. Ältere DATEN-only-ZIPs bleiben nach Prüfung lesbar.
- Wiederherstellung beendet alte Sitzungen und pausiert wartende Zustellungen. Ein alter Warteschlangenstand wird nicht automatisch erneut versendet. Die Server-Restoreanleitung enthält dieselbe Nachbehandlung.
- **Passwortwiederherstellung** vorhandener Administratoren mit Betriebssystemzugriff sowie Abmelden anderer eigener Sitzungen unter „Mein Konto“.
- **Sitemap, robots.txt und Exposé-Metadaten:** veröffentlichte/reservierte Angebote werden dynamisch aufgenommen, zurückgezogene Angebote entfernt. Lokale Installationen sperren Crawler.
- Aktualisierte Backend-Bibliotheken; Testabhängigkeiten werden separat installiert.

## Bereinigt und behalten

Die Hauptanleitung erklärt den regulären Start. Historische Cloud-Einrichtung und Entwicklerdetails liegen getrennt in `docs/ENTWICKLUNG.md`. Alte Gesamt-Demos sind aus den aktuellen Downloads entfernt und über die Entwicklungsversion weiterhin verfügbar. Der einfache vollständige ZIP-Import steht im Studio; die ältere JSON-Maske ist unter „Erweitert“ erhalten.

Die öffentliche interaktive API-Dokumentation ist standardmäßig ausgeschaltet und kann von Entwicklern mit `API_DOCS=1` aktiviert werden. Referenzexport, Quellcode, Tests, Diagnose, Reparatur und gezielte Verbindungstests bleiben erhalten, weil sie bei eigenen Frontends und im Betrieb nützlich sind. Automatische Tests und Simulationen verwenden ausschließlich synthetische Daten und Testdienste.

## Testnachweis

| Prüfung | Ergebnis |
| --- | --- |
| Backend mit SQLite | **58 bestanden** |
| Backend mit eigenständiger PostgreSQL-Testdatenbank | **55 bestanden**, 3 ausschließlich native SQLite-Tests ausgelassen |
| Browser: Desktop und Mobilgerät | **20 bestanden** |
| TypeScript und Next.js-Produktionsbuild | bestanden |
| npm-Audit der Frontend-Produktionsabhängigkeiten | 0 bekannte Meldungen |
| pip-audit der Backend-Produktionsabhängigkeiten | 0 bekannte Meldungen |
| Abgleich aller festgelegten Windows-Backendpakete | 0 bekannte Meldungen |
| Echtes Windows, PowerShell 5.1, eingebettetes Python, Node und Edge | bestanden |
| Fertiges Windows-Paket an anderem Pfad, ursprünglicher Pfad unzugänglich, externer Proxy blockiert | vollständiger Ablauf erneut offline bestanden |

Der [Windows-/Offline-Nachweis](https://github.com/cented124/immo_project/actions/runs/40785718730) und der [Linux-/Browsernachweis](https://github.com/cented124/immo_project/actions/runs/40785718772) gehören zum geprüften Kandidaten. Der abschließende Hauptzweig baut und prüft das ausgelieferte Paket nochmals; dessen Lauf ist im [Release v1.0.0](https://github.com/cented124/immo_project/releases/tag/v1.0.0) verlinkt. [Sicherheitsabgleich](release-1.0.0/abhaengigkeiten.json).

Der erste Windows-Kandidat fand eine tatsächlich offene SQLite-Verbindung, die den Dateiaustausch beim Restore blockierte. Die Verbindung wird jetzt ausdrücklich geschlossen; der gesamte Windows- und Offlineablauf wurde danach erfolgreich wiederholt. Zusätzlich sind beschädigte Archive, fehlende Schlüssel/Medien, Pfadmanipulationen und ein fehlgeschlagener Austausch mit Rücksetzung geprüft. Eine Warnung aus dem HTTP-Testadapter betrifft dessen künftigen Bibliothekswechsel; die Prüfungen bestehen.

## Simulation 1: Serverinstallation und Interessentin

Eine neue Musterfirma **Lindenhafen Immobilien GmbH** wurde in einer getrennten Installation mit Next.js-Produktionsbuild, FastAPI, PostgreSQL und Caddy/HTTPS eingerichtet. Das vollständige Westminster-Frontend wurde über die Oberfläche importiert und veröffentlicht. Die HTTPS-Zertifikatskette wurde gegen die eigene Test-CA geprüft; der Browser verwendete deren gepinnten Schlüssel.

Der Betreiber legte eine ausgedachte Wohnung **direkt im Server-Admin** über alle Schritte des Immobilienassistenten an und veröffentlichte sie. Eine getrennte mobile Besuchersitzung sah das Exposé. Archivieren lieferte öffentlich 404; nach erneutem Veröffentlichen war es wieder erreichbar. Sitemap, robots.txt und Exposé-Titel wurden dabei ebenfalls geprüft.

Die Interessentin **Mara Testkundin** stellte eine Objektanfrage. Die Outbox stellte genau eine synthetische Telegram-Nachricht an einen isolierten Testdienst zu. Der Betreiber sah die Anfrage im Admin, ergänzte eine interne Notiz und setzte den Status auf „In Bearbeitung“. Die technische Startprüfung war erfolgreich. Anschließend wurde ein PostgreSQL-Dump in eine zweite Datenbank zurückgespielt und der Bestand verglichen; alte Sitzungen wurden dort widerrufen.

[Maschinenlesbares Ergebnis](release-1.0.0/ergebnis.json) · [Mobiles Exposé](release-1.0.0/besucher-mobil.png) · [Bearbeitete Anfrage](release-1.0.0/anfrage-bearbeitet.png) · [Betriebsstatus](release-1.0.0/betriebsstatus.png)

## Simulation 2: Windows-Baukasten, Sicherung und Wiederherstellung

Auf einem frischen Windows-Runner wurden Ersteinrichtung, Anmeldung, Firmenkonfiguration, Bild-Upload, Inserat und unabhängige Kundenanfrage ausgeführt. Der Ablauf prüfte auch doppelte Starts, einen belegten Port ohne Beenden des fremden Dienstes, zwölf gleichzeitige Anfragen nach Neustart, private Zugriffsgrenzen, erhaltene verschlüsselte Integrationseinstellungen und vollständigen Projektexport mit Import in eine neue Datenbank.

Ein vollständiges Frontend-ZIP wurde über das Studio importiert, privat angesehen, veröffentlicht und von einem weiteren Kunden für eine Objektanfrage genutzt. Danach: vollständige Sicherung erstellen, eine Anfrage absichtlich löschen, Sicherung wiederherstellen und den wieder vorhandenen Datensatz, das eigene Frontend sowie den Integrationsschlüssel prüfen. Alte Sitzungen waren ungültig. Die lokale Administrator-Passwortwiederherstellung wurde ausgeführt und die erneute Anmeldung mit dem neuen Passwort bestätigt.

Aus dieser getesteten Installation wurde ein Paket ohne Daten und Konten gebaut. Es wurde an einen anderen Pfad entpackt, der ursprüngliche Pfad unzugänglich gemacht und der gesamte Ablauf mit blockiertem externen Proxy nochmals ausgeführt. [Windows-Ergebnis](release-1.0.0/windows.json).

## Betriebsgrenzen

Eine Firma und eine Website je Installation. Lokaler Windows-Baukasten und VPS nutzen getrennte Datenbanken; neue Live-Inserate werden direkt im Server-Admin gepflegt. Ein Projektexport ist keine laufende Synchronisierung und keine Betriebssicherung.

Die Server-Simulation war ein isoliertes lokales HTTPS-Deployment, kein öffentlich bereitgestellter VPS. In dieser Freigabeprüfung wurden **keine echten E-Mails oder Telegram-Nachrichten an Personen versendet**. Domain/DNS, öffentliches Hosting, rechtlich geprüfte Inhalte und reale Integrationsziele sind am Einsatzort einzurichten und zu prüfen. Windows wurde auf `windows-latest` mit Edge getestet; dies ersetzt keine Prüfung jeder Windows-10/11-Firmenrichtlinie oder Hardware. Unterstützt wird x64.

Bei importierten Sandbox-Frontends bleibt die [SEO-Einschränkung](FRONTEND-PACKAGES.md) bestehen. Sicherungen enthalten private Daten; lokale ZIP-Sicherungen sind nicht passwortverschlüsselt. Es wurden keine automatischen Portal-Schnittstellen, Mehrmandantenverwaltung, lokale/Server-Synchronisierung oder MFA ergänzt. Keine Zusage absoluter Fehlerfreiheit oder Schutz vor bisher unbekannten Schwachstellen.
