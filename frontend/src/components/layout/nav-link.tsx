"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "next";

import { cn } from "@/lib/utils";

type NavLinkProps = {
  href: Route;
  label: string;
  eyebrow: string;
  description: string;
};

export function NavLink({ href, label, eyebrow, description }: NavLinkProps) {
  const pathname = usePathname();
  const active = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        "block rounded-[1.5rem] border px-4 py-4 transition duration-200",
        active
          ? "border-pine bg-pine text-white shadow-panel"
          : "border-transparent bg-white/50 text-ink hover:border-[color:var(--border)] hover:bg-white/80",
      )}
    >
      <p
        className={cn(
          "text-[11px] font-semibold uppercase tracking-[0.28em]",
          active ? "text-white/70" : "text-slate-500",
        )}
      >
        {eyebrow}
      </p>
      <p className="mt-2 text-lg font-semibold">{label}</p>
      <p className={cn("mt-2 text-sm leading-6", active ? "text-white/80" : "text-slate-600")}>
        {description}
      </p>
    </Link>
  );
}
