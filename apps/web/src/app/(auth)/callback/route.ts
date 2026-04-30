import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { origin } = new URL(request.url);
  // With custom JWT auth, there's no OAuth callback flow.
  // Redirect to dashboard (middleware will send to login if not authenticated).
  return NextResponse.redirect(`${origin}/dashboard`);
}
