// Edge middleware: redirect unauthed users away from protected routes,
// and redirect already-authed users away from auth pages.
//
// Auth-state lives in localStorage (set by /lib/stores/auth-store) and is
// mirrored to a `vaktram_token` cookie so this edge function can see it.
// If the cookie is absent we never assume signed-out — the matcher only
// applies to specific paths so static + API + Next internals are excluded
// at the matcher level (cheaper than checking inside the function).

import { NextResponse, type NextRequest } from "next/server";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/meetings",
  "/settings",
  "/analytics",
  "/search",
  "/team",
  "/ask",
  "/topics",
  "/channels",
];

const AUTH_PATHS = new Set([
  "/login",
  "/signup",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
]);

export function middleware(request: NextRequest) {
  const token = request.cookies.get("vaktram_token")?.value;
  const { pathname } = request.nextUrl;

  if (!token && PROTECTED_PREFIXES.some((p) => pathname.startsWith(p))) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  if (token && AUTH_PATHS.has(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Only run middleware on the routes that actually need auth gating.
// This explicit allowlist is much safer than a regex with file-extension
// negative-lookaheads, which is what triggers MIDDLEWARE_INVOCATION_FAILED
// on certain Vercel edge runtimes.
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/meetings/:path*",
    "/settings/:path*",
    "/analytics/:path*",
    "/search/:path*",
    "/team/:path*",
    "/ask/:path*",
    "/topics/:path*",
    "/channels/:path*",
    "/login",
    "/signup",
    "/forgot-password",
    "/reset-password",
    "/verify-email",
  ],
};
