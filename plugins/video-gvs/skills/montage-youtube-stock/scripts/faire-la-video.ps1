# Fabrique la vidéo YouTube : voix off Gemini + clips Pexels / Pixabay + sous-titres.
# Les clés sont tapées en saisie masquée, gardées seulement le temps du montage, jamais enregistrées.
# Lancement : double-clic sur Faire-la-video.bat

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Fin($code) { Read-Host "Appuyez sur Entrée pour fermer"; exit $code }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "Python est introuvable. Installez-le avec : winget install Python.Python.3.12, puis rouvrez cette fenêtre."; Fin 1
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Host "ffmpeg est introuvable. Installez-le avec : winget install Gyan.FFmpeg, puis rouvrez cette fenêtre."; Fin 1
}

function Lire-Cle($nom, $texte) {
  if (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($nom))) { return }
  $s = Read-Host $texte -AsSecureString
  $p = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
  try { [Environment]::SetEnvironmentVariable($nom, [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($p), "Process") }
  finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($p) }
}

$scripts = Get-ChildItem videos\*.json
Write-Host ""
Write-Host "Vidéos disponibles :"
for ($i = 0; $i -lt $scripts.Count; $i++) { Write-Host ("  " + ($i + 1) + ". " + $scripts[$i].BaseName) }
$n = Read-Host "Numéro de la vidéo (Entrée = 1)"
if ([string]::IsNullOrWhiteSpace($n)) { $n = 1 }
$script = $scripts[[int]$n - 1].FullName

Write-Host ""
Write-Host "Clés gratuites : https://www.pexels.com/api/  et  https://pixabay.com/api/docs/"
Write-Host "Laissez vide (Entrée) une banque que vous n'utilisez pas."
Lire-Cle "PEXELS_API_KEY"  "Clé Pexels (rien ne s'affiche)"
Lire-Cle "PIXABAY_API_KEY" "Clé Pixabay (rien ne s'affiche)"
Lire-Cle "GEMINI_API_KEY"  "Clé Google pour la voix off (rien ne s'affiche)"

$args2 = @("montage.py", $script)
$musique = Read-Host "Musique de fond : glissez le fichier ici, ou Entrée pour aucune"
$musique = $musique.Trim('"', ' ')
if ($musique) { $args2 += @("--music", $musique) }

Write-Host ""
python @args2
$code = $LASTEXITCODE
Remove-Item Env:PEXELS_API_KEY, Env:PIXABAY_API_KEY, Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
Write-Host ""
if ($code -eq 0) {
  Write-Host "Terminé. Ouverture du dossier..."
  Start-Process explorer.exe (Join-Path $PSScriptRoot "build")
} else {
  Write-Host "Le montage s'est arrêté. Relancez : ce qui est déjà fait est conservé. Sinon, copiez le message (sans les clés) à Claude."
}
Fin $code
