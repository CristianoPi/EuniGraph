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
    title: "Browse publications",
    description: "Search by title, DOI, year and drill down into canonical metadata.",
  },
  {
    href: "/entities/researchers",
    title: "Browse researchers",
    description: "Inspect canonical researchers, ORCID data and affiliation context.",
  },
  {
    href: "/entities/organizations",
    title: "Browse organizations",
    description: "Navigate universities, departments and linked canonical entities.",
  },
];

function formatCappedCount(value: number, limit: number): string {
  return value >= limit ? `${limit}+` : String(value);
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
            value={formatCappedCount(counts.data.publications, counts.data.limit)}
            hint={`Count composed from the publication list endpoint, capped at ${counts.data.limit}.`}
          />
          <StatCard
            label="Researchers"
            value={formatCappedCount(counts.data.researchers, counts.data.limit)}
            hint={`Count composed from the researcher list endpoint, capped at ${counts.data.limit}.`}
          />
          <StatCard
            label="Organizations"
            value={formatCappedCount(counts.data.organizations, counts.data.limit)}
            hint={`Count composed from the organization list endpoint, capped at ${counts.data.limit}.`}
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
          title="Catalog entry points"
          description="The frontend now makes the canonical catalog navigable without forcing the user into graph views first."
        >
          <div className="grid gap-3">
            {quickLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-[1.5rem] border border-[color:var(--border)] bg-white/70 p-4 transition hover:border-pine/40 hover:bg-white"
              >
                <p className="text-base font-semibold text-ink">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
              </Link>
            ))}
          </div>
        </Panel>

        <Panel
          title="Prototype orientation"
          description="The dashboard deliberately combines stable backend layers rather than inventing client-side domain rules."
        >
          <ul className="space-y-3 text-sm leading-7 text-slate-700">
            <li>Canonical entities come from PostgreSQL-backed APIs.</li>
            <li>Workflow panels reuse existing embeddings and graph status endpoints.</li>
            <li>Graph exploration remains a separate concern for later issues.</li>
          </ul>
        </Panel>
      </div>

      <GraphStatusPanels />
    </div>
  );
}
