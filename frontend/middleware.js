
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

  const res = await fetch(targetUrl.toString(), {
    method: request.method,
    headers,
    body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
  });

  const resHeaders = new Headers(res.headers);
  return new Response(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers: resHeaders,
  });
}
