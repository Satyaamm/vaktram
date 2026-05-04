import type { Metadata } from "next";
import "./globals.css";

import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";

// SITE_URL drives the canonical URL embedded in OG/Twitter cards. On Vercel
// without a custom domain, set NEXT_PUBLIC_SITE_URL to your project's
// deployment URL (e.g. https://vaktram-website.vercel.app). Falls back to
// VERCEL_URL (auto-set by Vercel) so previews still produce valid metadata,
// then to localhost for dev.
const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ||
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3001");

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Vaktram — AI meeting notes on the model you choose",
    template: "%s · Vaktram",
  },
  description:
    "Vaktram joins your Google Meet, Zoom, and Teams calls and turns them into searchable transcripts and summaries — using your own LLM provider. No model lock-in, your keys, your data.",
  openGraph: {
    title: "Vaktram — AI meeting notes on the model you choose",
    description:
      "Bring your own model. Self-hosted bot. Searchable transcripts and summaries.",
    type: "website",
    url: SITE_URL,
    siteName: "Vaktram",
  },
  twitter: {
    card: "summary_large_image",
    title: "Vaktram — AI meeting notes on the model you choose",
    description:
      "Bring your own model. Self-hosted bot. Searchable transcripts and summaries.",
  },
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white">
        <SiteNav />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
