# Produit toutes les voix off de Second Souffle avec les voix choisies par défaut.
# Une seule chose à fournir : votre clé d'API Google (saisie masquée, jamais enregistrée).
# Lancement : double-clic sur Produire-les-voix.bat, ou
#   powershell -ExecutionPolicy Bypass -File tools\tout-faire.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Host "Node.js est introuvable. Installez-le avec : winget install OpenJS.NodeJS.LTS, puis rouvrez cette fenêtre."
  Read-Host "Appuyez sur Entrée pour fermer"; exit 1
}

Write-Host ""
Write-Host "Voix off Second Souffle"
Write-Host "  Modèle        : gemini-3.8-flash-tts (qualité maximale)"
Write-Host "  Voix de femme : Sulafat (bien-être : Vindemiatrix)"
Write-Host "  Voix d'homme  : Achird (bien-être : Charon)"
Write-Host "  Langues       : français, anglais, portugais du Brésil"
Write-Host "  Fichiers      : 822 (137 phrases x 3 langues x 2 voix), séances de bien-être assemblées"
Write-Host ""
Write-Host "Clé d'API Google : créez-la sur https://aistudio.google.com/apikey si vous n'en avez pas."
$secure = Read-Host "Collez votre clé (rien ne s'affiche), puis Entrée" -AsSecureString
$ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $env:GEMINI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) { Write-Host "Aucune clé saisie."; Read-Host "Appuyez sur Entrée pour fermer"; exit 1 }

Write-Host ""
Write-Host "Étape 1 : essai d'une phrase par langue, avec la voix de femme et la voix d'homme (6 fichiers)..."
node tools/generate-audio.js --test --out audio-essai
if ($LASTEXITCODE -ne 0) {
  Write-Host ""
  Write-Host "L'essai a échoué. Copiez le message ci-dessus (sans la clé) et envoyez-le à Claude."
  Read-Host "Appuyez sur Entrée pour fermer"; exit 1
}
Write-Host ""
Write-Host "Les six fichiers sont dans le dossier audio-essai (fr, en, pt ; dossiers f et m). Ouverture..."
Start-Process explorer.exe (Join-Path (Get-Location) "audio-essai")
$suite = Read-Host "Après écoute, la voix est-elle naturelle ? Produire les 822 fichiers maintenant (o/n)"
if ($suite -ne "o") {
  Write-Host "Arrêt. Dites à Claude ce qui ne va pas (voix, accent, rythme) : il changera les voix."
  Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
  Read-Host "Appuyez sur Entrée pour fermer"; exit 0
}

Write-Host ""
Write-Host "Étape 2 : production complète (quelques minutes). Un fichier déjà produit n'est pas refait."
node tools/generate-audio.js --lang all --out audio-out
$code = $LASTEXITCODE
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
Write-Host ""
if ($code -eq 0) {
  Write-Host "Terminé. Les fichiers sont dans le dossier audio-out. Ouverture..."
  Start-Process explorer.exe (Join-Path (Get-Location) "audio-out")
} else {
  Write-Host "La production s'est arrêtée. Relancez ce fichier : il reprend là où il s'est arrêté."
}
Read-Host "Appuyez sur Entrée pour fermer"
