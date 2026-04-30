import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("vaktram_token")?.value;
  const pathname = request.nextUrl.pathname;

  const isProtectedRoute =
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/meetings") ||
    pathname.startsWith("/settings") ||
    pathname.startsWith("/analytics") ||
    pathname.startsWith("/search") ||
    pathname.startsWith("/team");

  if (isProtectedRoute && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  const isAuthRoute =
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password";

  if (isAuthRoute && token) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
