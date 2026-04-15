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
    title: "Run workflows.",
    description: "Seed, normalization, embeddings and graph builds.",
    items: [
      "Seed load/reset/status",
      "Normalization run/status",
      "Embeddings build/reset",
      "Graph build/status",
    ],
  },
  {
    href: "/admin/data-entry" as Route,
    eyebrow: "Manual Data Entry",
    title: "Create data.",
    description: "Manual publications, researchers and organizations.",
    items: [
      "Publication metadata",
      "Researcher profiles",
      "Organization hierarchy",
      "Detail links after creation",
    ],
  },
];

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin Console"
        title="Operate the demo."
        description="Workflow controls and controlled manual data entry."
      />

      <div className="grid gap-5 xl:grid-cols-2">
        {adminCards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-[1.5rem] border border-[color:var(--border)] bg-white p-5 shadow-panel transition hover:border-zinc-300"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-600">
              {card.eyebrow}
            </p>
            <h2 className="mt-3 text-xl font-semibold tracking-tight text-ink">{card.title}</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-500">{card.description}</p>
            <ul className="mt-5 grid gap-2 text-sm leading-6 text-zinc-600">
              {card.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Link>
        ))}
      </div>

      <Panel
        title="Boundaries"
        description="Existing APIs only."
      >
        <p className="text-sm leading-6 text-zinc-600">
          Operations still run synchronously in the MVP. Feedback appears when the backend returns.
        </p>
      </Panel>
    </div>
  );
}
