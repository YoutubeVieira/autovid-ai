/* Imprime une page HTML en PDF A4 avec Chromium (Playwright). Usage : node tools/print-pdf.js entree.html sortie.pdf */
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [src, dst] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + path.resolve(src));
  await p.pdf({ path: dst, format: 'A4', printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log('PDF écrit', dst);
})();
