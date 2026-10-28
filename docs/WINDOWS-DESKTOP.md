# Native Windows-Architektur und Prüfung

Der Desktop-Start verwendet portable offizielle Node-/CPython-Laufzeiten, SQLite und einen ausschließlich an 127.0.0.1 gebundenen Gateway. Er liest die Docker-`.env` nicht ein. DATEN enthält den eigenständigen Datenbestand einschließlich verschlüsselter Integrationen und dauerhaftem Schlüssel; .runtime enthält ersetzbare Programme. Docker-/PostgreSQL- und Desktop-Daten bleiben getrennt.

## Laufzeiten und Einrichtung

`scripts/windows-runtime.json` legt Version, HTTPS-Quelle und SHA-256 für Node, eingebettetes Python und pip fest. Node wurde gegen das offizielle SHASUMS-Manifest, der Python-Paketdigest gegen den veröffentlichten Sigstore-Bundledigest abgeglichen. Der Bootstrap prüft Downloads vor dem Entpacken; TLS-Prüfungen bleiben aktiv. Die vollständigen Windows-x64-Wheels stehen mit Versionen und Hashes in `backend/requirements-windows.lock`, einschließlich Windows-spezifischer Abhängigkeiten. Es werden ausschließlich Binärwheels installiert; kein Compiler ist erforderlich.

Das kleine Quellpaket richtet sich beim ersten Start selbst ein. Das fertige Windows-Release enthält dieselben bereits auf Windows eingerichteten Laufzeiten, Backend-Pakete und einen Produktionsbuild. Es enthält keine Benutzer, Anfragen, Schlüssel, Sitzungen oder Testdatenbanken. Seine Relokation und sein Start ohne funktionierenden externen Proxy werden im Windows-Job geprüft. Lizenzen der Laufzeiten und installierten Bibliotheken bleiben enthalten.

Die Desktop-Variante verwendet einen regulären Next-Produktionsbuild, kein auf Windows möglicherweise ortsgebundenes Standalone-Junction-Paket. Frontend-Builds werden anhand des Inhalts, der Plattform und Node-Version erkannt. Normale Konfigurationsänderungen erfordern keinen Neubau. Die Linux-/Docker-Variante verwendet weiter den bisherigen Standalone-Build.

## Prozess- und Zugriffskontrolle

Der Gateway wählt einen freien öffentlichen Loopback-Port und leitet `/api` direkt an FastAPI weiter. SSR verwendet die tatsächliche interne API-Adresse. Interne Ports sind dynamisch; ein belegter Port führt nicht zum Beenden fremder Prozesse. Systemproxies erhalten keine lokalen Formularanfragen. Ein HTTP-Portwechsel erfordert keinen erneuten Frontend-Build.

Der Supervisor betreibt FastAPI im eigenen Prozess und verwaltet den Node-Prozessbaum unter Windows mit einem Job Object. Ein kontrollierter Stopp fährt API und Worker herunter und beendet nur die eigenen Prozesse. Dateisperren verhindern parallele Installationen und doppelte Supervisoren; OS-Sperren werden auch nach einem Prozessabbruch freigegeben. Start prüft Instanzkennung und Erreichbarkeit, nicht nur eine PID oder irgendeine Antwort auf Port 3000.

Einrichtung und Steuerung besitzen getrennte zufällige Geheimnisse. Der Einrichtungslink verwendet ein URL-Fragment; der Schlüssel wird nicht in Accesslogs geschrieben. Host- und Origin-Prüfung, einmalige Administratoranlage, gesperrtes Setup nach Anlage und HttpOnly-Anmeldesitzungen bleiben aktiv. Native Instanzen verwenden unterschiedliche Sitzungs-Cookienamen. Die Steuerungsdatei, Protokolle und DATEN erhalten unter Windows private Ordnerberechtigungen.

Die Proxygrenze begrenzt auch Chunked-Uploads, weist mehrdeutige Längenangaben ab und erhält Cookies, Fehlerstatus und Dateidownload-Header. Private Dateien bleiben API-seitig geschützt. Diagnose gibt keine Konfiguration oder Zugangsdaten aus. Die Sicherung stoppt den lokalen Datenbestand vor der ZIP-Erstellung; sie ist ein privates, nicht passwortverschlüsseltes Backup.

## Nachweise und Grenzen

Prüfungen umfassen Backendtests für Proxy-/Setupgrenzen und Sperren, einen nativen Produktionsdurchlauf mit Browser, Ersteinrichtung, mehrfachen Start, belegtem Port, Datei-Upload, Inserat, Objektanfrage, Projektexport mit Import in eine leere native Datenbank, Neustart, erhaltenem Integrationsschlüssel und Sicherung. Der Export wird auch auf vorhandene Windows-Starter und fehlende Konten/Anfragen/Geheimnisse geprüft. SMTP und Telegram werden dabei nicht live angesprochen.

Der Workflow **Windows without Docker** führt zusätzlich PowerShell 5.1, das echte eingebettete Windows-Python, Node für Windows und Edge auf `windows-latest` aus. Nach erfolgreichem Test wird das Daten-freie Laufzeitpaket gebaut und in einem anderen Pfad mit Leerzeichen und Umlauten erneut offline gestartet. Eine Veröffentlichung erfolgt auf `main` erst nach diesen Schritten. Laufstatus und Nachweise stehen im GitHub-Actions-Lauf.

Ein Windows-Runner ist ein echter Windows-Test, aber keine Prüfung jedes Windows-10/11-PCs, jeder Firmenrichtlinie, Antiviruskonfiguration, ARM-Installation oder Netzumgebung. Unterstützung dieses Pakets: Windows x64. Kein Anspruch auf 100 Prozent Fehlerfreiheit.
