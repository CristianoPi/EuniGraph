"use client";

import Link from "next/link";
import type { Route } from "next";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import { StatCard } from "@/components/ui/stat-card";
import { GraphStatusPanels, SystemOverview } from "@/components/widgets/system-overview";
import { useDashboardCounts } from "@/hooks/use-dashboard";

const quickLinks: Array<{
  href: Route;
  title: string;
  description: string;
}> = [
  {
    href: "/entities/publications",
    title: "Publications",
    description: "Search title, DOI or year.",
  },
  {
    href: "/entities/researchers",
    title: "Researchers",
    description: "Inspect names and affiliations.",
  },
  {
    href: "/entities/organizations",
    title: "Organizations",
    description: "Navigate units and hierarchy.",
  },
];

const integerFormatter = new Intl.NumberFormat("en-US");

function formatCount(value: number): string {
  return integerFormatter.format(value);
}

export function DashboardOverview() {
  const counts = useDashboardCounts();

  return (
    <div className="space-y-6">
      <SystemOverview />

      {counts.isLoading ? (
        <LoadingState label="Building the dashboard overview from canonical entity APIs..." />
      ) : counts.isError ? (
        <ErrorState message="Entity counts could not be loaded for the dashboard." />
      ) : counts.data ? (
        <div className="grid gap-4 xl:grid-cols-3">
          <StatCard
            label="Publications"
            value={formatCount(counts.data.publications)}
            hint="Canonical publications."
          />
          <StatCard
            label="Researchers"
            value={formatCount(counts.data.researchers)}
            hint="Canonical researcher profiles."
          />
          <StatCard
            label="Organizations"
            value={formatCount(counts.data.organizations)}
            hint="Canonical organizations."
          />
        </div>
      ) : (
        <EmptyState
          title="No dashboard metrics available"
          message="The backend responded without enough data to compose the overview."
        />
      )}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Panel
          title="Catalog"
          description="Direct browsing paths."
        >
          <div className="grid gap-3">
            {quickLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-[1.15rem] border border-[color:var(--border)] bg-white p-4 transition hover:border-zinc-300 hover:shadow-panel"
              >
                <p className="text-base font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-sm leading-6 text-zinc-500">{item.description}</p>
              </Link>
            ))}
          </div>
        </Panel>

        <Panel
          title="Source model"
          description="Read-only frontend composition."
        >
          <ul className="space-y-2 text-sm leading-6 text-zinc-600">
            <li>Catalog data comes from canonical APIs.</li>
            <li>Workflow cards reuse status endpoints.</li>
            <li>Graph exploration stays on `/graphs`.</li>
          </ul>
        </Panel>
      </div>

      <GraphStatusPanels />
    </div>
  );
}
