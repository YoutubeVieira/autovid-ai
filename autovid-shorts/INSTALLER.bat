@echo off
chcp 65001 >nul
setlocal
title autovid-shorts - installation sur le PC
rem Installe et lance le projet autovid-shorts sur ce PC (Windows). Double-cliquez, ou tapez son nom dans l'invite de commandes.
rem Mode d'emploi : INSTALLER.txt

set "DEPOT=https://github.com/YoutubeVieira/autovid-shorts.git"
set "DOSSIER=%USERPROFILE%\Documents\autovid-shorts"

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
echo Modele de montage Remotion ^(npm install^)...
pushd remotion
call npm install --no-audit --no-fund || (popd & goto erreur)
popd
choice /m "Installer earshot (effets sonores, environ 1 minute)"
if not errorlevel 2 powershell -NoProfile -ExecutionPolicy Bypass -File "outils\installer-earshot.ps1"
choice /m "Installer les 7 styles de creation MP4 (environ 200 Mo)"
if not errorlevel 2 powershell -NoProfile -ExecutionPolicy Bypass -File "outils\installer-styles.ps1"
python -c "import faster_whisper" >nul 2>nul || (
  choice /m "Installer la transcription pour la super-analyse (faster-whisper, environ 200 Mo)"
  if not errorlevel 2 python -m pip install faster-whisper
)
call :analyse

echo.
echo === 4/4 Lancement de la session Claude sur ce PC ===
echo Ouvrez ensuite l'application Claude Code : la session « autovid-shorts » apparait dans la liste.
echo Laissez cette fenetre OUVERTE pendant que vous travaillez ^(Ctrl+C pour arreter^).
echo.
claude remote-control
goto fin

:analyse
echo.
choice /m "Analyser une video maintenant (super-analyse : seconde par seconde, moments forts, mots, SEO, prompts)"
if errorlevel 2 exit /b 0
set "VIDEO="
set /p "VIDEO=Glissez la video dans cette fenetre (ou collez son chemin) puis Entree : "
if not defined VIDEO exit /b 0
set "VIDEO=%VIDEO:"=%"
set "SRT="
set /p "SRT=Fichier de sous-titres .srt (Entree si aucun) : "
if defined SRT set "SRT=%SRT:"=%"
if defined SRT (python outils\superanalyse.py "%VIDEO%" --srt "%SRT%") else (python outils\superanalyse.py "%VIDEO%")
echo Rapports dans : %CD%\analyses
start "" "%CD%\analyses"
goto analyse

:erreur
echo.
echo Une etape a echoue : copiez le message ci-dessus et envoyez-le a Claude.

:fin
echo.
pause
