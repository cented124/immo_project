$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop fehlt. Bitte Docker Desktop installieren und danach STARTEN erneut starten.' }
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Bitte Docker Desktop oeffnen und warten, bis Docker bereit ist. Danach STARTEN erneut oeffnen.' }
if (-not (Test-Path '.env')) {
  $rng=[System.Security.Cryptography.RandomNumberGenerator]::Create()
  function New-Secret { $bytes=New-Object byte[] 32; $rng.GetBytes($bytes); return [Convert]::ToBase64String($bytes).Replace('+','-').Replace('/','_') }
  $databasePassword=(New-Secret).TrimEnd('=')
  $encryptionKey=New-Secret
  $content="POSTGRES_PASSWORD=$databasePassword`nDATABASE_URL=postgresql+psycopg://raumwerk:${databasePassword}@db:5432/raumwerk`nENCRYPTION_KEY=$encryptionKey`nDATA_DIR=/data`nPUBLIC_ORIGIN=http://localhost:3000`nCOOKIE_SECURE=0`nAPI_INTERNAL_URL=http://api:8000`nDELIVERY_WORKER=1`n"
  [System.IO.File]::WriteAllText((Join-Path (Get-Location) '.env'),$content,(New-Object System.Text.UTF8Encoding($false)))
  $rng.Dispose()
}
Write-Host 'Die Anwendung wird vorbereitet. Beim ersten Start kann das einige Minuten dauern.'
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Der Start ist fehlgeschlagen. Bitte die angezeigte Fehlermeldung fuer die Fehlersuche aufbewahren. Keine Passwoerter weitergeben.' }
docker compose exec -T api python -m app.cli admin-exists
if ($LASTEXITCODE -eq 10) {
  Write-Host 'Erste Einrichtung: Legen Sie jetzt Ihr eigenes Administratorkonto an.'
  $email=Read-Host 'Ihre E-Mail-Adresse fuer den Adminzugang'
  docker compose exec api python -m app.cli create-admin --email "$email"
  if ($LASTEXITCODE -ne 0) { throw 'Das Administratorkonto wurde nicht erstellt. STARTEN erneut oeffnen und die Einrichtung wiederholen.' }
} elseif ($LASTEXITCODE -ne 0) { throw 'Die Kontoeinrichtung konnte nicht geprueft werden.' }
Write-Host 'Startbereit. Der Browser wird geoeffnet. Fuer spaetere Starts genuegt STARTEN.cmd.'
Start-Process 'http://localhost:3000/admin'
