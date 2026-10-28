# Assistant Windows pour produire les voix off de Second Souffle.
# Lancer depuis le dossier second-souffle-pwa :
#   powershell -ExecutionPolicy Bypass -File tools\generer-audio.ps1
# La clé d'API est demandée en saisie masquée. Elle n'est écrite dans aucun fichier
# et n'existe que dans cette fenêtre PowerShell.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Host "Node.js est introuvable. Installez-le avec : winget install OpenJS.NodeJS.LTS, puis rouvrez PowerShell."
  exit 1
}

Write-Host ""
Write-Host "Voix off Second Souffle : 822 fichiers (137 phrases × 3 langues × voix de femme et d'homme), séances de bien-être assemblées."
Write-Host ""
Write-Host "1) Essai sans clé (vérifie le découpage, produit des sons de test)"
Write-Host "2) Production réelle avec le service de voix de Google (une voix de femme et une voix d'homme)"
Write-Host "3) Écouter plusieurs voix sur la même phrase, dans les trois langues"
$choix = Read-Host "Votre choix (1, 2 ou 3)"

if ($choix -eq "1") {
  node tools/generate-audio.js --dry-run --lang all --out audio-essai
  Write-Host "Terminé. Les fichiers de test sont dans le dossier audio-essai."
  exit 0
}

if ($choix -eq "3") { $audition = $true }
$secure = Read-Host "Clé d'API Google (AI Studio), saisie masquée" -AsSecureString
$ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $env:GEMINI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }

$modele = Read-Host "Identifiant du modèle de voix (Entrée pour gemini-3.8-flash-lite-tts)"
if ([string]::IsNullOrWhiteSpace($modele)) { $modele = "gemini-3.8-flash-lite-tts" }
$env:TTS_MODEL = $modele
if ($audition) {
  Write-Host ""
  Write-Host "Voix comparées : Achird, Sadaltager, Orus, Charon, Puck (masculines) ; Sulafat, Vindemiatrix, Achernar, Kore, Aoede, Gacrux, Leda (féminines)."
  Write-Host "Pour en comparer d'autres, tapez leurs noms séparés par des virgules, sinon appuyez sur Entrée."
  $autres = Read-Host "Voix à comparer"
  if (-not [string]::IsNullOrWhiteSpace($autres)) { $env:AUDITION_VOICES = $autres }
  node tools/generate-audio.js --audition --out audio-voix
  Write-Host ""
  Write-Host "Écoutez les fichiers voix-*.wav dans les dossiers audio-voix\fr, audio-voix\en et audio-voix\pt."
  Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
  exit 0
}
$vf = Read-Host "Voix de femme (Entrée pour Sulafat)"
if ([string]::IsNullOrWhiteSpace($vf)) { $vf = "Sulafat" }
$vm = Read-Host "Voix d'homme (Entrée pour Achird)"
if ([string]::IsNullOrWhiteSpace($vm)) { $vm = "Achird" }
$env:VOICE_F = $vf
$env:VOICE_M = $vm
Write-Host "Ces deux voix parleront dans les trois langues (français, anglais, portugais du Brésil)."
$bf = Read-Host "Autre voix de femme pour les séances de bien-être (Entrée pour garder $vf)"
if (-not [string]::IsNullOrWhiteSpace($bf)) { $env:VOICE_WELLNESS_F = $bf }
$bm = Read-Host "Autre voix d'homme pour les séances de bien-être (Entrée pour garder $vm)"
if (-not [string]::IsNullOrWhiteSpace($bm)) { $env:VOICE_WELLNESS_M = $bm }

Write-Host ""
Write-Host "Essai d'une phrase par langue, avec la voix de femme et la voix d'homme (6 fichiers)..."
node tools/generate-audio.js --test --out audio-essai
if ($LASTEXITCODE -ne 0) { Write-Host "L'essai a échoué. Copiez le message ci-dessus et envoyez-le moi."; exit 1 }
Write-Host ""
Write-Host "Écoutez les six fichiers dans audio-essai (fr, en, pt, chacun dans les dossiers f et m)."
$suite = Read-Host "Les voix vous conviennent ? Produire les 822 fichiers maintenant (o/n)"
if ($suite -ne "o") { Write-Host "Arrêt. Relancez le script quand vous aurez choisi vos voix."; exit 0 }

node tools/generate-audio.js --lang all --out audio-out
Write-Host ""
Write-Host "Terminé. Les fichiers sont dans le dossier audio-out. Écoutez-les avant de les utiliser."
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
