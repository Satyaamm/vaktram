import { redirect } from "next/navigation";

// app.vaktram.com is the dashboard surface only — the marketing site lives
// at vaktram.com (apps/website). Visiting `/` here is a stale tab or a
// link that wasn't updated; bounce them to /login so the auth-aware
// middleware can take over from there.
export default function Root() {
  redirect("/login");
}
