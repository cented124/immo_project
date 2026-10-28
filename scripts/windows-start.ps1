param(
  [ValidateSet('start','prepare','stop','diagnose','repair','backup')][string]$Action = 'start',
  [switch]$NoBrowser,
  [switch]$NoDelivery
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $root
$runtime = Join-Path $root '.runtime'
$python = Join-Path $runtime 'python\python.exe'
$controller = Join-Path $PSScriptRoot 'desktop.py'
$lock = $null

function Invoke-Desktop([string]$Command) {
  $arguments = @('-X','utf8',$controller,$Command)
  if ($NoBrowser) { $arguments += '--no-browser' }
  if ($NoDelivery) { $arguments += '--no-delivery' }
  & $python @arguments
  if ($LASTEXITCODE -ne 0) { throw 'Der Schritt konnte nicht abgeschlossen werden. Bitte die Meldung oben und DIAGNOSE.cmd pruefen.' }
}

function Protect-LocalFolder([string]$Folder) {
  [System.IO.Directory]::CreateDirectory($Folder) | Out-Null
  $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
  $acl = New-Object System.Security.AccessControl.DirectorySecurity
  $acl.SetOwner($identity)
  $acl.SetAccessRuleProtection($true,$false)
  foreach ($sid in @($identity,(New-Object System.Security.Principal.SecurityIdentifier('S-1-5-18')),(New-Object System.Security.Principal.SecurityIdentifier('S-1-5-32-544')))) {
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule)
  }
  Set-Acl -LiteralPath $Folder -AclObject $acl
}

