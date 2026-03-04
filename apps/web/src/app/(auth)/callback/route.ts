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
        const {
          data: { user },
        } = await supabase.auth.getUser();

        if (user) {
          // Ensure user profile exists in our DB (via Supabase direct insert)
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
              avatar_url:
                user.user_metadata?.avatar_url ||
                user.user_metadata?.picture ||
                null,
              role: "member",
              is_active: true,
              onboarding_completed: false,
            });
          } else {
            // Update avatar/name from SSO if they were missing
            const updates: Record<string, string> = {};
            const name =
              user.user_metadata?.full_name || user.user_metadata?.name;
            const avatar =
              user.user_metadata?.avatar_url || user.user_metadata?.picture;
            if (name) updates.full_name = name;
            if (avatar) updates.avatar_url = avatar;

            if (Object.keys(updates).length > 0) {
              await supabase
                .from("user_profiles")
                .update(updates)
                .eq("id", user.id);
            }
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
