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
        // Auto-create user profile if it doesn't exist
        const {
          data: { user },
        } = await supabase.auth.getUser();

        if (user) {
          const { data: existingProfile } = await supabase
            .from("user_profiles")
            .select("id")
            .eq("id", user.id)
            .single();

          if (!existingProfile) {
            await supabase.from("user_profiles").insert({
              id: user.id,
              email: user.email,
              full_name:
                user.user_metadata?.full_name ||
                user.user_metadata?.name ||
                null,
              avatar_url: user.user_metadata?.avatar_url || null,
              role: "member",
              is_active: true,
              onboarding_completed: false,
            });
          }
        }

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
