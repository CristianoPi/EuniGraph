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
    description: "Run seed, normalization, embeddings and graph build workflows.",
  },
  {
    href: "/admin/data-entry" as Route,
    label: "Manual Data Entry",
    description: "Create canonical publications, researchers and organizations.",
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
              "rounded-[1.5rem] border px-5 py-4 transition",
              active
                ? "border-pine bg-pine text-white shadow-panel"
                : "border-[color:var(--border)] bg-white/70 text-ink hover:border-pine/40",
            )}
          >
            <p className="text-base font-semibold">{section.label}</p>
            <p className={cn("mt-2 text-sm leading-6", active ? "text-white/80" : "text-slate-600")}>
              {section.description}
            </p>
          </Link>
        );
      })}
    </nav>
  );
}
