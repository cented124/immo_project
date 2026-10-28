# Schnittstelle für Frontends

Raumwerk bleibt firmenneutral. Die Firmenidentität und alle Betriebsdaten kommen aus Config und den öffentlichen APIs. Ein Designwechsel erhält Immobilien, Anfragen, Rollen, Integrationen und URLs.

## Für Endnutzer

[Einfache Importanleitung einschließlich London-Paket und Windows-Update](FRONTEND-IMPORT.md). Ein **fertiges Version-3-ZIP** auswählen, automatische Prüfung abwarten, als Entwurf übernehmen, Vorschau prüfen, veröffentlichen. Kein manuelles Kopieren oder Build beim Importierenden.

## Drei kompatible Versionen

- **Version 1:** registrierter Atelier-/Editorial-Adapter, keine eigenen Dateien.
- **Version 2:** zusätzlich validiertes Theme mit Farben, Schriftstil, cover/split, grid/list, Rundung, Breite, Abständen und Überschriftengröße. Reines JSON, auch in einem Referenz-ZIP. Übernimmt keine Quellcodeänderungen oder Bilder.
- **Version 3:** vollständiger Browserbuild mit eigener HTML-/CSS-/JavaScript-Oberfläche, Bildern und lokalen Schriften. Eigenes React/Vite ist möglich, sofern die KI es vorher in Browserdateien baut. `entry` und optionale Bildzuordnungen `assets` ergänzen das Manifest. [Vollständiger Paket-/SDK-Vertrag](FRONTEND-PACKAGES.md).

Alle Manifeste besitzen eine neue ID, einen Namen, Adapter, alle sechs Seitentypen `home, properties, property, contact, disclosure, content` und alle vier Aktionen `search, inquiry, download, return`. Version 2 benötigt Theme; Version 3 benötigt eine HTML-Einstiegsdatei und alle dafür nötigen Dateien im ZIP. IDs werden nicht überschrieben. Schema: `schemas/manifest.schema.json` im KI-Paket.

## Daten- und Funktionsvertrag

- Config: `/api/public/config`. Module steuern Links, Seiten, Formulare und Downloads; serverseitige Sperren bleiben maßgeblich.
- Angebote: GET `/api/public/properties` mit bestehenden Filtern/Sortierung/Pagination und `/api/public/properties/{slug}`. Nur gelieferte öffentliche Angebote verwenden; keine Objekte, Energiewerte oder verborgenen Adressen erfinden.
- Anfragen: POST `/api/public/inquiries`, Idempotency-Key, Vor-/Nachname, E-Mail, bedingte Telefonpflicht, Betreff, Nachricht, Datenschutz, Honeypot; bei Objektanfragen echte property_id. Erfolg ausschließlich nach HTTP 202. Annahme ist keine Zusage externer Zustellung.
- PDF: GET öffentliche verknüpfte Datei. Private Rückgabe als Multipart an `/api/public/disclosure-return` mit reference, email, return_code, consent und file. Keine ausgefüllten Dateien oder deren Inhalte öffentlich machen.
- Analysen nur bei aktivem Modul. Vorschau erhält preview=1, benutzt ausschließlich freigegebene Vorschau-Lesefunktionen und sendet keine Formulare oder Ereignisse.
- Rechtstexte, Firmenkontakt, SEO, Seiten, Abschnitte und Inhalte aus Config. Keine Zugangsdaten, Tracker, festen Firmentexte oder externen CDN-Abhängigkeiten.
- Responsive ab 360 px, echte Formularlabels, Tastaturfokus, Kontraste, Leer-/Fehler-/Erfolgszustände sowie verständliche Behandlung von 404/409/413/422/429 und Netzfehlern.

Das JSON-Schema prüft Metadaten, nicht die gesamte inhaltliche Qualität beliebigen Programmcodes. Die KI muss ihren fertigen Build testen. Der Adminbereich und das Backend sind kein Bestandteil eines importierten Browserfrontends. Für eigene Server-/SSR-Funktionen bleibt der getrennte Quellcode- und Deploymentweg erforderlich.
