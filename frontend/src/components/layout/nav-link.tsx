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
  const active =
    href === "/" ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={cn(
        "block rounded-[1.15rem] border px-3.5 py-3 transition duration-200",
        active
          ? "border-zinc-900 bg-zinc-900 text-white shadow-panel"
          : "border-transparent bg-transparent text-ink hover:border-[color:var(--border)] hover:bg-white",
      )}
    >
      <p
        className={cn(
          "text-[10px] font-semibold uppercase tracking-[0.22em]",
          active ? "text-white/60" : "text-zinc-400",
        )}
      >
        {eyebrow}
      </p>
      <p className="mt-1 text-base font-semibold">{label}</p>
      <p className={cn("mt-1 text-xs leading-5", active ? "text-white/70" : "text-zinc-500")}>
        {description}
      </p>
    </Link>
  );
}
