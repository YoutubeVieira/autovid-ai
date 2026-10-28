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
Write-Host "Voix off Second Souffle : 411 fichiers (137 par langue), séances de bien-être assemblées."
Write-Host ""
Write-Host "1) Essai sans clé (vérifie le découpage, produit des sons de test)"
Write-Host "2) Production réelle avec le service de voix de Google"
$choix = Read-Host "Votre choix (1 ou 2)"

if ($choix -eq "1") {
  node tools/generate-audio.js --dry-run --lang all --out audio-essai
  Write-Host "Terminé. Les fichiers de test sont dans le dossier audio-essai."
  exit 0
}

$secure = Read-Host "Clé d'API Google (AI Studio), saisie masquée" -AsSecureString
$ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $env:GEMINI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }

$env:TTS_MODEL = Read-Host "Identifiant du modèle de voix (à copier depuis la documentation Google)"
$env:VOICE_FR = Read-Host "Nom de la voix en français"
$env:VOICE_EN = Read-Host "Nom de la voix en anglais"
$env:VOICE_PT = Read-Host "Nom de la voix en portugais du Brésil"

Write-Host ""
Write-Host "Essai d'une phrase par langue..."
node tools/generate-audio.js --test --out audio-essai
if ($LASTEXITCODE -ne 0) { Write-Host "L'essai a échoué. Copiez le message ci-dessus et envoyez-le moi."; exit 1 }
Write-Host ""
Write-Host "Écoutez les trois fichiers dans le dossier audio-essai (fr, en, pt)."
$suite = Read-Host "Les voix vous conviennent ? Produire les 411 fichiers maintenant (o/n)"
if ($suite -ne "o") { Write-Host "Arrêt. Relancez le script quand vous aurez choisi vos voix."; exit 0 }

node tools/generate-audio.js --lang all --out audio-out
Write-Host ""
Write-Host "Terminé. Les fichiers sont dans le dossier audio-out. Écoutez-les avant de les utiliser."
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
