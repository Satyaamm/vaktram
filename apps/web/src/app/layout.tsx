import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { Toaster } from "@/components/ui/toaster";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: {
    default: "Vaktram — AI meeting notes on the model you choose",
    template: "%s · Vaktram",
  },
  description:
    "Transcribe, summarize, and extract action items from your meetings. Bring your own LLM for complete privacy and control.",
  // Favicon is generated automatically by Next.js from these files:
  //   apps/web/src/app/icon.png         → browser tab + most surfaces
  //   apps/web/src/app/apple-icon.png   → iOS home screen
  // Drop the same logoshort.png at both paths and Next handles the rest.
  // No manual conversion, no metadata wiring required. The default
  // Next.js favicon.ico has been removed so an unbranded tab is the
  // worst case until your assets land.
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
