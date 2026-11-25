# Demarre Coach Viral sur ce PC et le rend accessible depuis le telephone (adresse HTTPS gratuite Cloudflare).
# Fermer cette fenetre arrete l'application.

$ErrorActionPreference = 'Stop'
$Racine = Join-Path $env:LOCALAPPDATA 'CoachViral'
$App = Join-Path $Racine 'app'
$Config = Join-Path $Racine 'config'
$Logs = Join-Path $Racine 'journaux'
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links')

$r = Get-Content (Join-Path $Config 'reglages.json') -Raw | ConvertFrom-Json
$sec = Get-Content (Join-Path $Config 'cle-api.txt') | ConvertTo-SecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
try { $env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }

$env:CODE_ACCES = $r.code_acces
$env:VOIX_MOTEURS = $r.voix
$env:PORT = [string]$r.port
$env:PYTHON = Join-Path $Racine 'python\Scripts\python.exe'
$env:DOSSIER_DONNEES = Join-Path $Racine 'donnees'
$env:HOST = '127.0.0.1'

# Arrete une ancienne session restee ouverte (fenetre fermee avec la croix).
$pids = Join-Path $Racine 'processus.txt'
if (Test-Path $pids) {
  foreach ($id in Get-Content $pids) {
    $ancien = Get-Process -Id ([int]$id) -ErrorAction SilentlyContinue
    if ($ancien -and ($ancien.ProcessName -eq 'node' -or $ancien.ProcessName -eq 'cloudflared')) { Stop-Process -Id $ancien.Id -Force -ErrorAction SilentlyContinue }
  }
  Remove-Item $pids -Force
}
if ($r.radar_heure -ne '') { $env:RADAR_HEURE = [string]$r.radar_heure }
$local = "http://127.0.0.1:$($r.port)"

Write-Host ''
Write-Host '  Coach Viral demarre...' -ForegroundColor Magenta

$serveur = Start-Process node -ArgumentList '--no-warnings', 'server.mjs' -WorkingDirectory $App -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $Logs 'serveur.txt') -RedirectStandardError (Join-Path $Logs 'serveur-erreurs.txt')
$pret = $false
for ($i = 0; $i -lt 60 -and -not $pret; $i++) {
  Start-Sleep -Milliseconds 500
  try { $null = Invoke-RestMethod "$local/api/sante" -TimeoutSec 2; $pret = $true } catch { }
  if ($serveur.HasExited) { break }
}
if (-not $pret) {
  Write-Host '  Le serveur ne demarre pas. Erreurs :' -ForegroundColor Red
  Get-Content (Join-Path $Logs 'serveur-erreurs.txt') -Tail 20
  Read-Host '  Entree pour fermer'; exit 1
}
Write-Host "  Sur ce PC : $local" -ForegroundColor Green

Set-Content $pids $serveur.Id
$tunnelLog = Join-Path $Logs 'tunnel.txt'
if (Test-Path $tunnelLog) { Remove-Item $tunnelLog -Force }
$tunnel = Start-Process cloudflared -ArgumentList 'tunnel', '--no-autoupdate', '--url', $local -PassThru -WindowStyle Hidden -RedirectStandardError $tunnelLog
Add-Content $pids $tunnel.Id
$adresse = $null
for ($i = 0; $i -lt 60 -and -not $adresse; $i++) {
  Start-Sleep -Milliseconds 500
  if (Test-Path $tunnelLog) {
    $m = Select-String -Path $tunnelLog -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' | Select-Object -First 1
    if ($m) { $adresse = $m.Matches[0].Value }
  }
}

Write-Host ''
if ($adresse) {
  Set-Clipboard $adresse
  Write-Host '  Sur le telephone, ouvrez :' -ForegroundColor Yellow
  Write-Host "     $adresse" -ForegroundColor White
  Write-Host '     (copiee dans le presse-papiers ; elle change a chaque demarrage)' -ForegroundColor Gray
} else {
  Write-Host "  Adresse telephone indisponible (tunnel Cloudflare). L'application marche sur ce PC." -ForegroundColor Yellow
}
Write-Host "  Code d'acces (Reglages > Code d'acces) : $($r.code_acces)" -ForegroundColor Yellow
Write-Host ''
Start-Process $local

Write-Host '  Laissez cette fenetre ouverte. Appuyez sur Entree pour arreter Coach Viral.' -ForegroundColor Gray
$null = Read-Host
foreach ($p in $tunnel, $serveur) { if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } }
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item $pids -Force -ErrorAction SilentlyContinue
Write-Host '  Arrete.'
