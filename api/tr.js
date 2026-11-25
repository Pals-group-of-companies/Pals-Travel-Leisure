// Automatic translation for the website.
// GET /api/tr?l=fr&q=Some%20English%20text  ->  {"t": "..."}
// Each answer is cached by Vercel's CDN for a year, so every piece of text is translated only once per language.
// Free by default: uses the MyMemory translation service (no key, no cost).
// Optional: add ANTHROPIC_API_KEY in Vercel for more natural wording.

const LANGS = {
  sw: 'Kiswahili (Kenya)', fr: 'French', es: 'Spanish', de: 'German', pt: 'Portuguese (Portugal)',
  it: 'Italian', zh: 'Simplified Chinese', ru: 'Russian', ar: 'Modern Standard Arabic'
};

let site = { at: 0, text: '' };
async function siteText(host) {
  // Only text that really appears on the website is translated, so the service cannot be used for anything else.
  if (Date.now() - site.at < 10 * 60 * 1000 && site.text) return site.text;
  try {
    const r = await fetch('https://' + host + '/index.html', { headers: { 'x-pals-tr': '1' } });
    if (r.ok) site = { at: Date.now(), text: await r.text() };
  } catch (e) {}
  return site.text;
}
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

module.exports = async (req, res) => {
  const l = String(req.query.l || '');
  const q = String(req.query.q || '').replace(/\s+/g, ' ').trim().slice(0, 300);
  if (!LANGS[l] || q.length < 2) return res.status(400).json({ error: 'bad request' });
  const key = process.env.ANTHROPIC_API_KEY;

  const text = await siteText(req.headers.host);
  const words = q.split(' ').filter((w) => w.length > 3).slice(0, 4);
  const onSite = text && (text.includes(q) || text.includes(esc(q)) || (words.length && words.every((w) => text.includes(w) || text.includes(esc(w)))));
  if (!onSite) return res.status(404).json({ error: 'unknown text' });

  if (!key) {
    // Free service. With an email address the daily allowance is about 50,000 characters, and the CDN cache
    // below means each sentence is only ever requested once per language.
    const MM = { sw: 'sw', fr: 'fr', es: 'es', de: 'de', pt: 'pt-PT', it: 'it', zh: 'zh-CN', ru: 'ru', ar: 'ar' };
    try {
      const u = 'https://api.mymemory.translated.net/get?q=' + encodeURIComponent(q) + '&langpair=en|' + MM[l] + '&de=' + encodeURIComponent(process.env.TRANSLATE_EMAIL || 'info@palstravelleisure.co.ke');
      const r = await fetch(u);
      const j = await r.json();
      const t = j && j.responseData && String(j.responseData.translatedText || '').trim();
      if (!r.ok || !t || j.responseStatus != 200 || /MYMEMORY WARNING|QUERY LENGTH LIMIT|INVALID/i.test(t)) return res.status(502).json({ error: 'translation failed' });
      res.setHeader('Cache-Control', 'public, max-age=86400, s-maxage=31536000, stale-while-revalidate=604800');
      return res.status(200).json({ t });
    } catch (e) {
      return res.status(502).json({ error: 'translation failed' });
    }
  }

  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      body: JSON.stringify({
        model: process.env.TRANSLATE_MODEL || 'claude-haiku-5-5',
        max_tokens: 700,
        system: 'You translate short pieces of text from the website of Pals Travel & Leisure, a travel company in Nairobi, Kenya, into ' + LANGS[l] + '. ' +
          'Write natural, warm, clear wording a native speaker would expect on a professional travel website. Keep the same length and tone. ' +
          'Do not translate brand names, hotel names, school names, place names, prices, numbers, codes, email addresses or phone numbers. ' +
          'If the text is only a name or cannot be translated, return it unchanged. Reply with the translation only, no quotes and no notes.',
        messages: [{ role: 'user', content: q }]
      })
    });
    if (!r.ok) return res.status(502).json({ error: 'translation failed' });
    const j = await r.json();
    const t = (j.content || []).map((c) => c.text || '').join('').trim();
    if (!t) return res.status(502).json({ error: 'empty' });
    res.setHeader('Cache-Control', 'public, max-age=86400, s-maxage=31536000, stale-while-revalidate=604800');
    return res.status(200).json({ t });
  } catch (e) {
    return res.status(502).json({ error: 'translation failed' });
  }
};
