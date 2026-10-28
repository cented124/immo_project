# Frontend-Studio und KI-Abnahme

Für Endnutzer: [Einfacher ZIP-Import](FRONTEND-IMPORT.md). Für Entwickler und KI: [Browserpaket und SDK](FRONTEND-PACKAGES.md).

## Der Ablauf

1. Firmen-/Registerdaten und Gestaltungswünsche im Studio speichern.
2. Das Referenzpaket herunterladen und der KI geben. PROMPT.md enthält die aktuellen Daten und den verbindlichen Vertrag.
3. Die KI gestaltet die öffentliche Website, baut und prüft sie und liefert **genau eine importfertige Raumwerk-Frontend.zip**. Ein nacktes Manifest oder ein Quellcode-Repository ist kein Ersatz für das fertige Frontend.
4. Endnutzer wählt dieses ZIP im Studio. Die automatische Prüfung zeigt Namen, Dateianzahl, Bilder und Bildersetzungen. Als Entwurf übernehmen und Vorschau ansehen.
5. Veröffentlichung erfolgt bewusst nach Abnahme. Versionen können frühere Konfigurationen als Entwurf zurückholen.

Ein bereits fertiges Beispiel liegt unter `frontend/portable/example.zip` und ist im Studio separat downloadbar. Der Buildhelfer `node scripts/build-frontend-package.cjs --id eindeutige-id --name "Mein Design"` bündelt öffentliche React-Komponenten, CSS, Bilder und Schriften. Keine manuellen Einbauschritte beim Endnutzer. Ältere Version-1/2-Manifeste bleiben reine Adapter-/Themeimporte; Quellen darin werden nicht installiert.

## Checkliste für die KI

- Alle aktivierten Seitentypen aus Config, Navigation, Impressum, Datenschutz und 404-/Modulzustände vorhanden.
- Startseite mit geordneten Config.sections, Firmenlogo, Texten, Bildern, Farben, SEO und Footer.
- Angebote filtern/sortieren/blättern; Leerzustand und Exposé nach Slug; echte property_id und korrekte Preis-/Energiedaten.
- Kontakt/Objekt-/Seitenformulare: Pflichtfelder, Datenschutzzustimmung, Idempotenz, Honeypot, Telefonpflicht, verständliche Zustände, Erfolg nach 202.
- PDF-Download und private Rückgabe mit Kennung, E-Mail und persönlichem Rückgabecode; Datei bleibt privat.
- Vorschau: Navigation behält preview=1, Formularbuttons sind gesperrt, keine Anfragen und keine Analysen. Öffentliche Website bleibt bis zur Veröffentlichung unverändert.
- Kein Admin-/Auth-/Outbox-Code im ZIP, keine Tokens, Passwörter oder Empfängerlisten. Keine festen Firmendaten und keine erfundenen Angebote.
- HTML/CSS/JS/Schriften/Bilder vollständig lokal im Browserpaket; keine Serverfunktionen, node_modules, Paketinstallation oder CDN nötig.
- Tastatur, Formularlabels, Kontraste, mobile Breite ab 360 px, Fehlerfälle und leere Angebote visuell prüfen.
- Tatsächlich das fertige ZIP importieren und testen, nicht nur Quellcode oder Manifest prüfen. Der Host blockiert private API-Zugriffe und Schreibaktionen in der Vorschau zusätzlich.

## Nachweise

```sh
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Die Browserpaket-Tests spielen Import, Vorschau, Veröffentlichung, getrennten Interessenten, Kontakt, PDF-Download/-Rückgabe und Adminsicht auf Desktop und Mobil durch. `scripts/test-desktop.cjs` prüft zusätzlich native Prozesse, Objektanfrage aus dem importierten Frontend, Export-/Seedimport, Neustart und Sicherung. Keine automatisierten echten E-Mails oder Telegram-Nachrichten senden.

Schemas und API-Vertrag sind im KI-Paket enthalten. Für frei veränderten Code Prüfbericht und offene Punkte wahrheitsgemäß angeben. Der eigene Browserbuild rendert im isolierten Rahmen; Details und SEO-/SSR-Grenzen stehen im Paketvertrag. Ein fremder VPS, DNS oder öffentliches Zertifikat ist erst nach tatsächlicher Prüfung als live anzusehen.
