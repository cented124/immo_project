# Frontend-Studio: Firma → KI-Paket → Import → Prüfung

Eine Instanz gehört zu einer Firma. Raumwerk und das Referenzfrontend bleiben firmenneutral. Die öffentliche Firmenidentität kommt aus der Konfiguration, nicht aus fest eingebauten Marken im Code.

1. Unter **Firma & Rechtliches** Firmennamen, Anschrift, Vertretung und erforderliche Registerdaten eintragen. Ein Impressumsentwurf kann aus den Daten erzeugt werden; anschließend fachlich ergänzen und prüfen. Datenschutz muss zu den tatsächlich eingesetzten Diensten passen. Änderungen speichern.
2. Unter **Frontend-Studio** Zielgruppe, Stil und weitere Wünsche eintragen. **Prompt erstellen** übernimmt die aktuellen Eingaben zuerst in den gespeicherten Entwurf. Der Prompt kann kopiert oder als Markdown gespeichert werden. **Referenzpaket exportieren** lädt ein ZIP mit demselben Firmenprofil, Prompt, Manifest, JSON-Schemas, Vertrag, Checkliste und vollständigen baubaren Quellen herunter.
3. Prompt und ZIP einer beliebigen KI geben. Keine SMTP-/Telegram-Zugangsdaten oder echten Anfragen weitergeben; diese sind im Paket nicht enthalten. Firmendaten und Rechtstexte sind enthalten: deren Weitergabe an die gewählte KI verantwortet der Betreiber.
4. Die KI liefert ein eindeutiges `manifest.json`, Version 2. Dieses oder ein ZIP mit `manifest.json` auf oberster Ebene auswählen. **Paket prüfen**, Ergebnis ansehen, dann **Als Entwurf übernehmen**. Es wird nichts automatisch veröffentlicht. Neue IDs verwenden; bestehende Designs werden nicht überschrieben.
5. Vorschau, technische Prüfung und die folgende Checkliste durchgehen. Erst danach **Veröffentlichen**. Unter **Versionen** können frühere Konfigurationen verglichen und als Entwurf wiederhergestellt werden.

## Zwei Wege für KI-Frontends

**Direkt importierbares Designpaket:** Das Manifest steuert den vorhandenen vollständig angebundenen Renderer. Verfügbar sind Atelier/Editorial, Farben, lokale Schrift, Hintergrund/Textfarbe, Hero als Bildfläche oder geteilte Ansicht, Karten als Raster/Liste, Rundung, Inhaltsbreite, Abschnittsabstände und Überschriftengröße. Die zulässigen Werte stehen in `schemas/manifest.schema.json`; zusätzliche Felder werden abgewiesen. Inhalte und Seiten werden im Baukasten bearbeitet. Version 1 bleibt für bisherige Adapter-Manifeste unterstützt.

**Freies React-/CSS-Frontend:** Das Paket enthält unter `reference/` den kompletten Projektquellcode inklusive Backend und isolierter Tests. Die KI kann daraus ein frei gestaltetes Frontend entwickeln. Diese Quelltexte werden bewusst nicht im laufenden Admin hochgeladen und ausgeführt. Sie müssen im Projekt eingebaut, gebaut und getestet werden; anschließend wird das veränderte Gesamtprojekt per Docker deployt. Ein Manifest allein installiert keine React-Komponenten. Die nachfolgende Suite ist dafür verbindlich. Beliebige KI-Ausgaben werden nicht pauschal als kompatibel bezeichnet.

ZIP-Import erlaubt nur das Manifest, die Begleitdateien README/PROMPT/CONTRACT/CHECKLIST/company sowie Referenzdateien unter `reference/` und Schemas unter `schemas/`. Referenzdateien werden weder extrahiert noch ausgeführt. Unsichere Pfade, Symlinks, doppelte Einträge, verschlüsselte Archive und übergroße Pakete werden abgewiesen. Maximal 10 MB komprimiert, 32 MB entpackt, 400 Einträge; Manifest maximal 128 KB.

## Abnahmecheckliste

- [ ] Firmendaten und Impressum stammen aus Config; kein Unternehmensname im Komponentenquellcode fest eingebaut.
- [ ] Startseite, Suche, Exposé, aktive Inhaltsseiten, Kontakt, Impressum, Datenschutz und optional Selbstauskunft vorhanden.
- [ ] Geordnete Abschnitte, Modulsichtbarkeit und deaktivierte direkte Routen korrekt.
- [ ] Echte öffentliche Immobilien aus API mit Filtern, Sortierung und Pagination; keine Entwürfe oder privaten Objektdateien sichtbar.
- [ ] Formulare mit Pflichtfeldern, bedingter Telefonpflicht, Datenschutz, Honeypot, Idempotenz, korrekter Objekt-/Seitenzuordnung.
- [ ] Erfolg nur nach Annahme durch das Backend; Zustellung über E-Mail/Telegram separat überprüfbar.
- [ ] PDF-Download und private Rückgabe mit Rückgabecode; vertrauliche Inhalte bleiben privat.
- [ ] Authentifizierte Vorschau erhält ihre Navigation, versendet nichts und zählt keine Analysen.
- [ ] Lade-, Leer-, Fehler-, Wiederholungs- und Annahmezustände verständlich.
- [ ] Mobil ab 360px ohne seitliches Scrollen; Tastaturbedienung, Labels, Fokus und Farbkontraste geprüft.
- [ ] SEO/404-Regeln, Admin, Authentifizierung und Rollen unverändert funktionsfähig.
- [ ] Keine Geheimnisse, Fremdtracker oder Remote-Scripts im Frontend.
- [ ] TypeScript-Prüfung, Produktionsbuild, Backend- und Browsertests erfolgreich.

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Die technische Prüfung im Studio prüft Datenvertrag und verknüpfte Dateien. Rechtliche Vollständigkeit, beliebigen fremden Programmcode und die DNS-/HTTPS-Erreichbarkeit eines späteren Servers kann sie nicht beweisen. Hinweise werden deshalb getrennt von technischen Fehlern angezeigt.

## Versionsverlauf

Die letzten 100 Konfigurationsstände werden bei Speichern, Veröffentlichung, Designimport und Wiederherstellung festgehalten. Der Vergleich zeigt die gespeicherten Werte, nicht nur ein Datum. Wiederherstellung sichert den bisherigen Entwurf und stellt ausschließlich die Konfiguration als neuen Entwurf her. Immobilien, Anfragen, Zugangsdaten und Integrationen werden nicht zurückgesetzt. Das ersetzt kein vollständiges verschlüsseltes Backup.
