"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "next";

import { cn } from "@/lib/utils";

const adminSections: Array<{
  href: Route;
  label: string;
  description: string;
}> = [
  {
    href: "/admin/operations" as Route,
    label: "Operations",
    description: "Seed, normalize, embed, build.",
  },
  {
    href: "/admin/data-entry" as Route,
    label: "Manual Data Entry",
    description: "Create canonical records.",
  },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav className="grid gap-3 md:grid-cols-2">
      {adminSections.map((section) => {
        const active = pathname === section.href || pathname.startsWith(`${section.href}/`);

        return (
          <Link
            key={section.href}
            href={section.href}
            className={cn(
              "rounded-[1.25rem] border px-5 py-4 transition",
              active
                ? "border-zinc-900 bg-zinc-900 text-white shadow-panel"
                : "border-[color:var(--border)] bg-white text-ink hover:border-zinc-300",
            )}
          >
            <p className="text-base font-semibold">{section.label}</p>
            <p className={cn("mt-1 text-sm leading-6", active ? "text-white/70" : "text-zinc-500")}>
              {section.description}
            </p>
          </Link>
        );
      })}
    </nav>
  );
}
