# Installe les 7 styles de création MP4 pour ce projet, sur Windows (PowerShell). Voir installer-styles.sh et styles/STYLES.md.
#   powershell -ExecutionPolicy Bypass -File outils\installer-styles.ps1 [-Setup] [-SansOpenMontage]
param([switch]$Setup, [switch]$SansOpenMontage)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Depots = @{
  "claymation-ads"    = @("https://github.com/mikefutia/claymation-ads-claude-skill", "5c88eea9b63d425ca444e1123dbfac8f93b193b3")
  "seedance"          = @("https://github.com/robonuggets/seedance-skill", "e513cc85ae2f9e8c8045b9581389cb8f8daddda9")
  "talking-explainer" = @("https://github.com/brewed-ops/talking-explainer", "3a19bbce0c97dcdd3120c7e3c4b10ddc3e13f1d5")
  "OpenMontage"       = @("https://github.com/calesthio/OpenMontage", "2e003e65fa99a0f329478a2c1cdcf26bc481933a")
}
function Fetch($nom) {
  $url, $commit = $Depots[$nom]; $dir = "externes\$nom"
  if (Test-Path "$dir\.git") { git -C $dir fetch -q --depth 1 origin $commit } else { git clone -q --filter=blob:none $url $dir }
  git -C $dir checkout -q $commit
}
New-Item -ItemType Directory -Force externes, .claude\skills | Out-Null

Write-Host "1/4 Claymation"; Fetch "claymation-ads"
Remove-Item -Recurse -Force .claude\skills\claymation-ads -ErrorAction SilentlyContinue
Copy-Item -Recurse externes\claymation-ads\claymation-ads .claude\skills\claymation-ads

Write-Host "2/4 Commercial / Motion (seedance)"; Fetch "seedance"
New-Item -ItemType Directory -Force .claude\skills\seedance | Out-Null
Copy-Item externes\seedance\SKILL.md, externes\seedance\README.md .claude\skills\seedance\

Write-Host "3/4 Explainer / Cartoon (talking-explainer)"; Fetch "talking-explainer"
foreach ($sk in "talking-explainer", "explainer-kit", "spatial-film") {
  Remove-Item -Recurse -Force ".claude\skills\$sk" -ErrorAction SilentlyContinue
  Copy-Item -Recurse "externes\talking-explainer\skills\$sk" ".claude\skills\$sk"
}
if (Get-Command npx -ErrorAction SilentlyContinue) { npx -y hyperframes skills update general-video hyperframes-animation media-use }
else { Write-Host "   npx absent : installez Node.js (winget install OpenJS.NodeJS.LTS)" }

if (-not $SansOpenMontage) {
  Write-Host "4/4 OpenMontage (~165 Mo)"; Fetch "OpenMontage"
  if ($Setup) { Push-Location externes\OpenMontage; make setup; Pop-Location }
  else { Write-Host "   (dépendances non installées : relancez avec -Setup ; « make » vient avec Git for Windows ou choco install make)" }
}
if (-not (Test-Path .env)) { Copy-Item outils\env.exemple .env }
Write-Host ""
Write-Host "OK : styles installés. Clés à renseigner dans .env (jamais dans git) : voir styles\STYLES.md."
