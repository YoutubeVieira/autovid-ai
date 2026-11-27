#!/usr/bin/env bash
# Néon Bay : fabrique le fichier .aab (Android App Bundle) à envoyer sur Google Play.
#
# Usage :
#   bash tools/build-android.sh            -> web + cap sync + ./gradlew bundleRelease (signé)
#   bash tools/build-android.sh sync       -> web + cap sync seulement (pas de Gradle)
#   bash tools/build-android.sh keystore   -> crée une clé d'importation (upload key) si elle n'existe pas
#
# Variables d'environnement (jamais dans le dépôt) :
#   NB_KEYSTORE       chemin du fichier .jks   (défaut : ~/neonbay-keys/neonbay-upload.jks)
#   NB_KEYSTORE_PASS  mot de passe du keystore
#   NB_KEY_ALIAS      alias de la clé           (défaut : upload)
#   NB_KEY_PASS       mot de passe de la clé    (défaut : le même que NB_KEYSTORE_PASS)
#   NB_VERSION_CODE   numéro entier, +1 à chaque envoi sur Google Play (défaut : 1)
#   NB_VERSION_NAME   version affichée aux joueurs (défaut : version de app-android/package.json)
#
# Prérequis : Node.js 20+, JDK 21, Android SDK (ANDROID_HOME ou app-android/android/local.properties),
# et l'accès réseau à dl.google.com / maven.google.com (dépendances Android de Gradle).
set -euo pipefail

NB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$NB_ROOT/app-android"
MODE="${1:-bundle}"
DEFAULT_KS="$HOME/neonbay-keys/neonbay-upload.jks"

make_keystore() {
  local ks="${NB_KEYSTORE:-$DEFAULT_KS}"
  if [ -f "$ks" ]; then echo "La clé existe déjà : $ks (rien n'est modifié)."; return 0; fi
  case "$ks" in "$NB_ROOT"/*|"$(cd "$NB_ROOT/.." && pwd)"/*)
    echo "Refus : le keystore doit être rangé HORS du dépôt git (ex. $DEFAULT_KS)."; exit 1;; esac
  : "${NB_KEYSTORE_PASS:?Définis NB_KEYSTORE_PASS (mot de passe de 6 caractères minimum)}"
  mkdir -p "$(dirname "$ks")"; chmod 700 "$(dirname "$ks")"
  # Format PKCS12 : un seul mot de passe pour le fichier et la clé (NB_KEY_PASS est ignoré ici).
  keytool -genkeypair -v -storetype PKCS12 -keystore "$ks" -alias "${NB_KEY_ALIAS:-upload}" \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass "$NB_KEYSTORE_PASS" -keypass "$NB_KEYSTORE_PASS" \
    -dname "CN=${NB_KEY_CN:-Neon Bay}, O=${NB_KEY_ORG:-Neon Bay}, C=FR"
  chmod 600 "$ks"
  echo
  echo "Clé créée : $ks"
  echo "IMPORTANT : sauvegarde ce fichier ET son mot de passe dans 2 endroits sûrs (clé USB, gestionnaire de mots de passe)."
  echo "Avec la signature d'application Google Play, une clé d'importation perdue peut être réinitialisée par le support Google, mais cela prend du temps."
  echo "Empreinte SHA-256 (utile pour la Play Console) :"
  keytool -list -v -keystore "$ks" -storepass "$NB_KEYSTORE_PASS" -alias "${NB_KEY_ALIAS:-upload}" | grep -E "SHA256|SHA-256" || true
}

sync_web() {
  command -v node >/dev/null || { echo "Node.js est requis."; exit 1; }
  cd "$APP"
  [ -d node_modules ] || npm ci --no-audit --no-fund || npm install --no-audit --no-fund
  node "$NB_ROOT/tools/build-app-web.js"
  npx cap sync android
}

case "$MODE" in
  keystore) make_keystore; exit 0;;
  sync) sync_web; exit 0;;
  bundle) ;;
  *) echo "Mode inconnu : $MODE (bundle | sync | keystore)"; exit 1;;
esac

# --- fabrication du .aab signé ---
export NB_KEYSTORE="${NB_KEYSTORE:-$DEFAULT_KS}"
if [ ! -f "$NB_KEYSTORE" ]; then
  echo "Keystore introuvable : $NB_KEYSTORE"
  echo "Crée-le d'abord :  NB_KEYSTORE_PASS='...' bash tools/build-android.sh keystore"
  exit 1
fi
: "${NB_KEYSTORE_PASS:?Définis NB_KEYSTORE_PASS (mot de passe du keystore)}"
export NB_KEY_ALIAS="${NB_KEY_ALIAS:-upload}"
export NB_KEY_PASS="${NB_KEY_PASS:-$NB_KEYSTORE_PASS}"
export NB_VERSION_CODE="${NB_VERSION_CODE:-1}"
export NB_VERSION_NAME="${NB_VERSION_NAME:-$(node -p "require('$APP/package.json').version")}"

if [ -z "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}" ] && [ ! -f "$APP/android/local.properties" ]; then
  echo "Android SDK introuvable : définis ANDROID_HOME (ex. ~/Android/Sdk) ou crée app-android/android/local.properties (sdk.dir=...)."
  exit 1
fi

sync_web
cd "$APP/android"
chmod +x gradlew
./gradlew --no-daemon bundleRelease

AAB="$APP/android/app/build/outputs/bundle/release/app-release.aab"
[ -f "$AAB" ] || { echo "Le fichier .aab n'a pas été produit."; exit 1; }
mkdir -p "$APP/dist"
OUT="$APP/dist/neon-bay-${NB_VERSION_NAME}-${NB_VERSION_CODE}.aab"
cp "$AAB" "$OUT"
jarsigner -verify "$OUT" >/dev/null 2>&1 && echo "Signature vérifiée." || echo "Attention : signature non vérifiée (jarsigner)."
echo "Prêt pour Google Play : $OUT  (versionCode $NB_VERSION_CODE, version $NB_VERSION_NAME)"
