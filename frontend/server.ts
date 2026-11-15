import { serve } from 'bun';
import path from 'path';

const PORT = 5173;
const HOST = '0.0.0.0';
const BACKEND_URL = 'http://127.0.0.1:8000';
const DIST_DIR = path.resolve(__dirname, 'dist');

console.log(`[luco-web] Memulai server produksi Bun di http://${HOST}:${PORT}`);
console.log(`[luco-web] Melayani berkas statis dari: ${DIST_DIR}`);
console.log(`[luco-web] Proksi backend /v1 dan /health mengarah ke: ${BACKEND_URL}`);

serve({
  port: PORT,
  hostname: HOST,
  async fetch(req) {
    const url = new URL(req.url);

    // 1. Proksi API backend (/v1/* dan /health)
    if (url.pathname.startsWith('/v1') || url.pathname === '/health') {
      const targetUrl = `${BACKEND_URL}${url.pathname}${url.search}`;
      try {
        const headers = new Headers(req.headers);
        headers.set('host', '127.0.0.1:8000');
        headers.set('x-forwarded-for', req.headers.get('x-forwarded-for') || '127.0.0.1');
        headers.set('x-forwarded-proto', url.protocol.replace(':', ''));

        const proxyRes = await fetch(targetUrl, {
          method: req.method,
          headers,
          body: req.method !== 'GET' && req.method !== 'HEAD' ? req.body : undefined,
          // @ts-ignore
          duplex: 'half',
        });

        const resHeaders = new Headers(proxyRes.headers);
        // Pastikan CORS tetap diizinkan
        resHeaders.set('Access-Control-Allow-Origin', req.headers.get('origin') || '*');
        resHeaders.set('Access-Control-Allow-Credentials', 'true');

        return new Response(proxyRes.body, {
          status: proxyRes.status,
          statusText: proxyRes.statusText,
          headers: resHeaders,
        });
      } catch (err: any) {
        console.error(`[luco-web] Gagal meneruskan permintaan ke ${targetUrl}:`, err?.message);
        return new Response(JSON.stringify({ detail: 'Backend service unavailable' }), {
          status: 502,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    // 2. Berkas Statis dari folder dist/
    const safePath = path.normalize(url.pathname).replace(/^(\.\.[\/\\])+/, '');
    const candidatePath = path.join(DIST_DIR, safePath === '/' ? 'index.html' : safePath);

    const file = Bun.file(candidatePath);
    if (await file.exists()) {
      const headers = new Headers();
      // Cache panjang untuk berkas bundel ter-hash di /assets/
      if (url.pathname.startsWith('/assets/')) {
        headers.set('Cache-Control', 'public, max-age=31536000, immutable');
      } else {
        headers.set('Cache-Control', 'no-cache');
      }
      return new Response(file, { headers });
    }

    // 3. SPA Fallback: Untuk routing client-side (misal ?session=...), layani index.html
    const indexFile = Bun.file(path.join(DIST_DIR, 'index.html'));
    return new Response(indexFile, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache',
      },
    });
  },
});
