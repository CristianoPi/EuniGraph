import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import Link from "next/link";
import type { Route } from "next";

const entryPoints: Array<{
  href: Route;
  title: string;
  description: string;
}> = [
  {
    href: "/entities/publications",
    title: "Publications",
    description: "Browse canonical publication metadata, filter by year or DOI and open detail views.",
  },
  {
    href: "/entities/researchers",
    title: "Researchers",
    description: "Search by name or ORCID and inspect affiliation context from canonical relations.",
  },
  {
    href: "/entities/organizations",
    title: "Organizations",
    description: "Navigate universities, departments and hierarchy-driven canonical entities.",
  },
];

export default function EntitiesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Entities"
        title="The canonical catalog now has dedicated browsing routes."
        description="This section is the non-graph entry point into EuniGraph: publications, researchers and organizations can now be searched, filtered and opened in detail views."
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Panel
          title="Catalog entry points"
          description="Each entity family now has a dedicated browser route with filters aligned to the backend APIs."
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
          title="Current scope"
          description="This iteration focuses on consultation and drill-down, not on editing or graph exploration."
        >
          <div className="grid gap-3">
            {[
              "List and detail views for the three canonical entity families",
              "Filters that correspond directly to existing FastAPI query parameters",
              "Route-linked drill-down between entities without duplicating backend rules",
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