function Get-VerifiedAsset($Asset) {
  $uri = [Uri]$Asset.url
  if ($uri.Scheme -ne 'https' -or $Asset.sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Das Runtime-Manifest ist ungueltig.' }
  $cache = Join-Path $runtime 'downloads'
  [System.IO.Directory]::CreateDirectory($cache) | Out-Null
  $destination = Join-Path $cache $Asset.file
  if ((Test-Path -LiteralPath $destination) -and (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -eq $Asset.sha256) { return $destination }
  $temporary = $destination + '.partial'
  Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
  Write-Host ('Lade geprueftes Laufzeitpaket: ' + $Asset.file)
  try {
    Invoke-WebRequest -UseBasicParsing -Uri $Asset.url -OutFile $temporary -TimeoutSec 600
    if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Asset.sha256) { throw 'Pruefsumme stimmt nicht. Der Download wird nicht ausgefuehrt.' }
    Move-Item -LiteralPath $temporary -Destination $destination -Force
  } finally { Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue }
  return $destination
}

function Test-Runtime([string]$Directory,[string]$Signature,[string]$Executable) {
  $marker = Join-Path $Directory 'installed.json'
  $exe = Join-Path $Directory $Executable
  try {
    if (-not (Test-Path -LiteralPath $marker) -or -not (Test-Path -LiteralPath $exe)) { return $false }
    $data = Get-Content -LiteralPath $marker -Raw -Encoding UTF8 | ConvertFrom-Json
    return $data.signature -eq $Signature -and $data.exe_sha256 -eq (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
  } catch { return $false }
}

function Save-RuntimeMarker([string]$Directory,[string]$Signature,[string]$Executable) {
  $data = @{signature=$Signature;exe_sha256=(Get-FileHash -LiteralPath (Join-Path $Directory $Executable) -Algorithm SHA256).Hash.ToLowerInvariant()}
  [System.IO.File]::WriteAllText((Join-Path $Directory 'installed.json'),($data | ConvertTo-Json),(New-Object System.Text.UTF8Encoding($false)))
}

function Install-Runtimes {
  $manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-runtime.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $nodeDirectory = Join-Path $runtime 'node'
  $pythonDirectory = Join-Path $runtime 'python'
  $requirements = Join-Path $root 'backend\requirements-windows.lock'
  $backendHash = (Get-FileHash -LiteralPath $requirements -Algorithm SHA256).Hash.ToLowerInvariant()
  $pythonSignature = $manifest.python.sha256 + ':' + $manifest.pip.sha256 + ':' + $backendHash
  $force = $Action -eq 'repair'
  [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::Tls12
  Add-Type -AssemblyName System.IO.Compression.FileSystem

  if ($force -or -not (Test-Runtime $nodeDirectory $manifest.node.sha256 'node.exe')) {
    $archive = Get-VerifiedAsset $manifest.node
    $stage = Join-Path $runtime ('node-install-' + [Guid]::NewGuid().ToString('N'))
    try {
      [System.IO.Compression.ZipFile]::ExtractToDirectory($archive,$stage)
      $unpacked = Join-Path $stage ('node-v' + $manifest.node.version + '-win-x64')
      Save-RuntimeMarker $unpacked $manifest.node.sha256 'node.exe'
      if (Test-Path -LiteralPath $nodeDirectory) { Remove-Item -LiteralPath $nodeDirectory -Recurse -Force }
      Move-Item -LiteralPath $unpacked -Destination $nodeDirectory
    } finally { if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force } }
  }
  if ($force -or -not (Test-Runtime $pythonDirectory $pythonSignature 'python.exe')) {
    $archive = Get-VerifiedAsset $manifest.python
    $pipArchive = Get-VerifiedAsset $manifest.pip
    $stage = Join-Path $runtime ('python-install-' + [Guid]::NewGuid().ToString('N'))
    try {
      [System.IO.Compression.ZipFile]::ExtractToDirectory($archive,$stage)
      $site = Join-Path $stage 'Lib\site-packages'
      [System.IO.Directory]::CreateDirectory($site) | Out-Null
      [System.IO.Compression.ZipFile]::ExtractToDirectory($pipArchive,$site)
      $pth = @(Get-ChildItem -LiteralPath $stage -Filter 'python*._pth')
      if ($pth.Count -ne 1) { throw 'Unerwartetes Python-Paketformat.' }
      $stdlib = @(Get-ChildItem -LiteralPath $stage -Filter 'python*.zip')
      if ($stdlib.Count -ne 1) { throw 'Python-Standardbibliothek fehlt.' }
      [System.IO.File]::WriteAllText($pth[0].FullName,($stdlib[0].Name + "`r`n.`r`nLib\site-packages`r`n..\..\backend`r`n..\..\scripts`r`nimport site`r`n"),[System.Text.Encoding]::ASCII)
      $stagePython = Join-Path $stage 'python.exe'
      Write-Host 'Installiere die festgelegten Backend-Pakete (ohne Compiler und ohne Docker).'
      $log = Join-Path $runtime 'logs\backend-install.log'
      & $stagePython -X utf8 -m pip --isolated install --no-user --require-hashes --only-binary=:all: --disable-pip-version-check --no-warn-script-location --no-cache-dir -r $requirements *> $log
      if ($LASTEXITCODE -ne 0) { throw 'Backend-Einrichtung fehlgeschlagen. Details: .runtime/logs/backend-install.log. Internetverbindung pruefen und REPARIEREN.cmd erneut versuchen.' }
      & $stagePython -X utf8 -c 'import fastapi,uvicorn,sqlalchemy,alembic,cryptography,argon2,PIL,httpx'
      if ($LASTEXITCODE -ne 0) { throw 'Backend-Pruefung fehlgeschlagen.' }
      Save-RuntimeMarker $stage $pythonSignature 'python.exe'
      if (Test-Path -LiteralPath $pythonDirectory) { Remove-Item -LiteralPath $pythonDirectory -Recurse -Force }
      Move-Item -LiteralPath $stage -Destination $pythonDirectory
    } finally { if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force } }
  }
}

try {
  if ($root.StartsWith('\\')) { throw 'Bitte den Baukasten in einen lokalen Ordner entpacken, nicht auf ein Netzlaufwerk.' }
  if (-not [Environment]::Is64BitOperatingSystem) { throw 'Dieses Paket benoetigt Windows 10/11 mit 64 Bit (x64).' }
  $architecture = $env:PROCESSOR_ARCHITECTURE
  if ($env:PROCESSOR_ARCHITEW6432) { $architecture = $env:PROCESSOR_ARCHITEW6432 }
  if ($architecture -ne 'AMD64') { throw 'Dieses Paket ist fuer Windows x64. Eine ARM-Version ist nicht enthalten.' }
  [System.IO.Directory]::CreateDirectory($runtime) | Out-Null
  foreach ($folder in @((Join-Path $root 'DATEN'),(Join-Path $runtime 'control'),(Join-Path $runtime 'logs'))) { Protect-LocalFolder $folder }
  if ($Action -eq 'backup') { Protect-LocalFolder (Join-Path $root 'SICHERUNGEN') }
  if ($Action -in @('stop','diagnose','backup')) {
    if (-not (Test-Path -LiteralPath $python)) {
      if ($Action -eq 'stop') { Write-Host 'Noch keine lokale Installation gestartet.'; exit 0 }
      throw 'Die Laufzeit ist noch nicht eingerichtet. Bitte zuerst STARTEN.cmd verwenden. Vorhandene Daten bleiben im Ordner DATEN.'
    }
    Invoke-Desktop $Action
    exit 0
  }
  $lockPath = Join-Path $runtime 'control\bootstrap.lock'
  try { $lock = [System.IO.File]::Open($lockPath,'OpenOrCreate','ReadWrite','None') }
  catch { throw 'Eine Einrichtung laeuft bereits. Bitte das erste Startfenster abwarten.' }
  if ($Action -eq 'repair' -and (Test-Path -LiteralPath $python)) { Invoke-Desktop 'stop' }
  if ((Get-PSDrive -Name ([System.IO.Path]::GetPathRoot($root).Substring(0,1))).Free -lt 2GB) { throw 'Bitte mindestens 2 GB freien Speicher fuer die erste Einrichtung bereitstellen.' }
  Install-Runtimes
  if ($Action -eq 'repair') {
    Get-ChildItem -LiteralPath $runtime -Directory -Filter 'web-*' | Where-Object { $_.Name -match '^web-(build-)?[a-f0-9]{12,16}$' } | Remove-Item -Recurse -Force
  }
  if ($Action -eq 'prepare') { Invoke-Desktop 'prepare' }
  else { Invoke-Desktop 'launch' }
} catch {
  Write-Host ''
  Write-Host ('Fehler: ' + $_.Exception.Message) -ForegroundColor Red
  Write-Host 'Keine Daten wurden geloescht. Bitte DIAGNOSE.cmd oder REPARIEREN.cmd verwenden.'
  exit 1
} finally { if ($lock) { $lock.Dispose() } }
