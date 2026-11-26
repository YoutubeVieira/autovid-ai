# Installe les skills vidéo dans Claude Code sur ce PC (dossier %USERPROFILE%\.claude\skills).
# Lancement : double-clic sur Installer-les-skills.bat
$ErrorActionPreference = "Stop"
$src = $PSScriptRoot
$dest = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$skills = @("montage-youtube-stock", "motion-design-video", "sound-design-auto")
foreach ($s in $skills) {
  $from = Join-Path $src $s
  if (-not (Test-Path (Join-Path $from "SKILL.md"))) { Write-Host "Introuvable : $from"; continue }
  $to = Join-Path $dest $s
  if (Test-Path $to) { Remove-Item -Recurse -Force $to }
  Copy-Item -Recurse $from $to
  Write-Host "Installée : $s"
}
Write-Host ""
Write-Host "Terminé. Dossier : $dest"
Write-Host "Redémarrez Claude Code (ou l'application Claude) pour que les skills apparaissent."
Read-Host "Appuyez sur Entrée pour fermer"
