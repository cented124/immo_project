# Vollständige Browserfrontends – Version 3

Version 1/2 bleiben Theme-/Adaptermanifeste. Version 3 liefert einen unveränderlichen Browserbuild als ZIP. Schema: `Manifest` in `backend/app/templates.py`. Alle sechs Seitentypen und vier Aktionen bleiben verpflichtend. `entry` bezeichnet eine relative HTML-Datei. `assets` ordnet optional `hero_image`, `approach_image`, `logo`, `favicon` Paketbildern zu. Theme ist optional. Unternehmens-/Registerdaten, Konten, Anfragen und Integrationen werden nicht aus dem Frontend übernommen.

## Paket bauen

Im vollständigen KI-Referenzprojekt:

```sh
npm --prefix frontend ci
node scripts/build-frontend-package.cjs --id eigenes-design-eindeutig --name "Eigenes Frontend"
```

Ergebnis: `downloads/Raumwerk-Frontend.zip`. Der Builder bündelt die öffentliche React-Oberfläche und lokale Fonts mit esbuild, ersetzt NextLink durch normale Browserlinks und übernimmt die öffentlichen Bilder und statischen Dateien. Eigene weitere Medien als relative Build-Assets importieren, damit esbuild sie mitnimmt. Der Endnutzer erhält nur dieses ZIP. `frontend/portable/example.zip` ist ein fertiges Beispiel. HTML/CSS/JavaScript können auch unabhängig gebaut werden; keine serverseitigen Next-Funktionen im Browserbuild verwenden.

## Browservertrag

Der Host fügt vor dem Paketcode `/api/public/frontend-sdk.js` ein. `await window.Raumwerk.ready()` liefert `{config,path,preview,base,origin}`. Die sechs Seiten werden aus `path` und den aktivierten Config-Modulen gerendert. `window.Raumwerk.navigate('/immobilien')` navigiert die äußere URL. Normale interne Anker werden ebenfalls weitergereicht. `window.Raumwerk.media(url)` löst Vorschau-Medien auf; vorhandene Referenz-IMG-Elemente werden automatisch angepasst.

`fetch('/api/public/...', options)` bzw. `window.Raumwerk.request(...)` verwenden die Hostbrücke. Unterstützt werden nur GET für config/properties/properties/{slug}/files/{fid} und POST für inquiries/events/disclosure-return. JSON und begrenztes Multipart mit File sind möglich. HTTP-Status, JSON-/Dateiinhalt und Idempotency-Key bleiben erhalten. Der Host gibt weder Cookies noch Sitzungsdaten weiter. Kein generischer Admin-, Netzwerk- oder Dateisystemzugriff.

In der privaten Vorschau werden ausschließlich Config und serialisierte Vorschauobjekte gelesen. Die Referenz-Aliase `/api/admin/config` und `/api/admin/preview/properties` werden nur dort unterstützt. Schreibzugriffe sind hostseitig gesperrt, unabhängig von der UI des fremden Frontends. Private Dokumente/Rückgaben sind über die Vorschau-Medienbrücke nicht lesbar. PDF-Downloads und geschützte Rückgaben bleiben an die vorhandenen API-Prüfungen gebunden.

## Isolation und Betrieb

Der Browserrahmen verwendet `sandbox="allow-scripts allow-forms allow-downloads"`, ausdrücklich ohne `allow-same-origin`. Paket-HTML erhält zusätzlich serverseitig eine Sandbox-CSP. Elternseite: frame-src self. Paket: keine externen Verbindungen, Formnavigation, Plugins, eingebettete Frames oder Topnavigation. Der Browsercode läuft nicht auf dem Server und erhält keinen Zugriff auf Admin-DOM oder Speicher. Klassische lokale Scripts/CSS und Fonts sind erlaubt; keine Remote-CDNs. Beliebiger frei veränderter Code benötigt weiterhin fachliche und visuelle Abnahme.

ZIP-Pfade, Groß-/Kleinschreibungsduplikate, Windows-Gerätenamen, Symlinks, verschlüsselte Archive, Dateitypen, Bildgrößen, UTF-8 und Gesamtgröße werden geprüft. Die Prüfung installiert nichts. Import schreibt Dateien und Registrierung mit Rücknahme bei Fehlern, ID-Duplikate überschreiben nichts. Dateien unter `DATEN/designs/{id}` sind vor Veröffentlichung nur mit einer signierten, auf das Paket beschränkten Vorschaufreigabe (15 Minuten) erreichbar. Nach Veröffentlichung bleiben nur aktive bzw. explizit als Unternehmensbild referenzierte Dateien öffentlich. Keine Anfrage-/Zugangsdaten im Paket.

Der Host rendert Seitentitel, Beschreibung, Robots und die bisherigen 404-/Modulprüfungen. Der sichtbare eigene Inhalt rendert im Browserrahmen; dessen Indexierung ist nicht gleichbedeutend mit vollständig servergerendertem HTML. Für besondere SEO-/SSR-Anforderungen bleibt der geprüfte Quellcode-Deploymentweg verfügbar.

Projektexporte enthalten registrierte Browserpakete samt Größen und SHA-256-Dateimetadaten. Frischer Seedimport prüft sämtliche Bytes vor Datenübernahme. Bestehende Installationen werden nicht überschrieben. Desktop-Sicherung umfasst den gesamten DATEN-Ordner.
