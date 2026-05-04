import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";

// Wraps every public marketing page (/, /product, /pricing, /customers,
// /security, /about, /contact, /privacy, /terms) with the same nav +
// footer. Auth pages and dashboard pages are in sibling route groups so
// they get their own layouts (no marketing chrome).

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteNav />
      {children}
      <SiteFooter />
    </>
  );
}
