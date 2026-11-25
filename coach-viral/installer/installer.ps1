# Installateur de Coach Viral pour Windows 10 / 11.
# A coller dans PowerShell (pas besoin d'etre administrateur) :
#   irm https://raw.githubusercontent.com/YoutubeVieira/autovid-ai/ccr-ee8a77f1-5c7kmx/coach-viral/installer/installer.ps1 | iex
# Relancer la meme commande met l'application a jour (vos reglages, votre voix et vos videos sont gardes).
# Mode sans questions (robot de test) : COACH_IA=gemini|claude, COACH_CLE=..., COACH_DEMARRER=non.

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Depot = 'YoutubeVieira/autovid-ai'
$Branche = 'ccr-ee8a77f1-5c7kmx'
$Racine = Join-Path $env:LOCALAPPDATA 'CoachViral'
$App = Join-Path $Racine 'app'
$Py = Join-Path $Racine 'python'
$Config = Join-Path $Racine 'config'

function Etape($texte) { Write-Host ''; Write-Host "==> $texte" -ForegroundColor Cyan }
function Ok($texte) { Write-Host "    $texte" -ForegroundColor Green }
function Info($texte) { Write-Host "    $texte" -ForegroundColor Gray }
function Actualiser-Path {
  $env:Path = $env:Path + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links')
}
function Winget-Installer($id, $nom) {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "$nom manque et winget est introuvable. Installez 'App Installer' depuis le Microsoft Store, puis relancez."
  }
  Info "Installation de $nom (quelques minutes)..."
  winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity | Out-Null
  Actualiser-Path
}

Write-Host ''
Write-Host '  Coach Viral - installation' -ForegroundColor Magenta
Write-Host '  ---------------------------'

# 1. Outils
Etape '1/6  Outils necessaires'
Actualiser-Path

$nodeOk = $false
if (Get-Command node -ErrorAction SilentlyContinue) {
  $v = (node --version).TrimStart('v').Split('.')
  $nodeOk = ([int]$v[0] -gt 22) -or ([int]$v[0] -eq 22 -and [int]$v[1] -ge 5)
}
if (-not $nodeOk) {
  Winget-Installer 'OpenJS.NodeJS.LTS' 'Node.js'
  winget upgrade --id OpenJS.NodeJS.LTS -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity | Out-Null
  Actualiser-Path
} else { Ok 'Node.js present' }

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Winget-Installer 'Gyan.FFmpeg' 'FFmpeg' } else { Ok 'FFmpeg present' }

