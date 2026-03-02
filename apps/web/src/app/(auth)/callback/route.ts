import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  if (code) {
    const supabase = createClient();

    try {
      const { error } = await supabase.auth.exchangeCodeForSession(code);

      if (!error) {
        return NextResponse.redirect(`${origin}${next}`);
      }

      console.error("Auth callback error:", error.message);
    } catch (err) {
      console.error("Auth callback exception:", err);
    }
  }

  // Return the user to the login page with an error indicator
  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}
