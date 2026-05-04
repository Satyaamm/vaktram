"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS: { label: string; href: string }[] = [
  { label: "Product", href: "/product" },
  { label: "Pricing", href: "/pricing" },
  { label: "Customers", href: "/customers" },
  { label: "Security", href: "/security" },
  { label: "About", href: "/about" },
];

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://app.vaktram.com";

export function SiteNav() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 w-full transition-colors duration-200",
        scrolled
          ? "border-b border-slate-200/70 bg-white/85 backdrop-blur"
          : "border-b border-transparent bg-transparent",
      )}
    >
      <nav className="container-wide flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-950 text-sm font-bold text-white">
            V
          </span>
          <span className="text-[17px] font-semibold tracking-tight text-slate-900">
            Vaktram
          </span>
        </Link>

        <ul className="hidden items-center gap-8 md:flex">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className="text-[14px] font-medium text-slate-700 transition-colors hover:text-slate-950"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-3 md:flex">
          <Link
            href={`${APP_URL}/login`}
            className="text-[14px] font-medium text-slate-700 transition-colors hover:text-slate-950"
          >
            Sign in
          </Link>
          <Link
            href="/contact"
            className="inline-flex items-center rounded-md bg-slate-950 px-4 py-2 text-[14px] font-semibold text-white shadow-sm transition-all hover:bg-slate-800"
          >
            Book a demo
          </Link>
        </div>

        <button
          className="md:hidden"
          onClick={() => setMobileOpen((s) => !s)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {mobileOpen && (
        <div className="border-t border-slate-200 bg-white md:hidden">
          <ul className="container-wide flex flex-col gap-1 py-4">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="block rounded-md px-3 py-2 text-[15px] font-medium text-slate-700 hover:bg-slate-50"
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li className="mt-2 flex gap-2 px-1">
              <Link
                href={`${APP_URL}/login`}
                className="flex-1 rounded-md border border-slate-200 px-4 py-2 text-center text-[14px] font-semibold text-slate-700"
              >
                Sign in
              </Link>
              <Link
                href="/contact"
                className="flex-1 rounded-md bg-slate-950 px-4 py-2 text-center text-[14px] font-semibold text-white"
              >
                Book a demo
              </Link>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
