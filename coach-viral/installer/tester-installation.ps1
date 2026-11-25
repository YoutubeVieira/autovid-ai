# Test de bout en bout d'une installation Windows (utilise par le robot GitHub, ou a la main apres installation).
# Prerequis : Coach Viral installe et demarre (lancer.ps1, avec COACH_TEST=1 pour rendre la main).
# Produit des fichiers a ecouter / regarder dans le dossier COACH_SORTIES.

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Racine = Join-Path $env:LOCALAPPDATA 'CoachViral'
$r = Get-Content (Join-Path $Racine 'config\reglages.json') -Raw | ConvertFrom-Json
$Base = "http://127.0.0.1:$($r.port)"
$H = @{ 'x-code-acces' = $r.code_acces }
$Sorties = if ($env:COACH_SORTIES) { $env:COACH_SORTIES } else { Join-Path $Racine 'test-sorties' }
New-Item -ItemType Directory -Force -Path $Sorties | Out-Null
$echecs = New-Object System.Collections.ArrayList

function Api($chemin, $corps) {
  $json = $corps | ConvertTo-Json -Depth 10
  Invoke-RestMethod "$Base/api/$chemin" -Method Post -Headers $H -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($json)) -TimeoutSec 600
}
function Televerser($fichier, $type) {
  Invoke-RestMethod "$Base/api/fichier" -Method Post -Headers $H -ContentType $type -InFile $fichier -TimeoutSec 600
}
function Attendre($id, $minutes) {
  $fin = (Get-Date).AddMinutes($minutes)
  while ((Get-Date) -lt $fin) {
    $j = Invoke-RestMethod "$Base/api/travaux/$id" -Headers $H
    if ($j.etat -eq 'termine') { return $j.resultat }
    if ($j.etat -eq 'erreur') { throw $j.erreur }
    Start-Sleep -Seconds 3
  }
  throw "Delai depasse ($minutes min)"
}
function Telecharger($nom, $dest) {
  Invoke-WebRequest "$Base/api/fichiers/$nom" -Headers $H -OutFile $dest -UseBasicParsing
  $taille = (Get-Item $dest).Length
  if ($taille -lt 5000) { throw "Fichier trop petit ($taille octets)" }
  return $taille
}
function Duree($f) { [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $f) }
function Etape($nom, [scriptblock]$bloc) {
  Write-Host ''
  Write-Host "==> $nom" -ForegroundColor Cyan
  $t = Get-Date
  try { & $bloc; Write-Host ("    OK ({0:N0} s)" -f ((Get-Date) - $t).TotalSeconds) -ForegroundColor Green }
  catch { Write-Host "    ECHEC : $($_.Exception.Message)" -ForegroundColor Red; [void]$echecs.Add($nom) }
}

$sante = Invoke-RestMethod "$Base/api/sante"
Write-Host "Moteurs de voix : $($sante.moteurs_voix -join ', ') ; clonage : $($sante.clonage -join ', ')"

Etape 'Voix Kokoro en francais' {
  $j = Api 'voix/essai' @{ texte = "Le pire bruit dans un couple, ce n'est pas les cris. C'est le silence."; moteur = 'kokoro'; langue = 'fr' }
  $res = Attendre $j.travail 15
  $f = Join-Path $Sorties 'voix-kokoro-fr.mp3'
  $null = Telecharger $res.voix $f
  Write-Host ("    {0:N1} s de voix" -f (Duree $f))
}

Etape 'Voix Kokoro en portugais du Bresil' {
  $j = Api 'voix/essai' @{ texte = 'Na roda, quem tem pressa cai. A capoeira me ensinou a paciencia.'; moteur = 'kokoro'; langue = 'pt' }
  $res = Attendre $j.travail 15
  $null = Telecharger $res.voix (Join-Path $Sorties 'voix-kokoro-pt.mp3')
}

Etape 'Voix Edge en francais' {
  $j = Api 'voix/essai' @{ texte = 'Bonjour, ceci est un essai de voix.'; moteur = 'edge'; langue = 'fr' }
  $res = Attendre $j.travail 10
  $null = Telecharger $res.voix (Join-Path $Sorties 'voix-edge-fr.mp3')
}

