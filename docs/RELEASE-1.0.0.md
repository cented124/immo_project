# Raumwerk 1.0.0 – Freigabeprüfung

Stand: 28.10.2026. Die frühere Entwicklungsausgabe bleibt im Branch `entwicklung`; die feste Ausgabe liegt unter `fertige-version/1.0.0` und im Release `v1.0.0`.

## Ergänzt und bereinigt

- Betriebsstatus und Startprüfung des veröffentlichten Stands: lokale/Server-Installation, Version, Medien/Pakete, Hintergrunddienst, Zustellfehler und Speicher.
- Vollständige lokale Sicherung mit Dateiprüfsummen und geführte Wiederherstellung mit Vorabprüfung, zusätzlicher Sicherung des bisherigen Stands und Austausch erst nach erfolgreicher Prüfung.
- Wiederherstellung beendet alte Sitzungen und pausiert wartende Zustellungen. So wird ein alter Warteschlangenstand nicht automatisch erneut versendet.
- Passwortwiederherstellung eines vorhandenen Administrators mit Betriebssystemzugriff; andere eigene Sitzungen über „Mein Konto“ beenden.
- Automatische Sitemap, robots.txt, Exposé-Titel und Canonical-/OpenGraph-Metadaten. Lokale Installationen sperren Crawler.
- Aktuelle geprüfte Backend-Bibliotheken und separat installierbare Testabhängigkeiten.
- Öffentliche Entwicklerdokumentation der API standardmäßig abgeschaltet; alte JSON-Importmaske unter „Erweitert“; kurze Hauptanleitung. Nützliche Tests, Diagnose und Quellcode bleiben enthalten.

## Automatisierte Prüfung

Bisher abgeschlossen: 56 Backendtests, 20 Browserfälle für Desktop/Mobil, TypeScript und Produktions-Build. Nach dem Bibliotheksupdate alle Backend- und Browserfälle erneut bestanden. npm-Audit der Produktionsabhängigkeiten und pip-audit der Backend-Produktionsabhängigkeiten melden zum Prüfzeitpunkt keine bekannten Schwachstellen.

Der abschließende Windows-Lauf und die beiden Simulationsprotokolle werden vor Veröffentlichung dieser Ausgabe ergänzt. Dieser Kandidatenstand ist noch keine abgeschlossene Freigabe.

## Umfang und Grenzen

Eine Firma und eine Website je Installation; SQLite im lokalen Windows-Baukasten und PostgreSQL im VPS-Betrieb. Kein automatischer Abgleich zwischen diesen Datenbanken. Neue Live-Inserate werden direkt im Server-Admin gepflegt.

Die Prüfungen sind kein Versprechen absoluter Fehlerfreiheit. Eigene Domain/DNS, öffentliches Hosting, rechtskonforme Inhalte und reale Mail-/Telegram-Ziele müssen am Betriebsort eingerichtet und geprüft werden. Im aktuellen Freigabetest gehen keine echten E-Mails oder Telegram-Nachrichten an Personen. Ein lokales HTTPS-Deployment ersetzt keinen Test eines realen öffentlichen VPS. Bei importierten Sandbox-Frontends bleibt die dokumentierte SEO-Einschränkung bestehen.
