@echo off
chcp 65001 >nul
setlocal
title autovid-senior - installation sur le PC
rem Installe et lance le projet autovid-senior sur ce PC (Windows). Double-cliquez, ou tapez son nom dans l'invite de commandes.
rem Mode d'emploi : INSTALLER.txt

set "DEPOT=https://github.com/YoutubeVieira/autovid-senior.git"
set "DOSSIER=%USERPROFILE%\Documents\autovid-senior"

echo.
echo === 1/4 Verification des outils ===
set "MANQUE="
where git    >nul 2>nul || set "MANQUE=%MANQUE% Git.Git"
where python >nul 2>nul || set "MANQUE=%MANQUE% Python.Python.3.12"
where ffmpeg >nul 2>nul || set "MANQUE=%MANQUE% Gyan.FFmpeg"
if defined MANQUE (
  echo Outils manquants :%MANQUE%
  choice /m "Les installer maintenant avec winget"
  if errorlevel 2 goto fin
  winget install -e --accept-source-agreements --accept-package-agreements%MANQUE%
  echo.
  echo Installation terminee. FERMEZ cette fenetre puis relancez ce fichier.
  goto fin
)
where claude >nul 2>nul || (
  echo Claude Code n'est pas installe :
  echo   curl -fsSL https://claude.ai/install.cmd -o install.cmd ^&^& install.cmd ^&^& del install.cmd
  echo puis lancez « claude » une fois pour vous connecter, et relancez ce fichier.
  goto fin
)
echo Tous les outils sont la.

echo.
echo === 2/4 Recuperation du projet dans %DOSSIER% ===
echo ^(depot prive : Git peut ouvrir une fenetre de connexion GitHub, connectez-vous avec le compte YoutubeVieira^)
if exist "%DOSSIER%\.git" (
  git -C "%DOSSIER%" pull --ff-only || goto erreur
) else (
  git clone "%DEPOT%" "%DOSSIER%" || goto erreur
)
cd /d "%DOSSIER%" || goto erreur

echo.
echo === 3/4 Installation du projet ===
echo Dependances Python ^(numpy, Pillow^)...
python -m pip install -r requirements.txt || goto erreur
choice /m "Installer earshot (effets sonores, environ 1 minute)"
if not errorlevel 2 powershell -NoProfile -ExecutionPolicy Bypass -File "outils\installer-earshot.ps1"
echo Verification avec l'exemple de 50 secondes :
python autovideo.py check sessions\exemple-50s.json

echo.
echo === 4/4 Lancement de la session Claude sur ce PC ===
echo Ouvrez ensuite l'application Claude Code : la session « autovid-senior » apparait dans la liste.
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
