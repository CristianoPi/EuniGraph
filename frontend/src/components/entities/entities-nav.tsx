"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "next";

import { cn } from "@/lib/utils";

const entitySections: Array<{
  href: Route;
  label: string;
}> = [
  { href: "/entities", label: "Overview" },
  { href: "/entities/publications", label: "Publications" },
  { href: "/entities/researchers", label: "Researchers" },
  { href: "/entities/organizations", label: "Organizations" },
];

export function EntitiesNav() {
  const pathname = usePathname();

  return (
    <div className="flex flex-wrap gap-3">
      {entitySections.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-full border px-4 py-2 text-sm font-semibold transition",
              active
                ? "border-zinc-900 bg-zinc-900 text-white"
                : "border-[color:var(--border)] bg-white text-zinc-600 hover:border-zinc-300 hover:text-ink",
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </div>
  );
}
