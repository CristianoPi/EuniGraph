import Link from "next/link";
import type { Route } from "next";

import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";

const adminCards: Array<{
  href: Route;
  eyebrow: string;
  title: string;
  description: string;
  items: string[];
}> = [
  {
    href: "/admin/operations" as Route,
    eyebrow: "Operations",
    title: "Control backend workflows from the UI.",
    description:
      "Run seed, normalization, embeddings and materialized graph operations without switching to Swagger or curl.",
    items: [
      "OpenAIRE Beginner's Kit seed load/reset/status",
      "Normalization status and run trigger",
      "Embeddings build/load-all/reset/status",
      "Coauthorship and semantic graph build/status",
    ],
  },
  {
    href: "/admin/data-entry" as Route,
    eyebrow: "Manual Data Entry",
    title: "Create canonical demo data.",
    description:
      "Insert controlled publications, researchers and organizations through the manual entity management APIs.",
    items: [
      "Publication creation with bibliographic metadata",
      "Researcher creation with optional ORCID and primary organization",
      "Organization creation with location and hierarchy fields",
      "Direct links back to public detail views after creation",
    ],
  },
];

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin Console"
        title="Operate the prototype without leaving the frontend."
        description="The admin area is intentionally separated from browsing. Operations trigger backend workflows; manual data entry creates canonical domain entities."
      />

      <div className="grid gap-5 xl:grid-cols-2">
        {adminCards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-[2rem] border border-[color:var(--border)] bg-[color:var(--panel)] p-6 shadow-panel transition hover:border-pine/40"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-pine">
              {card.eyebrow}
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-ink">
              {card.title}
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">{card.description}</p>
            <ul className="mt-5 space-y-2 text-sm leading-6 text-slate-700">
              {card.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Link>
        ))}
      </div>

      <Panel
        title="MVP boundaries"
        description="This console consumes existing backend APIs. It does not add authentication, role management, realtime orchestration or advanced editing workflows."
      >
        <p className="text-sm leading-7 text-slate-700">
          Use this area for controlled prototype administration and demo preparation. Long-running
          backend workflows still execute synchronously in the current MVP, so completion feedback is
          shown after the backend response returns.
        </p>
      </Panel>
    </div>
  );
}
