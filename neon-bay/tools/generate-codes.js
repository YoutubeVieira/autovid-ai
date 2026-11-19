#!/usr/bin/env node
// Génère des codes de déblocage pour Néon Bay.
// Usage : node tools/generate-codes.js 50 > codes.txt
// IMPORTANT : SALT doit être identique à SHOP_CONFIG.salt dans js/data.js
const crypto = require('crypto');
const SALT = 'nb-27359c4a7da65190-';
const ALPH = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function fnv(s) { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); } return h >>> 0; }
function check(body) { let h = fnv(SALT + body), o = ''; for (let i = 0; i < 4; i++) { o += ALPH[h % 32]; h = Math.floor(h / 32); } return o; }
const n = Math.max(1, parseInt(process.argv[2] || '10', 10));
for (let k = 0; k < n; k++) {
  let body = ''; const b = crypto.randomBytes(8); for (let i = 0; i < 8; i++) body += ALPH[b[i] % 32];
  const c = check(body);
  console.log(`NBAY-${body.slice(0, 4)}-${body.slice(4)}-${c}`);
}
