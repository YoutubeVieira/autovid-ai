# Vérifie que votre clé d'API Google accepte les modèles de voix. Rien n'est produit, la clé n'est pas enregistrée.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Write-Host "Node.js est introuvable."; Read-Host "Entrée pour fermer"; exit 1 }
Write-Host "Créez ou retrouvez votre clé sur https://aistudio.google.com/apikey"
$secure = Read-Host "Collez votre clé (rien ne s'affiche), puis Entrée" -AsSecureString
$ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $env:GEMINI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
Write-Host ""
node tools/verifier-cle.js
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
Write-Host ""
Read-Host "Appuyez sur Entrée pour fermer"
