@echo off
chcp 65001 >nul
setlocal
title AutoVid AI - installation sur le PC
rem Installe et lance les projets AutoVid AI sur ce PC (Windows). Double-cliquez, ou tapez son nom dans l'invite de commandes.
rem Mode d'emploi : INSTALLER-SUR-PC.txt

set "DEPOT=https://github.com/YoutubeVieira/autovid-ai.git"
set "BRANCHE=ccr-dc9e84d2-s625ne"
set "DOSSIER=%USERPROFILE%\Documents\autovid-ai"

echo.
echo === 1/4 Verification des outils ===
set "MANQUE="
where git    >nul 2>nul || set "MANQUE=%MANQUE% Git.Git"
where python >nul 2>nul || set "MANQUE=%MANQUE% Python.Python.3.12"
where node   >nul 2>nul || set "MANQUE=%MANQUE% OpenJS.NodeJS.LTS"
where ffmpeg >nul 2>nul || set "MANQUE=%MANQUE% Gyan.FFmpeg"
if defined MANQUE (
  echo Outils manquants :%MANQUE%
  choice /m "Les installer maintenant avec winget"
  if errorlevel 2 goto fin
  winget install -e --accept-source-agreements --accept-package-agreements%MANQUE%
  echo.
  echo Installation terminee. FERMEZ cette fenetre puis relancez ce fichier
  echo ^(Windows doit recharger la liste des programmes^).
  goto fin
)
where claude >nul 2>nul || (
  echo Claude Code n'est pas installe. Voir https://code.claude.com/docs
  echo puis lancez « claude » une fois pour vous connecter, et relancez ce fichier.
  goto fin
)
echo Tous les outils sont la.

echo.
echo === 2/4 Recuperation du projet dans %DOSSIER% ===
if exist "%DOSSIER%\.git" (
  git -C "%DOSSIER%" fetch origin %BRANCHE% || goto erreur
  git -C "%DOSSIER%" checkout %BRANCHE% || goto erreur
  git -C "%DOSSIER%" pull --ff-only origin %BRANCHE% || goto erreur
) else (
  git clone -b %BRANCHE% "%DEPOT%" "%DOSSIER%" || goto erreur
)

echo.
echo === 3/4 Choix du projet ===
echo   1 = projet-video      ^(Shorts, 7 styles, machine a Reels^)
echo   2 = projet-senior-us  ^(gym douce seniors^)
echo   3 = projet-app        ^(applications web et mobiles^)
choice /c 123 /m "Votre choix"
if errorlevel 3 (set "PROJET=projet-app") else if errorlevel 2 (set "PROJET=projet-senior-us") else (set "PROJET=projet-video")
cd /d "%DOSSIER%\%PROJET%" || goto erreur

if exist "remotion\package.json" (
  echo Installation du modele de montage Remotion ^(npm install^)...
  pushd remotion
  call npm install --no-audit --no-fund || (popd & goto erreur)
  popd
)

if exist "outils\installer-earshot.ps1" (
  choice /m "Installer earshot (effets sonores, environ 1 minute)"
  if not errorlevel 2 powershell -NoProfile -ExecutionPolicy Bypass -File "outils\installer-earshot.ps1"
)
if exist "outils\installer-styles.ps1" (
  choice /m "Installer les 7 styles de creation MP4 (environ 200 Mo)"
  if not errorlevel 2 powershell -NoProfile -ExecutionPolicy Bypass -File "outils\installer-styles.ps1"
)

echo.
echo === 4/4 Lancement de la session Claude sur ce PC ===
echo Ouvrez ensuite l'application Claude Code : la session « %PROJET% » apparait dans la liste.
echo Laissez cette fenetre OUVERTE pendant que vous travaillez ^(Ctrl+C pour arreter^).
echo.
claude remote-control
goto fin

:erreur
echo.
echo Une etape a echoue : copiez le message ci-dessus et envoyez-le a Claude.

:fin
echo.
pause
