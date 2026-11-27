// (Facultatif mais recommandé) Fonction serveur qui vérifie un achat Google Play et en accuse réception.
// Prévue pour Netlify Functions (dossier netlify/functions/). Adaptable à Vercel ou Cloudflare.
// Variables d'environnement à définir chez l'hébergeur (jamais dans le code) :
//   GOOGLE_SERVICE_ACCOUNT_JSON : contenu JSON de la clé du compte de service lié à la Play Console
//   PACKAGE_NAME : com.ton-nom.neonbay
// Dépendance : npm install googleapis
const { google } = require('googleapis');

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'POST uniquement' };
  try {
    const { sku, token } = JSON.parse(event.body || '{}');
    if (!sku || !token) return { statusCode: 400, body: 'sku et token requis' };
    const auth = new google.auth.GoogleAuth({
      credentials: JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON),
      scopes: ['https://www.googleapis.com/auth/androidpublisher'],
    });
    const api = google.androidpublisher({ version: 'v3', auth });
    const packageName = process.env.PACKAGE_NAME;
    const { data } = await api.purchases.products.get({ packageName, productId: sku, token });
    if (data.purchaseState !== 0) return { statusCode: 402, body: 'Achat non payé ou annulé' };
    if (data.acknowledgementState === 0) {
      await api.purchases.products.acknowledge({ packageName, productId: sku, token, requestBody: {} });
    }
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  } catch (e) {
    return { statusCode: 500, body: 'Erreur de vérification' };
  }
};
