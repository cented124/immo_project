# Komplette Simulation – 27.10.2026

**Ergebnis: bestanden.** Zwei getrennte Browsersitzungen haben den Ablauf vom Baukasten über den Deploy bis zur echten Telegram-Zustellung und Bearbeitung im deployten Admin durchgespielt. Alle Firmen-, Personen- und Objektdaten sind erfunden.

| Schritt | Tatsächlich durchgeführt |
| --- | --- |
| Betreiber richtet Firma ein | Küstenklar Immobilien GmbH, Mara Beispiel, Beispielkai 18 in Musterhafen; eigene Texte und als Simulation gekennzeichnete Anbieter-/Datenschutzhinweise. |
| Wohnung anlegen | „Sonnenloggia am Beispielkai – SIMULATION“, 78 m², 3 Zimmer, 980 € Kaltmiete + 180 € Nebenkosten = 1.160 € Warmmiete. Bild ist eine Architekturillustration. Erst privat gespeichert, dann veröffentlicht. |
| Frontend bauen und importieren | KI-Prompt und Referenz exportiert; eigenes kompatibles Designpaket „Küstenklar · Kai“ mit geteiltem Hero, Listenlayout, Serifenschrift und eigenen Farben erstellt, im Studio geprüft, importiert und veröffentlicht. |
| Deployment | Das über die GUI exportierte Projekt mit Website, Admin, Medien und PostgreSQL in einer eigenen Docker-Installation gestartet. HTTPS mit lokaler CA und geprüfter Zertifikatskette. Öffentliche Domain und fremder VPS waren nicht Teil dieser Simulation. |
| Interessentin | Lena Muster besucht Startseite und Über-uns-Seite, lädt die Demo-PDF herunter, filtert nach Mietwohnung in Musterhafen, öffnet das Exposé und schickt eine objektbezogene Besichtigungsanfrage mit erfundenen Angaben. |
| Telegram | **Genau eine echte Nachricht an B1 Gruppe**, mit Namen, Nachricht und Objektbezug. Offizielle Telegram-API erfolgreich; Outbox: `sent`, **ein Zustellversuch**. Keine Nachricht an den alternativen Privataccount; keine E-Mail. |
| Betreiber kontrolliert | Anfrage #1 im deployten Admin geöffnet; richtige Wohnung und Nachricht überprüft, Notiz ergänzt, Status auf **In Bearbeitung** gesetzt und CSV exportiert. |

Im Dashboard waren ein Exposéaufruf, ein Klick auf den Anfragebutton und eine angenommene Anfrage sichtbar. Das sind aggregierte Ereignisse; der Baukasten erstellt kein personenbezogenes Klickprofil. Die konkrete Anfrage ist über Name und Objektzuordnung nachvollziehbar.

Zusätzlich geprüft: Besucher erhalten keinen Adminzugriff, PDF-Download bleibt bytegleich, mobile Darstellung läuft nicht seitlich über. E-Mail-Versand wurde in dieser Simulation nicht eingerichtet oder getestet.

## Ansehen und ausprobieren

- [Website-Screenshot](simulation/website.png)
- [Exposé](simulation/expose.png)
- [Eingegangene Anfrage im Admin](simulation/admin-anfrage.png)
- [Dashboard nach der Bearbeitung](simulation/admin-dashboard.png)
- [Mobile Website](simulation/mobil.png)
- [Erstellter KI-Prompt](simulation/KI-Prompt.md) und [importiertes Manifest](simulation/manifest.json)
- [Konfiguriertes Demo-Projekt herunterladen](https://github.com/cented124/immo_project/raw/refs/heads/main/downloads/Kuestenklar-Demo-Website.zip)
- [Importierbares Frontend-Design herunterladen](https://github.com/cented124/immo_project/raw/refs/heads/main/downloads/Kuestenklar-Frontend.zip)

Das Demo-Projekt enthält Website, Musterfirma, Wohnung und Demo-PDF. Entpacken und mit `STARTEN.cmd` wie in der [Windows-Anleitung](../ANLEITUNG-WINDOWS.md) starten; einen eigenen Administrator anlegen. Für einen neuen Import des Designs bei bereits vorhandener ID diese im Manifest ändern.

Anfragen und Telegram-Zugangsdaten werden vom Projektexport nicht übernommen. Die tatsächlich eingegangene Anfrage ist hier mit Screenshots dokumentiert. Der Download versendet daher nicht automatisch an die echte Gruppe. Das Paket dient ausschließlich zum Testen; Firmendaten und Rechtstexte sind nicht für einen realen Geschäftsbetrieb bestimmt.

## Gefundener Fehler behoben

Ein schneller Wechsel zwischen SMTP- und Telegram-Tab konnte Einstellungen des vorherigen Tabs anzeigen und die Oberfläche abstürzen lassen. Beim Wechsel wird das alte Formular jetzt sofort geleert; verspätete Antworten werden ignoriert. Während des Speicherns sind die Tabs gesperrt. Ein Browserfall mit absichtlich verzögerter Antwort sichert das auf Desktop und Mobilgerät ab. Der Kundendurchlauf wurde anschließend mit dem korrigierten Produktionsbuild erfolgreich abgeschlossen. Zusätzlich wurde der Kontrast des zweiten Links im geteilten Hero verbessert.
