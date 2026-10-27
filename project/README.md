# Daten für eine neue Installation

Dieses Verzeichnis enthält im normalen Quellpaket nur diesen Hinweis. Der Projektexport im Admin ergänzt `project.json` und die zugeordneten Medien unter `files/`. Diese Dateien gehören nicht in GitHub.

Beim Docker-Build werden die Exportdaten mit dem Eigentümer des nicht privilegierten App-Benutzers nach `/seed` kopiert. Dadurch funktioniert der Erstimport auch nach dem Entpacken mit strengen Dateirechten. Die öffentliche API liefert keine Dateien aus `/seed` aus. Laufende Daten liegen anschließend ausschließlich im Datenbank-/Dateivolume; ein Neustart überschreibt sie nicht.

Projektpakete und daraus gebaute eigene Images enthalten auch zugeordnete interne Objekt-PDFs. Entsprechend vertraulich aufbewahren. Ein Projektexport enthält keine Anfragen, ausgefüllten Selbstauskünfte oder Zugangsdaten.
