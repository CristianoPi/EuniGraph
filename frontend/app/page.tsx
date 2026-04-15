import Link from "next/link";
import type { Route } from "next";

import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { SystemOverview } from "@/components/widgets/system-overview";

const entryPoints: Array<{
  href: Route;
  title: string;
  description: string;
}> = [
  {
    href: "/dashboard",
    title: "Dashboard",
    description: "Catalog size, workflow status and quick search.",
  },
  {
    href: "/entities/publications",
    title: "Publications",
    description: "Search records and open metadata detail.",
  },
  {
    href: "/entities/researchers",
    title: "Researchers",
    description: "Names, ORCID data and affiliations.",
  },
  {
    href: "/entities/organizations",
    title: "Organizations",
    description: "Units, hierarchy and linked people.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Overview"
        title="Research activity, mapped."
        description="A clean entry point for catalog browsing, workflow status and graph exploration."
      />

      <SystemOverview />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Panel
          title="Start here"
          description="Core demo paths."
        >
          <div className="grid gap-3">
            {entryPoints.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-[1.25rem] border border-[color:var(--border)] bg-white px-5 py-4 transition hover:border-zinc-300 hover:shadow-panel"
              >
                <p className="text-base font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-sm leading-6 text-zinc-500">{item.description}</p>
              </Link>
            ))}
          </div>
        </Panel>
        <Panel
          title="MVP scope"
          description="Kept intentionally focused."
        >
          <div className="grid gap-3">
            {[
              "Advanced graph analytics",
              "Full editing workflows",
              "Authentication and roles",
            ].map((item) => (
              <div
                key={item}
                className="rounded-[1rem] border border-[color:var(--border)] bg-white px-4 py-3 text-sm leading-6 text-zinc-600"
              >
                {item}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
