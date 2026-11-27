# Néon Bay : fabrique le fichier .aab signé sous Windows (sans passer par les menus d'Android Studio).
# Les fichiers du jeu sont DÉJÀ copiés dans android\app\src\main\assets\public : Node.js n'est pas nécessaire.
#
# Utilisation (PowerShell, dans le dossier app-android) :
#   powershell -ExecutionPolicy Bypass -File .\build-android.ps1 -NewKey   # 1re fois : crée la clé d'importation
#   powershell -ExecutionPolicy Bypass -File .\build-android.ps1           # fabrique le .aab
#
# Le script demande les mots de passe : ils ne sont jamais écrits dans un fichier.
# La version se règle dans android\app\version.properties (versionCode +1 à chaque envoi).
param(
  [switch]$NewKey,
  [string]$Keystore = "$env:USERPROFILE\neonbay-keys\neonbay-upload.jks",
  [string]$Alias = "upload"
)
$ErrorActionPreference = "Stop"
$App = $PSScriptRoot
$Android = Join-Path $App "android"

# Java : celui fourni avec Android Studio (jbr) si JAVA_HOME n'est pas défini
if (-not $env:JAVA_HOME) {
  $jbr = "C:\Program Files\Android\Android Studio\jbr"
  if (Test-Path $jbr) { $env:JAVA_HOME = $jbr } else { throw "Java introuvable : installe Android Studio ou définis JAVA_HOME." }
}
$keytool = Join-Path $env:JAVA_HOME "bin\keytool.exe"

# SDK Android : celui installé par Android Studio
if (-not (Test-Path (Join-Path $Android "local.properties"))) {
  $sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
  if (-not (Test-Path $sdk)) { throw "SDK Android introuvable. Ouvre d'abord le dossier android dans Android Studio une fois." }
  "sdk.dir=$($sdk -replace '\\','\\')" | Set-Content -Encoding ASCII (Join-Path $Android "local.properties")
}

function Read-Secret([string]$label) {
  $s = Read-Host $label -AsSecureString
  return [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
}

if ($NewKey) {
  if (Test-Path $Keystore) { Write-Host "La clé existe déjà : $Keystore (rien n'est modifié)."; exit 0 }
  New-Item -ItemType Directory -Force (Split-Path $Keystore) | Out-Null
  $pass = Read-Secret "Choisis un mot de passe pour la clé (6 caractères minimum)"
  & $keytool -genkeypair -v -storetype PKCS12 -keystore $Keystore -alias $Alias -keyalg RSA -keysize 2048 -validity 10000 `
    -storepass $pass -keypass $pass -dname "CN=Neon Bay, O=Neon Bay, C=FR"
  if ($LASTEXITCODE -ne 0) { throw "keytool a échoué." }
  Write-Host ""
  Write-Host "Clé créée : $Keystore" -ForegroundColor Green
  Write-Host "IMPORTANT : copie ce fichier ET son mot de passe dans 2 endroits sûrs (clé USB, gestionnaire de mots de passe)." -ForegroundColor Yellow
  exit 0
}

if (-not (Test-Path $Keystore)) { throw "Clé introuvable : $Keystore. Lance d'abord le script avec -NewKey." }
$pass = Read-Secret "Mot de passe de la clé"
$env:NB_KEYSTORE = $Keystore
$env:NB_KEYSTORE_PASS = $pass
$env:NB_KEY_ALIAS = $Alias
$env:NB_KEY_PASS = $pass

Push-Location $Android
try {
  & .\gradlew.bat --no-daemon bundleRelease
  if ($LASTEXITCODE -ne 0) { throw "La compilation Gradle a échoué." }
} finally {
  Pop-Location
  Remove-Item Env:NB_KEYSTORE_PASS, Env:NB_KEY_PASS -ErrorAction SilentlyContinue
}

$props = ((Get-Content (Join-Path $Android "app\version.properties") | Where-Object { $_ -match "=" -and $_ -notmatch "^#" }) -join "`n") | ConvertFrom-StringData
$aab = Join-Path $Android "app\build\outputs\bundle\release\app-release.aab"
$dist = Join-Path $App "dist"
New-Item -ItemType Directory -Force $dist | Out-Null
$out = Join-Path $dist ("neon-bay-{0}-{1}.aab" -f $props.versionName, $props.versionCode)
Copy-Item $aab $out -Force
Write-Host "Prêt pour Google Play : $out" -ForegroundColor Green
