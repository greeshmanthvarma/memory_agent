/**
 * Serverless proxy for POST /api/chat so the request can run longer than Edge limit (~30s).
 * Chat (LLM) often takes 30–90s; this function has a 60s timeout.
 * Streams the backend response to the client so tokens appear as they arrive.
 */
import { Readable } from 'stream';

export const config = { maxDuration: 60 };

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return res.status(503).json({ error: 'Backend not configured' });
  }

  const base = backendUrl.replace(/\/$/, '');
  const targetUrl = `${base}/api/chat`;

  const headers = {
    'Content-Type': req.headers['content-type'] || 'application/json',
    Host: new URL(backendUrl).host,
  };
  if (req.headers.cookie) headers.Cookie = req.headers.cookie;

  let body;
  try {
    body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body ?? {});
  } catch {
    body = '{}';
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000);

    const response = await fetch(targetUrl, {
      method: 'POST',
      headers,
      body,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const contentType = response.headers.get('content-type') || 'text/plain';
    res.setHeader('Content-Type', contentType);
    res.setHeader('X-Proxied', '1');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.status(response.status);

    const nodeStream = Readable.fromWeb(response.body);
    nodeStream.pipe(res);
  } catch (err) {
    const isTimeout = err.name === 'AbortError';
    res.status(502).json({
      error: isTimeout ? 'Backend timeout' : 'Backend unreachable',
      detail: isTimeout
        ? 'Chat took too long. Try a shorter message or try again.'
        : err.message || 'Proxy could not reach backend',
    });
  }
}
