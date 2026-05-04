"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

// Logo wordmarks. The PNGs live in /public so this picks them up
// automatically once the assets are dropped in:
//   apps/web/public/logo-long.png    (horizontal wordmark, ~32-40px tall)
//   apps/web/public/logoshort.png    (square mark, used as favicon too)
//
// If the PNG is missing the component falls back to a minimal text+badge
// version so the site never renders broken-image icons. Swap the two
// files at any time — no code change needed.

interface LogoProps {
  variant?: "long" | "short";
  className?: string;
  // Tone controls the fallback colours for the text wordmark.
  tone?: "dark" | "light";
  href?: string;
  width?: number;
  height?: number;
}

export function Logo({
  variant = "long",
  className = "",
  tone = "dark",
  href = "/",
  width,
  height,
}: LogoProps) {
  const [errored, setErrored] = useState(false);
  const src = variant === "long" ? "/logo-long.png" : "/logoshort.png";

  const inner = errored ? (
    <FallbackMark variant={variant} tone={tone} />
  ) : (
    <Image
      src={src}
      alt="Vaktram"
      width={width ?? (variant === "long" ? 144 : 32)}
      height={height ?? 32}
      priority
      onError={() => setErrored(true)}
      className={variant === "long" ? "h-8 w-auto" : "h-8 w-8"}
    />
  );

  if (!href) return <span className={className}>{inner}</span>;
  return (
    <Link href={href} className={`inline-flex items-center ${className}`}>
      {inner}
    </Link>
  );
}

function FallbackMark({
  variant,
  tone,
}: {
  variant: "long" | "short";
  tone: "dark" | "light";
}) {
  const badgeBg = tone === "dark" ? "bg-white text-slate-950" : "bg-slate-950 text-white";
  const wordTone = tone === "dark" ? "text-white" : "text-slate-950";

  if (variant === "short") {
    return (
      <span
        className={`flex h-8 w-8 items-center justify-center rounded-md text-sm font-bold ${badgeBg}`}
      >
        V
      </span>
    );
  }
  return (
    <span className="flex items-center gap-2.5">
      <span
        className={`flex h-8 w-8 items-center justify-center rounded-md text-sm font-bold ${badgeBg}`}
      >
        V
      </span>
      <span className={`text-[17px] font-semibold tracking-tight ${wordTone}`}>
        Vaktram
      </span>
    </span>
  );
}
