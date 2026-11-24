import { createRemoteJWKSet, jwtVerify } from 'jose';

const keySets = new Map();
const deny = (code, status = 401) => Response.json({ error: code }, { status });

export function readConfig(env) {
  const issuer = String(env.ACCESS_TEAM_DOMAIN || '').replace(/\/$/, '');
  const audience = String(env.ACCESS_AUD || '').trim();
  const emails = new Set(String(env.ADMIN_EMAILS || '').split(',').map(s => s.trim().toLowerCase()).filter(Boolean));
  const origin = String(env.ADMIN_ORIGIN || '').replace(/\/$/, '');
  // Configuration is server-owned. Neither token claims nor request headers choose the key server.
  if (!/^https:\/\/[a-z0-9-]+\.cloudflareaccess\.com$/.test(issuer)
      || !audience || !emails.size || [...emails].some(e => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e))
      || !/^https:\/\/[^/?#]+$/.test(origin) || !URL.canParse(origin) || new URL(origin).origin !== origin) return null;
  return { issuer, audience, emails, origin };
}

export async function verifyIdentity(request, config, keyResolver) {
  const token = request.headers.get('Cf-Access-Jwt-Assertion');
  if (!token || token.length > 16384) return null;
  try {
    let key = keyResolver;
    if (!key) {
      if (!keySets.has(config.issuer)) keySets.set(config.issuer, createRemoteJWKSet(new URL(config.issuer + '/cdn-cgi/access/certs'), { timeoutDuration: 5000 }));
      key = keySets.get(config.issuer);
    }
    const { payload } = await jwtVerify(token, key, {
      issuer: config.issuer, audience: config.audience, algorithms: ['RS256'],
      requiredClaims: ['exp', 'iat', 'sub', 'email'], clockTolerance: 5, maxTokenAge: '2h',
    });
    const email = typeof payload.email === 'string' ? payload.email.toLowerCase().trim() : '';
    // A valid Google/Access identity alone does not grant CMS access.
    if (typeof payload.sub !== 'string' || !payload.sub || !config.emails.has(email)) return null;
    return { email, role: 'admin', expiresAt: payload.exp * 1000 };
  } catch { return null; }
}

function harden(response) {
  const headers = new Headers(response.headers);
  headers.set('Cache-Control', 'private, no-store');
  headers.set('Vary', 'Cf-Access-Jwt-Assertion, Cookie');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('X-Frame-Options', 'DENY');
  headers.set('Referrer-Policy', 'no-referrer');
  headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  headers.set('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https: data: blob:; connect-src 'self'; frame-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'");
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

export function createHandler({ keyResolver } = {}) {
  return async (request, env) => {
    const respond = harden;
    const config = readConfig(env);
    // Incomplete setup never exposes the workspace, even on an alternate hostname.
    if (!config) return respond(deny('AUTH_NOT_CONFIGURED', 503));
    const url = new URL(request.url);
    if (url.origin !== config.origin) return respond(deny('HOST_NOT_ALLOWED', 403));
    const identity = await verifyIdentity(request, config, keyResolver);
    if (!identity) return respond(deny('ADMIN_ACCESS_REQUIRED', 401));
    const path = url.pathname;
    if (path === '/api/admin/session') {
      if (request.method !== 'GET') return respond(deny('METHOD_NOT_ALLOWED', 405));
      return respond(Response.json({ authenticated: true, user: identity, publishingEnabled: false }));
    }
    if (path === '/api/admin/logout') {
      if (request.method !== 'POST') return respond(deny('METHOD_NOT_ALLOWED', 405));
      if (request.headers.get('Origin') !== config.origin) return respond(deny('ORIGIN_NOT_ALLOWED', 403));
      // Access owns the HttpOnly session cookie and server-side revocation.
      return respond(Response.json({ logoutUrl: config.origin + '/cdn-cgi/access/logout' }));
    }
    if (path.startsWith('/api/')) return respond(deny('NOT_FOUND', 404));
    if (!['GET', 'HEAD'].includes(request.method)) return respond(deny('METHOD_NOT_ALLOWED', 405));
    if (path === '/' || path === '/admin' || path === '/admin/' || path === '/admin/index.html')
      return respond(Response.redirect(config.origin + '/admin/workspace.html', 302));
    if (path === '/admin/auth.json') return respond(Response.json({ enabled: true, mode: 'cloudflare-access', serviceUrl: config.origin }));
    // Only ship assets used by the CMS. Demo routes and public decap test mode are not production entry points.
    const allowed = new Set(['/admin/workspace.html', '/admin/admin.css', '/admin/admin.js', '/admin/core.js', '/admin/session.js', '/content/site.json']);
    const mediaPath = path.startsWith('/littlescholar-demo/uploads/wix/') ? path.replace('/littlescholar-demo', '') : path;
    if (!allowed.has(path) && !/^\/uploads\/wix\/[a-f0-9]+\.webp$/.test(mediaPath)) return respond(deny('NOT_FOUND', 404));
    const assetUrl = new URL(request.url); assetUrl.pathname = mediaPath;
    const response = await env.ASSETS.fetch(new Request(assetUrl, request));
    return respond(response);
  };
}
export default { fetch: createHandler() };
