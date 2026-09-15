/**
 * Serverless proxy for GET /api/memory so the request can run longer than Edge limit (~30s).
 * Listing memories (with Qdrant) can be slow; this function has a 60s timeout.
 */
import type { VercelRequest, VercelResponse } from '@vercel/node'

export const config = { maxDuration: 60 }

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET')
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl) {
    return res.status(503).json({ error: 'Backend not configured' })
  }

  const base = backendUrl.replace(/\/$/, '')
  const reqUrl = req.url ?? ''
  const query = reqUrl.includes('?') ? reqUrl.slice(reqUrl.indexOf('?')) : ''
  // Trailing slash matches the FastAPI route so Node fetch does not follow a
  // 307 and drop the Cookie header.
  const targetUrl = `${base}/api/memory/${query}`

  const headers: Record<string, string> = { Host: new URL(backendUrl).host }
  if (req.headers.cookie) headers['Cookie'] = req.headers.cookie as string

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 55000)

    let response = await fetch(targetUrl, {
      method: 'GET',
      headers,
      redirect: 'manual',
      signal: controller.signal,
    })

    const redirectStatus = response.status
    if (redirectStatus >= 300 && redirectStatus < 400) {
      const location = response.headers.get('location')
      if (location) {
        response = await fetch(new URL(location, targetUrl).toString(), {
          method: 'GET',
          headers,
          redirect: 'manual',
          signal: controller.signal,
        })
      }
    }

    clearTimeout(timeoutId)

    const data = await response.text()
    const contentType = response.headers.get('content-type') || 'application/json'
    res.setHeader('Content-Type', contentType)
    res.setHeader('X-Proxied', '1')
    res.status(response.status).send(data)
  } catch (err) {
    const error = err as Error
    const isTimeout = error.name === 'AbortError'
    res.status(502).json({
      error: isTimeout ? 'Backend timeout' : 'Backend unreachable',
      detail: isTimeout
        ? 'Request took too long.'
        : error.message || 'Proxy could not reach backend',
    })
  }
}
