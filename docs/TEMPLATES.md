# Template-Schnittstelle, Version 1 und 2

Das [Frontend-Studio](FRONTEND-STUDIO.md) exportiert einen KI-unabhängigen Prompt, vollständigen Referenzcode, Schemas und Prüfliste. Version 2 ergänzt ein streng validiertes `theme` für direkt importierbare Gestaltung. Farben, Schrift, Hintergrund/Textfarbe, Hero cover/split, Karten grid/list, Rundung, Inhaltsbreite, Abstände und Überschriftengröße werden tatsächlich vom öffentlichen Renderer angewendet. Beim Studio-Import wird das Theme in den Konfigurationsentwurf übernommen; spätere manuelle Änderungen bleiben möglich. Ein Version-2-Manifest ohne Theme ist ungültig; Version 1 verwendet den registrierten Adapter ohne eigenes Theme.

Die Firmenidentität ist Datenbestand, kein Code. Kein Adapter darf Firmenname, Kontaktadressen oder Geheimnisse fest einbauen. Eine Instanz betreibt eine Firma; Designwechsel erhalten Immobilien-IDs, Anfragezuordnungen, URLs, Outbox und Authentifizierung.

## Unterstützte Formate

1. Mitgelieferte geprüfte React-Komponenten für Next.js, mit zentralem Konfigurationsvertrag und gemeinsamem API-Client.
2. Ein JSON-Manifest als deklarative Beschreibung. Ein Manifest allein importiert keine HTML-/React-Dateien und führt keinen Code aus.
3. Weitere React-Frontends nach einer bewussten Entwickler-Anpassung. Statisches HTML wird zunächst in React-Komponenten überführt; Formulare, Buttons und Datenansichten werden explizit verbunden.

Beispiel: `templates/atelier.json`; zweiter durchgängig verbundener Stiladapter `templates/editorial.json`. `template` ist eine serverseitig validierte Auswahl registrierter Adapter, niemals ein Dateipfad, Paketname oder Script-URL. Die Varianten verwenden dieselben funktionalen Seitenkomponenten; Editorial ändert Schrift, Farbflächen und Darstellung ohne Funktionstausch.

```json
{
  "id": "mein-design",
  "name": "Mein Design",
  "version": 1,
  "adapter": "atelier",
  "pages": ["home", "properties", "property", "contact", "disclosure", "content"],
  "actions": ["search", "inquiry", "download", "return"]
}
```

`POST /api/admin/templates/validate` prüft Schema, Schnittstellenversion, vorhandenen Adapter, alle erforderlichen Seitentypen und Aktionen. `POST /api/admin/templates/import` speichert ein validiertes Manifest dauerhaft in der Datenbank. Es erscheint in der Template-Bibliothek; `template` wählt seine ID und `template_adapter` liefert den registrierten Stiladapter. Doppelte IDs und zusätzliche Code-/Scriptfelder werden abgewiesen. IDs enthalten ausschließlich Kleinbuchstaben, Zahlen und Bindestriche. Die Studio-Dateischnittstelle `/api/admin/builder/design/validate` bzw. `/import` akzeptiert JSON oder begrenzte ZIP-Pakete, liest ausschließlich `manifest.json` und extrahiert oder installiert keine Quelltexte. Dort wird das Theme ebenfalls in den Entwurf übernommen. ZIP-Grenzen und Quellcodeweg: [Frontend-Studio](FRONTEND-STUDIO.md). Kein dynamischer `eval`/`import` aus Benutzerdateien. Die Prüfung ist bewusst **keine Installation fremden Codes**.

## Komponentenvertrag

Implementiert in `frontend/components/Website.tsx`:

| Seitentyp | Eingabe / Quelle | Verbindung |
| --- | --- | --- |
| home | veröffentlichte `Config`, geordnete `sections` | Firmenidentität, dynamischer Immobilien-Teaser, CTAs |
| properties | Suchparameter | `GET /public/properties` mit Pagination |
| property | gültiger Slug | `GET /public/properties/{slug}`; private Vorschau nur mit Adminsitzung |
| contact | Config, optional Seitentyp | `ContactForm`, serverseitiges Zielrouting |
| disclosure | aktives Modul + aktuelles PDF | Download, optional private Rückgabe |
| content | aktive Seite aus `Config.pages` | Text, SEO, optional `ContactForm` |

Gemeinsame Komponenten: Header/Navigation, Footer, `ContactForm`, `PropertyCard`, `Eyebrow`. Öffentliche Daten kommen aus `/api/public/config`, Immobilien aus `/api/public/properties`. Geheimnisse gibt es ausschließlich über maskierte Adminendpunkte. Das Backend validiert zusätzlich alle Module; ein Adapter kann deaktivierte Funktionen nicht durch einen sichtbaren Button wieder aktivieren.

Aktionen:

- **search**: UI-Filter → Querystring; keine hart codierten Karten.
- **inquiry**: validierte Angaben + Datenschutzbestätigung + `Idempotency-Key`; bei Immobilien ausschließlich eine existierende öffentliche `property_id`, serverseitig nachgeprüft. Erfolg erst nach HTTP 202.
- **download**: aktueller Dateiverweis aus veröffentlichter Config; keine Kopie mit dauerhaftem öffentlichen Dateipfad.
- **return**: Multipart-PDF mit bestehender Anfragekennung, persönlichem Rückgabecode und passender E-Mail; Dateien bleiben privat.

Lade-, Leer-, Fehler- und Annahmezustände sind Bestandteil des Vertrags. Aus einem angezeigten Erfolg darf kein behaupteter SMTP-/Telegram-Zustellerfolg werden. `accepted` und `sent` sind verschiedene Zustände.

## Vorhandenes Aurevia- oder anderes Frontend anschließen

1. Eigene Nutzungsrechte und vorhandene Quelldateien prüfen. Die Screenshots ersetzen keine React-Quellen und geben keine Rechte an fremden Bildern oder Texten.
2. Seiten inventarisieren: Start, Übersicht, Exposé, Kontakt, optionale PDF-Seite und Inhaltsseiten. Jedes Formular/CTA in einer Zuordnungsliste erfassen.
3. Feste Firmendaten durch `Config` ersetzen. Keine Marken-/Kontaktdaten in CSS oder Komponenten hinterlegen. Farben über `--primary`/`--accent`, Typografie über die erlaubte Schriftwahl.
4. Formular-Markup an `ContactForm` oder denselben API-Vertrag anschließen; Pflichtfelder, Zustände, Datenschutz, Honeypot und Idempotenz übernehmen.
5. Immobilienkarten und Exposé anhand des Property-Vertrags rendern. Entwürfe nicht aus einer allgemeinen Liste auswählen und im Browser verstecken: nur öffentliche API verwenden.
6. Modulprüfungen für Navigation, Seiten, CTAs und Downloads anwenden. Neue kontrollierte Adapter-ID in Backend-`Config` und Frontendauswahl registrieren. Das ist eine Quellcodeänderung mit Review, kein automatischer Runtime-Import.
7. Manifest prüfen, Browser-Suite ergänzen und den API-Test zum deaktivierten Modul ausführen. Private Dateien müssen auch bei bekannter URL gesperrt bleiben.
8. Erst in der authentifizierten Vorschau prüfen, anschließend Konfiguration veröffentlichen.

Die mitgelieferten Atelier-/Editorial-Adapter sind vollständig verbunden. Für ein beliebiges fremdes HTML oder React-Frontend wird keine automatische Kompatibilität versprochen.