# Trouve un python.exe 3.12 : lanceur py, dossier habituel, ou python du PATH.
function Trouver-Python312 {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    try { $p = & cmd.exe /c "py -3.12 -c ""import sys; print(sys.executable)"" 2>nul"; if ($LASTEXITCODE -eq 0 -and $p) { return ($p | Select-Object -First 1).Trim() } } catch { }
  }
  $habituel = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
  if (Test-Path $habituel) { return $habituel }
  foreach ($c in Get-Command python -All -ErrorAction SilentlyContinue) {
    try { $v = & cmd.exe /c """$($c.Source)"" --version 2>&1"; if ("$v" -match 'Python 3\.12\.') { return $c.Source } } catch { }
  }
  return $null
}
if (-not (Trouver-Python312)) { Winget-Installer 'Python.Python.3.12' 'Python 3.12' } else { Ok 'Python 3.12 present' }

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) { Winget-Installer 'Cloudflare.cloudflared' 'Cloudflare Tunnel' } else { Ok 'Cloudflare Tunnel present' }

foreach ($c in 'node', 'ffmpeg', 'cloudflared') {
  if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { throw "$c n'est pas accessible. Fermez PowerShell, rouvrez-le et relancez la commande." }
}

# 2. Application
Etape "2/6  Telechargement de l'application"
$zip = Join-Path $env:TEMP 'coach-viral.zip'
$tmp = Join-Path $env:TEMP 'coach-viral-extrait'
Invoke-WebRequest "https://github.com/$Depot/archive/refs/heads/$Branche.zip" -OutFile $zip -UseBasicParsing
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive $zip -DestinationPath $tmp -Force
$source = Get-ChildItem $tmp -Directory | Select-Object -First 1
New-Item -ItemType Directory -Force -Path $Racine, $Config, (Join-Path $Racine 'donnees') | Out-Null
if (Test-Path $App) { Remove-Item $App -Recurse -Force }
Copy-Item (Join-Path $source.FullName 'coach-viral') $App -Recurse
Remove-Item $zip, $tmp -Recurse -Force
Ok "Installee dans $App"

# 3. Modules Node
Etape '3/6  Modules de l application'
Push-Location $App
& npm.cmd ci --omit=dev --no-audit --no-fund --loglevel=error
if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'npm ci a echoue.' }
Pop-Location
Ok 'Modules installes'

# 4. Outils Python gratuits : voix Kokoro, transcription, telechargement, voix Edge
Etape '4/6  Voix et transcription (gros telechargement la premiere fois, 10 a 20 min)'
$pyExe = Join-Path $Py 'Scripts\python.exe'
if (-not (Test-Path $pyExe)) {
  $py312Exe = Trouver-Python312
  if (-not $py312Exe) { throw 'Python 3.12 introuvable. Fermez PowerShell, rouvrez-le et relancez la commande.' }
  & $py312Exe -m venv $Py
  if ($LASTEXITCODE -ne 0) { throw 'Creation de l environnement Python impossible.' }
}
& $pyExe -m pip install --upgrade pip --quiet
& $pyExe -m pip install --quiet --extra-index-url https://download.pytorch.org/whl/cpu torch
& $pyExe -m pip install --quiet --upgrade soundfile faster-whisper yt-dlp edge-tts espeakng-loader
if ($LASTEXITCODE -ne 0) { throw 'Installation des outils Python impossible.' }
Ok 'Whisper, yt-dlp et voix Edge installes'
& $pyExe -m pip install --quiet --upgrade kokoro
if ($LASTEXITCODE -eq 0) { Ok 'Voix Kokoro installee' } else { Info 'Kokoro non installe : les voix Edge restent disponibles.' }

# 5. Reglages
Etape '5/6  Reglages'
$reglages = Join-Path $Config 'reglages.json'
$ia = 'gemini'
if (Test-Path $reglages) {
  $ancien = Get-Content $reglages -Raw | ConvertFrom-Json
  if ($ancien.ia) { $ia = $ancien.ia } elseif (Test-Path (Join-Path $Config 'cle-api.txt')) { $ia = 'claude' }
} elseif ($env:COACH_IA) {
  $ia = $env:COACH_IA
} else {
  Write-Host '    Quelle IA utiliser ?' -ForegroundColor Yellow
  Write-Host '      1 = Gemini de Google : GRATUIT (cle gratuite sur aistudio.google.com) - recommande'
  Write-Host '      2 = Claude : payant a l usage (console.anthropic.com), reponses souvent meilleures'
  $choix = Read-Host '    Votre choix (1 ou 2)'
  if ($choix -eq '2') { $ia = 'claude' }
}
if ($ia -eq 'gemini') { $cleFichier = Join-Path $Config 'cle-gemini.txt'; $ou = 'aistudio.google.com > Get API key' }
else { $cleFichier = Join-Path $Config 'cle-api.txt'; $ou = 'console.anthropic.com > API Keys' }
if (-not (Test-Path $cleFichier) -and $env:COACH_CLE) {
  ConvertTo-SecureString $env:COACH_CLE -AsPlainText -Force | ConvertFrom-SecureString | Set-Content $cleFichier
  Ok 'Cle enregistree (mode automatique)'
} elseif (-not (Test-Path $cleFichier)) {
  Write-Host "    Collez votre cle API ($ou). Clic droit pour coller. Elle reste chiffree sur ce PC." -ForegroundColor Yellow
  $sec = Read-Host '    Cle API' -AsSecureString
  $sec | ConvertFrom-SecureString | Set-Content $cleFichier
} else { Ok "Cle deja enregistree (supprimez $cleFichier pour la changer)" }

if (-not (Test-Path $reglages)) {
  $code = -join ((48..57) + (97..122) | Get-Random -Count 8 | ForEach-Object { [char]$_ })
  @{ ia = $ia; code_acces = $code; voix = 'kokoro,edge'; port = 8080; radar_heure = '' } | ConvertTo-Json | Set-Content $reglages -Encoding UTF8
  Ok "Code d'acces cree : $code (a saisir dans Reglages sur le telephone)"
} else {
  $r = Get-Content $reglages -Raw | ConvertFrom-Json
  if (-not $r.ia) { $r | Add-Member -NotePropertyName ia -NotePropertyValue $ia; $r | ConvertTo-Json | Set-Content $reglages -Encoding UTF8 }
  Ok "Reglages gardes (IA : $ia)"
}

# 6. Raccourci
Etape '6/6  Raccourci sur le Bureau'
Copy-Item (Join-Path $App 'installer\lancer.ps1') (Join-Path $Racine 'lancer.ps1') -Force
$bureau = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut((Join-Path $bureau 'Coach Viral.lnk'))
$lnk.TargetPath = (Get-Command powershell.exe).Source
$lnk.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $Racine 'lancer.ps1') + '"'
$lnk.WorkingDirectory = $Racine
$lnk.IconLocation = (Get-Command node).Source + ',0'
$lnk.Save()
$maj = $ws.CreateShortcut((Join-Path $bureau 'Mettre a jour Coach Viral.lnk'))
$maj.TargetPath = (Get-Command powershell.exe).Source
$maj.Arguments = '-NoProfile -ExecutionPolicy Bypass -NoExit -Command "irm https://raw.githubusercontent.com/' + $Depot + '/' + $Branche + '/coach-viral/installer/installer.ps1 | iex"'
$maj.WorkingDirectory = $Racine
$maj.Save()
Ok 'Raccourcis "Coach Viral" et "Mettre a jour Coach Viral" crees sur le Bureau'

Write-Host ''
Write-Host '  Installation terminee !' -ForegroundColor Magenta
Write-Host '  Double-cliquez sur "Coach Viral" sur le Bureau pour demarrer.'
Write-Host ''
if ($env:COACH_DEMARRER -eq 'non') { return }
$rep = Read-Host '  Demarrer maintenant ? (O/n)'
if ($rep -ne 'n' -and $rep -ne 'N') { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Racine 'lancer.ps1') }
