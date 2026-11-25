# Ajoute le clonage de VOTRE voix (Chatterbox Multilingual, Resemble AI, licence MIT, gratuit) a Coach Viral.
# A lancer apres l'installateur principal, dans PowerShell :
#   irm https://raw.githubusercontent.com/YoutubeVieira/autovid-ai/ccr-ee8a77f1-5c7kmx/coach-viral/installer/ajouter-chatterbox.ps1 | iex
# Avec une carte graphique NVIDIA : quelques secondes par phrase. Sans : ca marche, mais c'est lent (environ 1 minute par phrase).

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Racine = Join-Path $env:LOCALAPPDATA 'CoachViral'
$Venv = Join-Path $Racine 'python-chatterbox'
$Reglages = Join-Path $Racine 'config\reglages.json'

function Etape($texte) { Write-Host ''; Write-Host "==> $texte" -ForegroundColor Cyan }
function Ok($texte) { Write-Host "    $texte" -ForegroundColor Green }
function Info($texte) { Write-Host "    $texte" -ForegroundColor Gray }

if (-not (Test-Path $Reglages)) { throw "Installez d'abord Coach Viral (installer.ps1), puis relancez cette commande." }
$env:Path = $env:Path + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')

Write-Host ''
Write-Host '  Coach Viral - clonage de voix (Chatterbox)' -ForegroundColor Magenta

Etape '1/4  Carte graphique'
$gpu = $false
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  try { $nom = & cmd.exe /c "nvidia-smi --query-gpu=name --format=csv,noheader 2>&1"; $gpu = ($LASTEXITCODE -eq 0) } catch { $gpu = $false }
}
if ($gpu) { Ok "Carte NVIDIA detectee : $nom" ; $index = 'https://download.pytorch.org/whl/cu124' }
else { Info 'Pas de carte NVIDIA : version processeur (lente mais gratuite).'; $index = 'https://download.pytorch.org/whl/cpu' }

Etape '2/4  Environnement Python separe (Chatterbox a ses propres versions)'
$pyExe = Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path $pyExe)) {
  # Meme Python 3.12 que l'application (l'environnement principal connait son interpreteur de base).
  $base = & (Join-Path $Racine 'python\Scripts\python.exe') -c "import sys; print(sys._base_executable)"
  if ($LASTEXITCODE -ne 0 -or -not $base) { throw 'Python de Coach Viral introuvable : relancez d abord installer.ps1.' }
  & $base.Trim() -m venv $Venv
  if ($LASTEXITCODE -ne 0) { throw 'Creation de l environnement Python impossible.' }
}
& $pyExe -m pip install --upgrade pip --quiet
Ok 'Environnement pret'

Etape '3/4  Installation de Chatterbox (2 a 4 Go, 10 a 30 min)'
& $pyExe -m pip install --quiet torch==2.6.0 torchaudio==2.6.0 --index-url $index
if ($LASTEXITCODE -ne 0) { throw 'Installation de torch impossible.' }
& $pyExe -m pip install --quiet chatterbox-tts
if ($LASTEXITCODE -ne 0) { throw 'Installation de Chatterbox impossible.' }
Ok 'Chatterbox installe'

Etape '4/4  Telechargement du modele de voix (une seule fois)'
& $pyExe -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS as M; M.from_pretrained(device='cpu'); print('modele pret')"
if ($LASTEXITCODE -ne 0) { throw 'Telechargement du modele impossible (verifiez la connexion).' }

$r = Get-Content $Reglages -Raw | ConvertFrom-Json
$moteurs = @($r.voix -split ',' | Where-Object { $_ -and $_ -ne 'chatterbox' })
$r.voix = (@('chatterbox') + $moteurs) -join ','
$r | ConvertTo-Json | Set-Content $Reglages -Encoding UTF8
Ok "Moteurs de voix : $($r.voix)"

Write-Host ''
Write-Host '  Clonage de voix active !' -ForegroundColor Magenta
Write-Host '  Redemarrez Coach Viral (raccourci du Bureau), puis onglet Voix > Cloner ma voix.'
Write-Host '  Lisez la phrase affichee pendant 10 a 30 secondes, dans un endroit calme.'
