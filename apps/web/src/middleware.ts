// Edge middleware: gate protected routes on the presence of a session-hint
// cookie, and bounce already-signed-in users away from auth pages.
//
// Auth state lives in:
//   • `vaktram_refresh` — HttpOnly cookie on the API domain. The browser
//     attaches it automatically; this middleware can NOT see it (different
//     registrable domain).
//   • `vaktram_session` — a non-HttpOnly hint cookie set by the API on the
//     same response. Value is just "1"; it carries no credential. We use
//     it here purely to avoid flashing the dashboard for visibly-signed-out
//     users. The real auth check is the JWT on every API call.
//
// Important: the hint cookie is also on the API origin, NOT the Vercel
// origin, so this middleware in fact cannot see it either. We therefore
// fall back to client-side guarding: the dashboard layout calls
// `bootstrapSession()` and redirects to /login if it returns null. The
// middleware below only matches the auth pages so signed-in users don't
// get stuck on /login if they revisit the URL.

import { NextResponse, type NextRequest } from "next/server";

const AUTH_PATHS = new Set([
  "/login",
  "/signup",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
]);

export function middleware(request: NextRequest) {
  // The session-hint cookie may not be reachable cross-origin, so this
  // check only catches the same-origin case (e.g. a future custom domain).
  // The real gate is in the dashboard layout's client-side bootstrap.
  const hasHint = Boolean(request.cookies.get("vaktram_session")?.value);
  const { pathname } = request.nextUrl;

  if (hasHint && AUTH_PATHS.has(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/signup",
    "/forgot-password",
    "/reset-password",
    "/verify-email",
  ],
};
