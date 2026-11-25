@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title AutoVid - creation des 3 depots independants
rem Cree sur GitHub les 3 depots prives autovid-shorts, autovid-senior, autovid-apps, les remplit et les place
rem dans Documents. Tout par commande, avec l'outil officiel de GitHub (gh). Mode d'emploi : CREER-DEPOTS.txt

set "COMPTE=YoutubeVieira"
set "SOURCE=https://github.com/YoutubeVieira/autovid-ai.git"
set "BRANCHE=ccr-dc9e84d2-s625ne"
set "TMPSRC=%TEMP%\autovid-ai-source"
set "DOCS=%USERPROFILE%\Documents"

echo.
echo === 1/5 Outils ===
where git >nul 2>nul || (
  echo Git manque.
  choice /m "L'installer avec winget"
  if errorlevel 2 goto fin
  winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
  echo FERMEZ cette fenetre puis relancez ce fichier.
  goto fin
)
where gh >nul 2>nul || (
  echo L'outil GitHub ^(gh^) manque.
  choice /m "L'installer avec winget"
  if errorlevel 2 goto fin
  winget install -e --id GitHub.cli --accept-source-agreements --accept-package-agreements
  echo FERMEZ cette fenetre puis relancez ce fichier.
  goto fin
)
echo Git et gh sont la.

echo.
echo === 2/5 Connexion a GitHub ===
gh auth status >nul 2>nul || (
  echo Une page GitHub va s'ouvrir : collez le code affiche ici, puis autorisez.
  gh auth login --hostname github.com --git-protocol https --web || goto erreur
)
gh auth setup-git >nul 2>nul
for /f "delims=" %%U in ('gh api user --jq .login') do set "MOI=%%U"
echo Connecte en tant que : !MOI!
if /i not "!MOI!"=="%COMPTE%" (
  echo Attention : les depots seront crees sur le compte !MOI!, pas %COMPTE%.
  choice /m "Continuer quand meme"
  if errorlevel 2 goto fin
  set "COMPTE=!MOI!"
)

echo.
echo === 3/5 Telechargement des 3 projets ===
if exist "%TMPSRC%" rmdir /s /q "%TMPSRC%"
git clone -q --depth 1 -b %BRANCHE% %SOURCE% "%TMPSRC%" || goto erreur

echo.
echo === 4/5 Creation des depots prives et envoi ===
call :projet autovid-shorts "Shorts et Reels avec Claude Code et Antigravity"
if errorlevel 1 goto erreur
call :projet autovid-senior "Gentle Senior Fitness US - seances de gym douce automatiques"
if errorlevel 1 goto erreur
call :projet autovid-apps "Applications web et mobiles avec Claude Code et Antigravity"
if errorlevel 1 goto erreur
rmdir /s /q "%TMPSRC%"

echo.
echo === 5/5 Termine ===
echo Vos 3 projets :
echo   %DOCS%\autovid-shorts   https://github.com/%COMPTE%/autovid-shorts
echo   %DOCS%\autovid-senior   https://github.com/%COMPTE%/autovid-senior
echo   %DOCS%\autovid-apps     https://github.com/%COMPTE%/autovid-apps
echo.
echo Pour que Claude ^(dans le cloud^) puisse aussi y travailler, autorisez l'application Claude sur ces depots :
echo   https://github.com/apps/claude/installations/select_target
echo.
echo Installer un projet maintenant ?  1 = autovid-shorts   2 = autovid-senior   3 = autovid-apps   0 = non
choice /c 1230 /m "Votre choix"
if errorlevel 4 goto fin
if errorlevel 3 (set "P=autovid-apps") else if errorlevel 2 (set "P=autovid-senior") else (set "P=autovid-shorts")
call "%DOCS%\!P!\INSTALLER.bat"
goto fin

:projet
set "P=%~1"
set "DEST=%DOCS%\%P%"
echo.
echo --- %P% ---
if exist "%DEST%\.git" (
  echo %DEST% existe deja : rien a faire pour ce projet.
  exit /b 0
)
if exist "%DEST%" (
  echo Le dossier %DEST% existe deja ^(sans Git^) : renommez-le puis relancez ce fichier.
  exit /b 1
)
robocopy "%TMPSRC%\%P%" "%DEST%" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 exit /b 1
pushd "%DEST%"
git init -q -b main
git config user.name "%COMPTE%"
for /f "delims=" %%I in ('gh api user --jq .id') do git config user.email "%%I+%COMPTE%@users.noreply.github.com"
git add -A
git commit -q -m "Projet %P% (extrait du depot autovid-ai)"
gh repo view %COMPTE%/%P% >nul 2>nul
if errorlevel 1 (
  gh repo create %COMPTE%/%P% --private --description "%~2" --source . --remote origin --push
) else (
  echo Le depot %COMPTE%/%P% existe deja sur GitHub : envoi dedans ^(il doit etre vide^).
  git remote add origin https://github.com/%COMPTE%/%P%.git
  git push -u origin main
)
if errorlevel 1 (
  popd
  echo Echec de l'envoi de %P%. Si le depot existait avec un README, supprimez-le sur GitHub et relancez.
  exit /b 1
)
popd
echo %P% : cree et envoye.
exit /b 0

:erreur
echo.
echo Une etape a echoue : copiez le message ci-dessus et envoyez-le a Claude.

:fin
echo.
pause