$script:video = $null
Etape 'Studio : video citation avec images et voix Kokoro' {
  $version = @{
    titre = 'La patience de la roda'; legende = 'Ce que la capoeira m a appris.'; hashtags = @('capoeira', 'patience')
    ambiance_musique = 'berimbau doux'; pourquoi_mieux = 'Accroche directe.'
    scenes = @(
      @{ haut = 'Dans la roda, celui qui se precipite tombe.'; bas = 'La capoeira m a appris la patience.'; voix = 'Dans la roda, celui qui se precipite tombe.'; prompt_image = 'cinematic 3D animated scene, capoeira circle at sunset, warm light, Pixar style'; duree = 4 },
      @{ haut = 'Attendre son moment, c est deja jouer.'; bas = 'Et toi, tu sais attendre ?'; voix = 'Attendre son moment, c est deja jouer. Et toi, tu sais attendre ton tour ?'; prompt_image = 'cinematic 3D animated scene, young capoeirista smiling, berimbau, Pixar style'; duree = 4 }
    )
  }
  $j = Api 'studio/fabriquer' @{ gabarit = 'citation'; version = $version; moteur = 'kokoro'; langue = 'fr' }
  $res = Attendre $j.travail 30
  $script:video = Join-Path $Sorties 'video-citation.mp4'
  $null = Telecharger $res.video $script:video
  $null = Telecharger $res.voix (Join-Path $Sorties 'video-citation-voix.mp3')
  Write-Host ("    video de {0:N1} s" -f (Duree $script:video))
}

Etape 'Face camera : transcription Whisper et sous-titres mot a mot' {
  if (-not $script:video) { throw 'pas de video source (etape precedente en echec)' }
  $up = Televerser $script:video 'video/mp4'
  $j = Api 'studio/fabriquer' @{ gabarit = 'face_camera'; video = $up.id; titres = $false }
  $res = Attendre $j.travail 30
  $null = Telecharger $res.video (Join-Path $Sorties 'video-face-camera.mp4')
}

if ($sante.clonage -contains 'chatterbox') {
  Etape 'Clonage de voix Chatterbox (processeur, lent)' {
    $long = "Je confirme que c'est ma propre voix et j'autorise Coach Viral a la reproduire pour mes videos. " +
      "La capoeira est un art martial bresilien qui melange la musique, la danse et le combat. On la pratique en cercle, avec le berimbau."
    $j = Api 'voix/essai' @{ texte = $long; moteur = 'kokoro'; langue = 'fr' }
    $res = Attendre $j.travail 15
    $echantillon = Join-Path $Sorties 'echantillon-a-cloner.mp3'
    $null = Telecharger $res.voix $echantillon
    $up = Televerser $echantillon 'audio/mpeg'
    $null = Api 'voix/echantillon' @{ fichier = $up.id; consentement = $true }
    $j = Api 'voix/essai' @{ texte = 'Bonjour, voici ma voix clonee par Chatterbox.'; moteur = 'chatterbox'; langue = 'fr' }
    $res = Attendre $j.travail 60
    $null = Telecharger $res.voix (Join-Path $Sorties 'voix-clonee-chatterbox.mp3')
  }
}

if ($env:COACH_GEMINI_REEL -eq 'true') {
  Etape 'Gemini : vraies idees de videos' {
    $d = Api 'ideas' @{ niche = 'capoeira pour debutants'; nombre = 3; langue = 'fr' }
    if (-not $d.ideas -or $d.ideas.Count -lt 1) { throw 'aucune idee' }
    $d | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $Sorties 'gemini-idees.json') -Encoding UTF8
    Write-Host "    Premiere accroche : $($d.ideas[0].accroche)"
  }
} else {
  Write-Host ''
  Write-Host '==> Gemini : non teste (aucune cle GEMINI_API_KEY dans les secrets GitHub)' -ForegroundColor Yellow
}

Write-Host ''
if ($echecs.Count) { Write-Host "ECHECS : $($echecs -join ' | ')" -ForegroundColor Red; exit 1 }
Write-Host 'Tout fonctionne.' -ForegroundColor Green
