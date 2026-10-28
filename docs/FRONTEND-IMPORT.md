# Ein Frontend importieren – ohne Dateien zu kopieren

Du brauchst die aktuelle Raumwerk-Version. Ein älteres Raumwerk importiert nur Theme-Werte aus JSON, keinen eigenen Code oder Bilder.

## Dein London-Frontend aus raumwerk_test

1. [Aktuelles Windows-Paket](https://github.com/cented124/immo_project/releases/latest) laden und wie unten aktualisieren.
2. [Westminster-Frontend.zip herunterladen](https://github.com/cented124/immo_project/raw/refs/heads/main/downloads/Westminster-Frontend.zip). Das ist das fertig gebaute Frontend aus `cented124/raumwerk_test`, einschließlich London-Gestaltung, Illustration und lokaler Schriften.
3. Im Baukasten **Frontend-Studio → Frontend importieren** öffnen und das ZIP auswählen. **Nicht entpacken.**
4. Die Prüfung läuft automatisch. **Als Entwurf übernehmen → Vorschau öffnen**.
5. Wenn alles passt, im Studio **Veröffentlichen** anklicken.

Firmenname, Texte, Immobilien, Anfragen und Integrationszugänge bleiben deine bestehenden Daten. Das London-Paket ersetzt das Design sowie Titel- und Beratungsbild. Kein `company.json` wird automatisch in deinen Betrieb übernommen.

Das ursprüngliche `manifest.json` in `raumwerk_test` ist nur ein älteres Theme. **Code → Download ZIP** dieses Quellcode-Repositories ergibt kein fertiges Importpaket. Verwende das oben verlinkte fertige ZIP.

## Deine vorhandene Windows-Installation aktualisieren

1. In der bisherigen Installation **SICHERN.cmd** öffnen. Das stoppt Raumwerk und legt eine private Sicherung an.
2. Das neue Windows-Paket in einen **neuen** lokalen Ordner entpacken.
3. Den bisherigen Ordner **DATEN vollständig** in den neuen Raumwerk-Ordner kopieren. Er enthält auch den Schlüssel deiner Integrationen. Nicht nur `app.db` kopieren.
4. Im neuen Ordner **STARTEN.cmd** öffnen und mit deinem bisherigen Konto anmelden.

Die alte Installation und Sicherung zunächst behalten. Nicht beide Installationen gleichzeitig mit demselben Datenordner betreiben. Falls nach dem Kopieren unerwartet eine neue Administratoranlage erscheint, zuerst STOPPEN und prüfen, ob DATEN im richtigen Raumwerk-Ordner liegt.

## Beim nächsten Mal die KI richtig beauftragen

Im Studio die Firmendaten und Gestaltungswünsche speichern, dann **Referenzpaket exportieren**. Dieses ZIP der KI geben. Der enthaltene Prompt verlangt genau **eine fertige Raumwerk-Frontend.zip**, mit allen Bildern, Styles, Schriften und dem gebauten Browsercode. Die KI baut und prüft; du importierst nur das fertige ZIP.

Mit **Beispiel-ZIP zum Importieren** kannst du den Ablauf ohne eine weitere KI ausprobieren. Ältere JSON-Themes funktionieren weiter, ändern aber nur Theme-Werte.

## Was ein vollständiges ZIP unterstützt

Fertiges HTML, CSS, JavaScript, Bilder (PNG/JPG/WebP/GIF/ICO), WOFF/WOFF2-Schriften und eine `manifest.json` Version 3. Bis 10 MB als ZIP, 32 MB entpackt und 400 Dateien. Bildzuordnungen für Titelbild, Beratungsbild, Logo und Browser-Icon sind optional und werden vor dem Import angezeigt.

Eine eigene React-/Vite-Oberfläche kann vor der Lieferung in Browserdateien gebaut werden. Ein Next.js-Quellprojekt mit Serverfunktionen, eine Backendanwendung oder ein Ordner mit `node_modules` ist kein fertiges Browserpaket. Die mitgelieferte KI-Bauanleitung macht diesen Unterschied konkret; der importierende Benutzer muss weder npm noch Python bedienen.

Der Import registriert das Paket als neuen Entwurf. Die öffentliche Website bleibt bis zum Veröffentlichen unverändert. Unter **Versionen** kannst du einen vorherigen Stand als Entwurf wiederherstellen und erneut veröffentlichen. Pakete und Bilder sind auch im Projektexport und in der Desktop-Sicherung enthalten.
