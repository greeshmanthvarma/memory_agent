/**
 * Serverless proxy for GET /api/memory so the request can run longer than Edge limit (~30s).
 * Listing memories (with Qdrant) can be slow; this function has a 60s timeout.
 */
export const config = { maxDuration: 60 };

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return res.status(503).json({ error: 'Backend not configured' });
  }

  const base = backendUrl.replace(/\/$/, '');
  const targetUrl = `${base}/api/memory${req.url.includes('?') ? req.url.slice(req.url.indexOf('?')) : ''}`;

  const headers = { Host: new URL(backendUrl).host };
  if (req.headers.cookie) headers.Cookie = req.headers.cookie;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000);

    const response = await fetch(targetUrl, {
      method: 'GET',
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const data = await response.text();
    const contentType = response.headers.get('content-type') || 'application/json';
    res.setHeader('Content-Type', contentType);
    res.setHeader('X-Proxied', '1');
    res.status(response.status).send(data);
  } catch (err) {
    const isTimeout = err.name === 'AbortError';
    res.status(502).json({
      error: isTimeout ? 'Backend timeout' : 'Backend unreachable',
      detail: isTimeout
        ? 'Request took too long.'
        : err.message || 'Proxy could not reach backend',
    });
  }
}
