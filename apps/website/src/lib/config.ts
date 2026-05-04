// One source of truth for outbound URLs. Buttons in the marketing site
// route to APP_URL/login etc.; OG metadata uses SITE_URL.
//
// Both can be overridden via Vercel env vars at build time. The fallbacks
// below are the *production-deployed* Vercel URLs — they work today even
// before the user owns vaktram.com — so a build with no env config still
// links the user somewhere real.

export const APP_URL =
  process.env.NEXT_PUBLIC_APP_URL || "https://vaktram-web.vercel.app";

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ||
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3001");
