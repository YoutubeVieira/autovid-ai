# Installe earshot (outils 2 et 3 de la vidéo « 3 outils SFX ») pour ce projet, sur Windows (PowerShell).
# Même fichier dans le dépôt autovid-shorts (outils\). Mac / Linux : installer-earshot.sh.
#
#   powershell -ExecutionPolicy Bypass -File outils\installer-earshot.ps1
#   ... -Ecoute     (+ modèles d'écoute, ≈ 1,1 Go)    ... -SansMcp    (n'enregistre pas le serveur MCP)
param([switch]$Ecoute, [switch]$SansMcp)
$ErrorActionPreference = "Stop"
$Commit = "7a7f7c5c70d4a763a1eca4b3666af7c77e313f97"   # version testée
$Repo = "https://github.com/Leonxlnx/earshot"
$Projet = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Projet ".venv-earshot"
$Py = Join-Path $Venv "Scripts\python.exe"

# « py » (lanceur officiel) évite le faux python du Microsoft Store.
$Base = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
Write-Host "1/3 environnement Python : $Venv"
& $Base -3 -m venv $Venv
& $Py -m pip install -q --upgrade pip
$Extras = "mcp"
if ($Ecoute) {
  $Extras = "mcp,listen"
  & $Py -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu
}
& $Py -m pip install -q "earshot[$Extras] @ git+$Repo@$Commit"
if ($Ecoute) { & $Py -m earshot doctor --fetch | Out-Null }

Write-Host "2/3 serveur MCP"
if (-not $SansMcp -and (Get-Command claude -ErrorAction SilentlyContinue)) {
  Push-Location $Projet
  claude mcp remove earshot --scope local 2>$null
  claude mcp add earshot --scope local -e EARSHOT_THREADS=3 -- $Py -m earshot mcp
  Pop-Location
} else {
  Write-Host "   (ignoré) à la main : claude mcp add earshot --scope local -e EARSHOT_THREADS=3 -- `"$Py`" -m earshot mcp"
}

Write-Host "3/3 essai"
& $Py -m earshot make "a soft UI pop" -o (Join-Path $Venv "essai.wav")
Write-Host ""
Write-Host "OK : earshot est prêt. Python pour la skill real-sound ({{PY}}) : $Py"
Write-Host "   Relancez Claude Code dans ce dossier pour charger le serveur MCP « earshot »."
