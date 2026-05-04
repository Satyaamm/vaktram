# Deploying the marketing site

This is the public marketing site (`vaktram.com` once you own it). For now
it deploys to a Vercel-provided URL like `vaktram-website.vercel.app`.

## One-time: create the Vercel project

1. **Vercel dashboard** → **Add New Project** → import `Satyaamm/vaktram`.
2. **Root Directory**: `apps/website`
3. **Framework**: Next.js (auto-detected)
4. **Install Command**: `npm install` (default)
5. **Build Command**: `npm run build` (default)
6. **Output Directory**: `.next` (default)

## Environment variables (Vercel → Project → Settings → Environment Variables)

The site has two outbound links that depend on env vars. If they aren't set,
the buttons will fall through to `https://app.vaktram.com` placeholders that
you don't own — set these correctly so login/signup CTAs route to your real
dashboard.

| Var | Value | Why |
|---|---|---|
| `NEXT_PUBLIC_APP_URL` | Your dashboard's Vercel URL, e.g. `https://vaktram.vercel.app` | Drives every "Sign in" / "Start free" / "Book a demo" button. Must point at `apps/web` (the dashboard), NOT this site. |
| `NEXT_PUBLIC_SITE_URL` | This site's own URL, e.g. `https://vaktram-website.vercel.app` | Used in OG/Twitter card metadata. Optional — falls back to `VERCEL_URL` (auto-set per deploy). |
| `NEXT_PUBLIC_CONTACT_ENDPOINT` | Optional. URL that receives POSTed contact form JSON. | If unset, the contact form falls back to `mailto:hello@vaktram.com`. |

Set scope to **Production, Preview, Development** unless you want preview
deploys to point at a staging dashboard.

## Verify routing after deploy

1. Open the deployed URL.
2. Click **Sign in** in the top-right → must land on `<NEXT_PUBLIC_APP_URL>/login`
3. Click **Start free** in the hero → must land on `<NEXT_PUBLIC_APP_URL>/signup`
4. Click **Book a demo** → must land on this site's `/contact`.

If a CTA still shows `app.vaktram.com` in the URL bar, you didn't set
`NEXT_PUBLIC_APP_URL` and Vercel is using the build-time fallback. Set it
and trigger a redeploy.

## The matching env var on the dashboard project

On your `apps/web` Vercel project, set:

| Var | Value |
|---|---|
| `NEXT_PUBLIC_WEBSITE_URL` | This site's URL, e.g. `https://vaktram-website.vercel.app` |
| `NEXT_PUBLIC_API_URL` | The API URL, e.g. `https://vaktram-api.onrender.com` |
| `NEXT_PUBLIC_APP_URL` | The dashboard's own URL, e.g. `https://vaktram.vercel.app` |

That makes the auth pages link Terms/Privacy/Home back to this site
correctly, and lets the API client know where to call.

## Custom domain (later)

Once you own `vaktram.com`:
1. Add it as a custom domain to **this** Vercel project.
2. Add `app.vaktram.com` to the dashboard project.
3. Update `NEXT_PUBLIC_APP_URL` → `https://app.vaktram.com`
4. Update `NEXT_PUBLIC_WEBSITE_URL` (on the dashboard) → `https://vaktram.com`
5. Update `FRONTEND_BASE_URL` (on Render API) → `https://app.vaktram.com` so
   verification email links point at the new domain.
