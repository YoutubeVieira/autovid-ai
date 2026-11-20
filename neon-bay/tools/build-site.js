#!/usr/bin/env node
// Construit le site de vente de Néon Bay : site/dist/
//   index.html (page de vente), guides/*.html (articles), pdf/*.pdf, jouer/ (le jeu), sitemap.xml, robots.txt
// Usage : node tools/build-site.js [--no-pdf]   (les PDF demandent Playwright + Chromium)
// Réglages : SITE_URL et les liens ci-dessous.
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..'), site = path.join(root, 'site'), out = path.join(site, 'dist');
const SITE_URL = process.env.SITE_URL || 'https://TON-DOMAINE.fr';
const BUY_URL = '#acheter';            // remplace par ta page Systeme.io
const PRICE = '2,99 €';
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// ---------- mini Markdown ----------
function md(src) {
  const inline = t => esc(t).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>').replace(/`(.+?)`/g, '<code>$1</code>').replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>');
  const lines = src.split('\n'), html = []; let list = null, para = [], table = null;
  const flush = () => { if (para.length) { html.push('<p>' + inline(para.join(' ')) + '</p>'); para = []; } if (list) { html.push(`</${list}>`); list = null; } if (table) { html.push(renderTable(table)); table = null; } };
  const renderTable = rows => { const cells = r => r.replace(/^\||\|$/g, '').split('|').map(c => c.trim()); const head = cells(rows[0]); const body = rows.slice(2).map(cells); return `<div class="tw"><table><thead><tr>${head.map(h => `<th>${inline(h)}</th>`).join('')}</tr></thead><tbody>${body.map(r => `<tr>${r.map(c => `<td>${inline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`; };
  for (const raw of lines) {
    const l = raw.trimEnd();
    if (l.trim() === '<!--CTA-->') { flush(); html.push('<!--CTA-->'); continue; }
    if (/^\|.*\|$/.test(l.trim())) { if (!table) { flush(); table = []; } table.push(l.trim()); continue; } else if (table) { html.push(renderTable(table)); table = null; }
    let m;
    if (/^#\s+/.test(l)) { flush(); continue; }
    if ((m = l.match(/^(#{2,4})\s+(.*)$/))) { flush(); const lv = m[1].length, id = m[2].toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); html.push(`<h${lv} id="${id}">${inline(m[2])}</h${lv}>`); continue; }
    if ((m = l.match(/^\s*[-*]\s+(.*)$/))) { if (para.length) { html.push('<p>' + inline(para.join(' ')) + '</p>'); para = []; } if (list !== 'ul') { if (list) html.push(`</${list}>`); html.push('<ul>'); list = 'ul'; } html.push('<li>' + inline(m[1]) + '</li>'); continue; }
    if ((m = l.match(/^\s*\d+[.)]\s+(.*)$/))) { if (para.length) { html.push('<p>' + inline(para.join(' ')) + '</p>'); para = []; } if (list !== 'ol') { if (list) html.push(`</${list}>`); html.push('<ol>'); list = 'ol'; } html.push('<li>' + inline(m[1]) + '</li>'); continue; }
    if (!l.trim()) { flush(); continue; }
    if (list) { html.push(`</${list}>`); list = null; }
    para.push(l.trim());
  }
  flush();
  return html.join('\n');
}
function front(src) {
  const m = src.match(/^---\n([\s\S]*?)\n---\n?/); const meta = {};
  if (m) for (const line of m[1].split('\n')) { const k = line.match(/^(\w+):\s*(.*)$/); if (k) meta[k[1]] = k[2].replace(/^"|"$/g, ''); }
  return { meta, body: m ? src.slice(m[0].length) : src };
}

// ---------- gabarit commun ----------
const CSS = fs.readFileSync(path.join(site, 'style.css'), 'utf8');
const LOGO = `<a class="logo" href="/">NÉON<span>BAY</span></a>`;
const NAV = `<nav class="nav">${LOGO}<div class="links"><a href="/#jeu">Le jeu</a><a href="/guides/">Guides</a><a class="btn small" href="/jouer/">Jouer gratuitement</a></div></nav>`;
const FOOT = `<footer class="foot"><p>Néon Bay est un jeu indépendant original. Les guides de ce site sont des contenus de fans non officiels. Grand Theft Auto, GTA et les noms associés sont des marques de Rockstar Games et Take-Two Interactive ; ce site n'est ni affilié, ni approuvé, ni sponsorisé par ces sociétés.</p><p><a href="/jouer/privacy.html">Confidentialité</a> · <a href="/guides/">Tous les guides</a></p></footer>`;
const CTA = `<aside class="cta"><div><b>Envie d'un nouveau jeu de rue ?</b><p>Néon Bay est un jeu indépendant d'action en monde ouvert : 30 missions, 4 pays, police, gangs et poursuites, sur téléphone et ordinateur. Le premier niveau est gratuit.</p></div><a class="btn" href="/jouer/">Jouer au niveau 1</a></aside>`;
const page = ({ title, desc, canonical, body, schema, ogImg = '/img/og.jpg' }) => `<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="${SITE_URL}${canonical}">
<meta property="og:type" content="website"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:image" content="${SITE_URL}${ogImg}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/jouer/icons/icon-192.png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bungee&family=Chakra+Petch:wght@400;600;700&display=swap">
<style>${CSS}</style>${schema ? `<script type="application/ld+json">${JSON.stringify(schema)}</script>` : ''}</head>
<body>${NAV}${body}${FOOT}</body></html>`;

// ---------- guides ----------
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(path.join(out, 'guides'), { recursive: true }); fs.mkdirSync(path.join(out, 'pdf'), { recursive: true }); fs.mkdirSync(path.join(out, 'img'), { recursive: true });
const contentDir = path.join(site, 'content');
const order = ['gta-1', 'gta-2', 'gta-3', 'gta-vice-city', 'gta-san-andreas', 'gta-4', 'gta-5', 'gta-online', 'gta-6', 'gta-7'];
const guides = fs.existsSync(contentDir) ? fs.readdirSync(contentDir).filter(f => f.endsWith('.md')).map(f => { const { meta, body } = front(fs.readFileSync(path.join(contentDir, f), 'utf8')); return { ...meta, slug: meta.slug || f.replace('.md', ''), body }; }) : [];
guides.sort((a, b) => (order.indexOf(a.slug) + 1 || 99) - (order.indexOf(b.slug) + 1 || 99));
for (const g of guides) {
  let html = md(g.body);
  html = html.split('<!--CTA-->').join(CTA);
  const toc = [...html.matchAll(/<h2 id="([^"]+)">(.*?)<\/h2>/g)].map(m => `<li><a href="#${m[1]}">${m[2]}</a></li>`).join('');
  const others = guides.filter(o => o.slug !== g.slug).slice(0, 6).map(o => `<a class="mini" href="/guides/${o.slug}.html"><b>${esc(o.game || o.title)}</b><span>${esc(o.year || '')}</span></a>`).join('');
  const body = `<main class="article"><header class="ahead"><p class="eyebrow">Guide · ${esc(g.game || '')} ${g.year ? '· ' + esc(g.year) : ''}</p><h1>${esc(g.title)}</h1><p class="lead">${esc(g.description || '')}</p>
    <div class="row"><a class="btn small" href="/pdf/${g.slug}.pdf">Télécharger en PDF</a><a class="btn small ghost" href="/guides/">Tous les guides</a></div></header>
    ${toc ? `<details class="toc" open><summary>Sommaire</summary><ol>${toc}</ol></details>` : ''}<article>${html}</article>
    <section class="more"><h2>Autres guides</h2><div class="minis">${others}</div></section></main>`;
  const schema = { '@context': 'https://schema.org', '@type': 'Article', headline: g.title, description: g.description, inLanguage: 'fr', author: { '@type': 'Organization', name: 'Néon Bay' }, dateModified: new Date().toISOString().slice(0, 10) };
  fs.writeFileSync(path.join(out, 'guides', g.slug + '.html'), page({ title: g.title, desc: g.description || g.title, canonical: `/guides/${g.slug}.html`, body, schema }));
}
// index des guides
fs.writeFileSync(path.join(out, 'guides', 'index.html'), page({ title: 'Guides et stratégies GTA : tous les jeux de la série', desc: 'Astuces, argent, missions, police et secrets pour chaque Grand Theft Auto, de GTA 1 à GTA VI. Guides gratuits en ligne et en PDF.', canonical: '/guides/',
  body: `<main class="wrap"><header class="ahead"><p class="eyebrow">Guides gratuits</p><h1>Stratégies pour toute la série GTA</h1><p class="lead">Argent, missions, police, véhicules et secrets : un guide par jeu, à lire en ligne ou à télécharger en PDF.</p><div class="row"><a class="btn" href="/pdf/guide-complet-gta.pdf">Télécharger le guide complet (PDF)</a></div></header>
  <div class="cards">${guides.map(g => `<a class="card" href="/guides/${g.slug}.html"><span class="yr">${esc(g.year || '')}</span><b>${esc(g.game || g.title)}</b><p>${esc(g.description || '')}</p><em>Lire le guide →</em></a>`).join('')}</div>${CTA}</main>` }));

// ---------- page de vente ----------
const tpl = fs.readFileSync(path.join(site, 'landing.html'), 'utf8')
  .replace(/{{PRICE}}/g, PRICE).replace(/{{BUY_URL}}/g, BUY_URL)
  .replace('{{GUIDES}}', guides.slice(0, 6).map(g => `<a class="card" href="/guides/${g.slug}.html"><span class="yr">${esc(g.year || '')}</span><b>${esc(g.game || g.title)}</b><p>${esc(g.description || '')}</p></a>`).join(''));
fs.writeFileSync(path.join(out, 'index.html'), page({ title: 'Néon Bay : jeu d’action en monde ouvert sur mobile et PC', desc: '30 missions, 4 pays, police, gangs et poursuites. Néon Bay est un jeu indépendant d’action en monde ouvert. Niveau 1 gratuit, jeu complet ' + PRICE + '.', canonical: '/', body: tpl,
  schema: { '@context': 'https://schema.org', '@type': 'VideoGame', name: 'Néon Bay', gamePlatform: ['Web', 'Android', 'iOS'], genre: ['Action', 'Open world'], offers: { '@type': 'Offer', price: PRICE.replace(/[^\d,]/g, '').replace(',', '.'), priceCurrency: 'EUR' } } }));

// ---------- jeu, images, vidéo ----------
const web = path.join(root, 'dist-web'); if (fs.existsSync(web)) fs.cpSync(web, path.join(out, 'jouer'), { recursive: true });
const imgSrc = path.join(site, 'img'); if (fs.existsSync(imgSrc)) fs.cpSync(imgSrc, path.join(out, 'img'), { recursive: true });
const vid = path.join(root, 'marketing', 'bande-annonce-verticale.mp4'); if (fs.existsSync(vid)) fs.copyFileSync(vid, path.join(out, 'img', 'bande-annonce.mp4'));
const urls = ['/', '/guides/', ...guides.map(g => `/guides/${g.slug}.html`), '/jouer/'];
fs.writeFileSync(path.join(out, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map(u => `<url><loc>${SITE_URL}${u}</loc></url>`).join('')}</urlset>\n`);
fs.writeFileSync(path.join(out, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${SITE_URL}/sitemap.xml\n`);
console.log(`site/dist prêt : ${guides.length} guides`);

// ---------- PDF ----------
if (process.argv.includes('--no-pdf') || !guides.length) process.exit(0);
(async () => {
  const { chromium } = require('playwright');
  const b = await chromium.launch(); const p = await b.newPage();
  const files = [];
  for (const g of guides) {
    const html = fs.readFileSync(path.join(out, 'guides', g.slug + '.html'), 'utf8').replace('</head>', '<style>:root{color-scheme:light!important}.nav,.toc,.more,.cta,.row,.foot{display:none!important}html,body{background:#fff!important;color:#111!important}article,h1,h2,h3,h4,p,li,strong,em,td,th,.lead,.eyebrow{color:#111!important;text-shadow:none!important}h3{color:#b5005a!important}a{color:#0057b8!important}th{background:#eee!important}code{background:#f1f1f1!important;color:#111!important}.article{max-width:none;padding:0}</style></head>');
    await p.setContent(html, { waitUntil: 'load' }).catch(() => {});
    const f = path.join(out, 'pdf', g.slug + '.pdf');
    await p.pdf({ path: f, format: 'A4', margin: { top: '18mm', bottom: '18mm', left: '16mm', right: '16mm' }, printBackground: true, displayHeaderFooter: true, headerTemplate: '<span></span>', footerTemplate: `<div style="font-size:8px;width:100%;text-align:center;color:#888">Guide de fan non officiel · ${esc(g.game || '')} · page <span class="pageNumber"></span></div>` });
    files.push(f);
  }
  await b.close();
  try { require('child_process').execFileSync('python3', ['-c', `import sys;from pypdf import PdfWriter;w=PdfWriter();[w.append(f) for f in sys.argv[2:]];w.write(sys.argv[1])`, path.join(out, 'pdf', 'guide-complet-gta.pdf'), ...files]); } catch (e) { console.log('fusion PDF impossible :', e.message); }
  console.log(files.length + ' PDF + guide complet');
})();
