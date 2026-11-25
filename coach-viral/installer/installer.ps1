# Installateur de Coach Viral pour Windows 10 / 11.
# A coller dans PowerShell (pas besoin d'etre administrateur) :
#   irm https://raw.githubusercontent.com/YoutubeVieira/autovid-ai/ccr-ee8a77f1-5c7kmx/coach-viral/installer/installer.ps1 | iex
# Relancer la meme commande met l'application a jour (vos reglages, votre voix et vos videos sont gardes).

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
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links')
}
function Winget-Installer($id, $nom) {
  Info "Installation de $nom (quelques minutes)..."
  winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity | Out-Null
  Actualiser-Path
}

Write-Host ''
Write-Host '  Coach Viral - installation' -ForegroundColor Magenta
Write-Host '  ---------------------------'

# 1. Outils
Etape '1/6  Outils necessaires'
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  throw "winget est introuvable. Installez 'App Installer' depuis le Microsoft Store, puis relancez."
}
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

$py312 = $false
if (Get-Command py -ErrorAction SilentlyContinue) {
  try { $out = & cmd.exe /c "py -3.12 --version 2>&1"; $py312 = ($LASTEXITCODE -eq 0) } catch { $py312 = $false }
}
if (-not $py312) { Winget-Installer 'Python.Python.3.12' 'Python 3.12' } else { Ok 'Python 3.12 present' }

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
  $py312Exe = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
  if (Get-Command py -ErrorAction SilentlyContinue) { & py -3.12 -m venv $Py }
  elseif (Test-Path $py312Exe) { & $py312Exe -m venv $Py }
  else { throw 'Python 3.12 introuvable. Fermez PowerShell, rouvrez-le et relancez la commande.' }
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
$cleFichier = Join-Path $Config 'cle-api.txt'
if (-not (Test-Path $cleFichier)) {
  Write-Host '    Collez votre cle API Claude (console.anthropic.com > API Keys). Elle reste chiffree sur ce PC.' -ForegroundColor Yellow
  $sec = Read-Host '    Cle API' -AsSecureString
  $sec | ConvertFrom-SecureString | Set-Content $cleFichier
} else { Ok 'Cle API deja enregistree (supprimez config\cle-api.txt pour la changer)' }

$reglages = Join-Path $Config 'reglages.json'
if (-not (Test-Path $reglages)) {
  $code = -join ((48..57) + (97..122) | Get-Random -Count 8 | ForEach-Object { [char]$_ })
  @{ code_acces = $code; voix = 'kokoro,edge'; port = 8080; radar_heure = '' } | ConvertTo-Json | Set-Content $reglages -Encoding UTF8
  Ok "Code d'acces cree : $code (a saisir dans Reglages sur le telephone)"
} else { Ok 'Reglages gardes' }

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
Ok 'Raccourci "Coach Viral" cree sur le Bureau'

Write-Host ''
Write-Host '  Installation terminee !' -ForegroundColor Magenta
Write-Host '  Double-cliquez sur "Coach Viral" sur le Bureau pour demarrer.'
Write-Host ''
$rep = Read-Host '  Demarrer maintenant ? (O/n)'
if ($rep -ne 'n' -and $rep -ne 'N') { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Racine 'lancer.ps1') }
