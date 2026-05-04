import Link from "next/link";

const COLUMNS: { title: string; links: { label: string; href: string }[] }[] = [
  {
    title: "Product",
    links: [
      { label: "Overview", href: "/product" },
      { label: "Pricing", href: "/pricing" },
      { label: "Security", href: "/security" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Customers", href: "/customers" },
      { label: "About", href: "/about" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="container-wide grid grid-cols-2 gap-10 py-16 md:grid-cols-5">
        <div className="col-span-2">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-950 text-sm font-bold text-white">
              V
            </span>
            <span className="text-[17px] font-semibold tracking-tight text-slate-900">
              Vaktram
            </span>
          </Link>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-slate-600">
            AI meeting notes that work for you, on the model you choose. Built
            in India.
          </p>
        </div>

        {COLUMNS.map((col) => (
          <div key={col.title}>
            <p className="text-[12px] font-semibold uppercase tracking-wider text-slate-500">
              {col.title}
            </p>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-700 transition-colors hover:text-slate-950"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-slate-200">
        <div className="container-wide flex flex-col items-center justify-between gap-3 py-6 md:flex-row">
          <p className="text-xs text-slate-500">
            &copy; {new Date().getFullYear()} Vaktram. All rights reserved.
          </p>
          <p className="inline-flex items-center gap-1.5 text-xs text-slate-500">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            All systems operational
          </p>
        </div>
      </div>
    </footer>
  );
}
