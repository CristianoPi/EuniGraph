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
    title: "Open dashboard",
    description: "Get a synthetic view of catalog size, workflow presence and quick search.",
  },
  {
    href: "/entities/publications",
    title: "Browse publications",
    description: "Search canonical publications and navigate to detailed metadata views.",
  },
  {
    href: "/entities/researchers",
    title: "Browse researchers",
    description: "Inspect researchers, ORCID data and affiliation context.",
  },
  {
    href: "/entities/organizations",
    title: "Browse organizations",
    description: "Navigate organizations, hierarchy and linked researcher context.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Overview"
        title="A frontend shell that now opens into real dashboard and catalog browsing flows."
        description="Use the overview as the entry point into dashboard, catalog browsing and graph exploration."
      />

      <SystemOverview />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Panel
          title="Where to go next"
          description="The most useful frontend entry points are now available directly from the shell."
        >
          <div className="grid gap-3">
            {entryPoints.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-[1.5rem] border border-[color:var(--border)] bg-white/70 px-5 py-5 transition hover:border-pine/40 hover:bg-white"
              >
                <p className="text-lg font-semibold text-ink">{item.title}</p>
                <p className="mt-2 text-sm leading-7 text-slate-600">{item.description}</p>
              </Link>
            ))}
          </div>
        </Panel>
        <Panel
          title="What remains intentionally out of scope"
          description="Some areas stay intentionally lightweight so the core exploration flows remain readable."
        >
          <div className="grid gap-3">
            {[
              "Graph explorer interactions and visual analytics",
              "Advanced editing and curation workflows",
              "Authentication and user-specific personalization",
            ].map((item) => (
              <div
                key={item}
                className="rounded-[1.25rem] border border-[color:var(--border)] bg-white/70 px-4 py-4 text-sm leading-6 text-slate-700"
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
