# Fortsetzbarer Umsetzungsstand

Stand: 28.10.2026. Produktname des firmenneutralen Werkzeugs: **Raumwerk**. Musteridentität der öffentlichen Website: austauschbares „RAUM & WERT“. Kein Aurevia-spezifischer Datenbank-/Backendcode.

## Umgesetzt

1. Grundsystem: Next.js/FastAPI, migrationsgestützte Tabellen, lokale persistente Ablage, Argon2-Login, Sitzungen/Rollen, gemeinsame validierte Konfiguration.
2. Öffentliche Seiten und Templates: responsive Atelier-/Editorial-Stile, gemeinsame Funktionskomponenten, Konfigurationsentwurf/Vorschau/Veröffentlichung, Inhalte/Navigation/Abschnitte/SEO.
3. Immobilien: geführter Assistent, Stammdaten, Lage, Eigenschaften, Kauf-/Mietpreise, nachvollziehbare Warmmiete, Energieprüfung, Medien, Status, Duplizieren, Vorschau, Listen/Details/Filter/Pagination.
4. Anfragen: Kontakt/Bewerbung, serverseitige Objektzuordnung, konfigurierbare Ziele, Idempotenz, Ratelimits, Outbox, SMTP/Telegram, Tests, Wiederholungen, CSV, Status, Notizen und Löschung.
5. PDF: Vorlagen-Upload/Austausch, modulabhängiger Download, optionale private Rückgabe mit Anfragezuordnung; kein erfundenes Kunden-PDF.
6. Analytics/Betrieb: tatsächliche Ereignisse, Dashboard, Änderungsprotokoll, Docker Compose, Konfigurationserzeugung, Installations-/Betriebs-/Template-/Backup-Dokumentation.
7. Freigegebener GUI-Entwurf umgesetzt: Firma & Rechtliches, Frontend-Studio, KI-Prompt und komplettes Referenzprojekt, versionierter sicherer Designimport mit tatsächlich angewendeten Layoutwerten, Kontrast-/Medienprüfung, manuelle Layoutregler, Konfigurationsvergleich und Wiederherstellung.
8. Vollständiger Projektexport mit veröffentlichtem Stand und Entwurf, allen Immobilien und zugeordneten Medien, einmaliger verifizierter Datenübernahme in frische Instanzen, VPS-/DNS-Assistent, Caddy/HTTPS, Live-Startprogramm und lesender HTTPS-Prüfhelfer. Kein Export echter Anfragen, ausgefüllter PDFs, Benutzer oder Geheimnisse.
9. Nativer Windows-x64-Start ohne Docker/WSL: portable geprüfte Python-/Node-Laufzeiten, SQLite, Ersteinrichtung im Browser, freier lokaler Port, Start/Stopp/Diagnose/Reparatur/Sicherung. Fertiges Laufzeit-ZIP und kleines selbst einrichtendes Quellpaket; [Anleitung](../ANLEITUNG-WINDOWS.md), [Architektur und Testgrenzen](WINDOWS-DESKTOP.md). Ein echter Windows-/Edge-Durchlauf und 37 Backendtests sind bestanden. Eigene Desktop-Daten werden getrennt von bestehenden Docker-Daten gespeichert.

Aktuelle echte Oberflächenbilder: [Screenshots](screenshots/README.md). Der frühere Zielentwurf bleibt unter `entwuerfe/` dokumentiert. Freier React-Code wird über den Quellcode-/Buildweg angepasst; direktes GUI-Importformat bleibt ein geprüftes Datenpaket, keine beliebige Codeausführung.

Die [vollständige Nutzersimulation](SIMULATION.md) ist erfolgreich abgeschlossen: eigene Musterfirma, Wohnung, selbst erstelltes Design, separates HTTPS-Docker-Deployment, unabhängige Interessentin, genau eine zusätzliche echte Telegram-Objektanfrage an B1 Gruppe und anschließende Adminbearbeitung. Der dabei gefundene Tab-Wechselfehler ist korrigiert; jetzt 16 bestandene Browserfälle. Ein konfiguriertes Demo-Projekt steht auf GitHub zum Download bereit.

## Externe Voraussetzungen

- Kundeneigenes PDF ist eingebunden: 4 Seiten, 27 leere AcroForm-Felder, kein PDF-JavaScript. Download bytegleich geprüft.
- Telegram ist mit der gewählten Firmengruppe live geprüft: Testnachricht, Kontakt-Outbox und private Dokumentbenachrichtigung, insgesamt drei bestätigte Nachrichten. SMTP-Zugang ist verschlüsselt gespeichert, aber die Verbindung zu 465/587 wird aus dieser Cloud abgelehnt. Zwei Testaufrufe, keine angenommene E-Mail.
- Eigene Unternehmens-/Kontaktdaten und rechtlich geprüfte Texte vor öffentlicher Veröffentlichung ergänzen.
- Öffentliche Domain, TLS-Reverse-Proxy und geschützte externe Backupablage sind noch nicht eingerichtet.

## Referenzprüfung

Goldbach-Selbstauskunftsseite wurde nach Netzwerkfreigabe per HTTP gelesen: Seitentitel „Selbstauskunft zum Download“, zwei Links auf dasselbe PDF, kein HTML-Formular. Keine fremden PDFs, Marken, Texte oder Bilder übernommen. Ein kontaktloser Besichtigungsprozess wurde nicht implementiert. Aurevia war beim Abruf nicht zugänglich; dessen Design wurde ausschließlich anhand der vom Nutzer gelieferten Screenshots berücksichtigt.

Offizielle Next.js-Dokumentation zu App-Router-Seiten, Metadaten und Rewrites (mit installierter versionsspezifischer Dokumentation), SQLAlchemy-Sitzungsdokumentation und Telegram Bot API wurden konsultiert. Titelbild ist eine eigens generierte Architekturillustration, kein reales Angebot. Schriften: Manrope und Barlow Condensed aus Fontsource (OFL).

Die tatsächlichen Test-/Build-Ergebnisse stehen in `VALIDATION.md`. Dieser Stand ist keine Behauptung, dass Livebetrieb, fremde Integrationen, Backupziel oder Veröffentlichung bereits eingerichtet sind.

## Nachprüfung des ursprünglichen Auftrags

Siehe `AUFTRAGSABGLEICH.md` für den vollständigen Abgleich und `../ANLEITUNG-WINDOWS.md` für den einfachen lokalen Start. Ergänzt wurden persistenter Template-Import, Seitenformularziele, sichere Vorschau-Navigation ohne Versand, eigene Dokumentbenachrichtigungen mit atomarer Deduplizierung, vollständige Medienduplikate, Kontoverwaltung, Unicode-/Notizensuche und gefilterter CSV-Export. Windows-Starter und ein Paket ohne Zugangsdaten stehen bereit.
