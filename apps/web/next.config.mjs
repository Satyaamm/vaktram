/** @type {import('next').NextConfig} */

// Build the Content-Security-Policy from a structured map so additions stay
// readable. Each directive lists the origins permitted for that resource.
//
// Why each entry exists:
//   default-src 'self'              — fall-through for anything not listed
//   script-src 'self' 'unsafe-inline' 'unsafe-eval'
//                                    — Next.js inlines runtime + dev tools
//                                      use eval. unsafe-* is unfortunate but
//                                      moving to nonces is a bigger refactor;
//                                      tracked separately.
//   style-src 'self' 'unsafe-inline' — Tailwind/shadcn rely on inline styles
//                                      for runtime variants
//   img-src 'self' data: blob: https:
//                                    — avatars + user-uploaded image previews
//   connect-src 'self' + API + WS    — fetch() to Render API and WS server
//   font-src 'self' data:            — embedded fonts from Tailwind
//   frame-ancestors 'none'           — defense-in-depth against clickjacking
//   form-action 'self'               — forms only POST same-origin
//   base-uri 'self'                  — block <base> override hijacks
//   object-src 'none'                — no Flash/PDF/embed bypass tricks
//   upgrade-insecure-requests        — auto-rewrite http: to https: in prod
const apiOrigin = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const wsOrigin = apiOrigin
  .replace(/^http:\/\//, "ws://")
  .replace(/^https:\/\//, "wss://");

const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "img-src 'self' data: blob: https:",
  `connect-src 'self' ${apiOrigin} ${wsOrigin} https://*.upstash.io`,
  "font-src 'self' data: https://fonts.gstatic.com",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "upgrade-insecure-requests",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  // 1 year HSTS with subdomain inclusion. Cannot be undone for that period
  // for visitors who already received the header — we are committing to TLS
  // on this domain and all subdomains. Safe because Vercel terminates TLS.
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains; preload" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // Block geolocation, camera, mic, and the FLoC interest cohort by default.
  // The bot does its own thing on the VPS; the dashboard never needs them.
  {
    key: "Permissions-Policy",
    value: "geolocation=(), microphone=(), camera=(), interest-cohort=()",
  },
];

const nextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
