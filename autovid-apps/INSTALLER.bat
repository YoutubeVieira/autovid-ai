@echo off
chcp 65001 >nul
setlocal
title autovid-apps - installation sur le PC
rem Installe et lance le projet autovid-apps sur ce PC (Windows). Double-cliquez, ou tapez son nom dans l'invite de commandes.
rem Mode d'emploi : INSTALLER.txt

set "DEPOT=https://github.com/YoutubeVieira/autovid-apps.git"
set "DOSSIER=%USERPROFILE%\Documents\autovid-apps"

echo.
echo === 1/4 Verification des outils ===
set "MANQUE="
where git    >nul 2>nul || set "MANQUE=%MANQUE% Git.Git"
where node   >nul 2>nul || set "MANQUE=%MANQUE% OpenJS.NodeJS.LTS"
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
echo Rien a installer de plus : les agents et skills sont dans .claude\.

echo.
echo === 4/4 Lancement de la session Claude sur ce PC ===
echo Ouvrez ensuite l'application Claude Code : la session « autovid-apps » apparait dans la liste.
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
