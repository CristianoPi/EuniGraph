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
    description: "Metadata, DOI, year and detail views.",
  },
  {
    href: "/entities/researchers",
    title: "Researchers",
    description: "Names, ORCID and affiliation context.",
  },
  {
    href: "/entities/organizations",
    title: "Organizations",
    description: "Universities, departments and hierarchy.",
  },
];

export default function EntitiesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Entities"
        title="Canonical catalog."
        description="Browse publications, researchers and organizations through focused views."
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Panel
          title="Browse"
          description="Backend-aligned filters."
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
          title="Scope"
          description="Read-first catalog navigation."
        >
          <div className="grid gap-3">
            {[
              "List and detail views",
              "Backend query filters",
              "Route-linked drill-down",
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
