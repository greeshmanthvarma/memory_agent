
export const config = {
  matcher: '/api/:path*',
};

export default async function middleware(request) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return new Response(
      JSON.stringify({ error: 'Backend not configured' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const url = new URL(request.url);
  const base = backendUrl.replace(/\/$/, '');
  const targetUrl = new URL(url.pathname + url.search, base);

  const headers = new Headers(request.headers);
  headers.set('Host', new URL(backendUrl).host);


  const timeoutMs = 90000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let res;
  try {
    res = await fetch(targetUrl.toString(), {
      method: request.method,
      headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    const isTimeout = err.name === 'AbortError';
    return new Response(
      JSON.stringify({
        error: isTimeout ? 'Backend timeout' : 'Backend unreachable',
        detail: isTimeout
          ? 'Chat took too long. Try a shorter message or try again.'
          : err.message || 'Proxy could not reach BACKEND_URL',
      }),
      { status: 502, headers: { 'Content-Type': 'application/json' } }
    );
  }
  clearTimeout(timeoutId);

  const resHeaders = new Headers(res.headers);
  resHeaders.set('X-Proxied', '1');
  return new Response(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers: resHeaders,
  });
}
