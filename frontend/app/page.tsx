import Link from "next/link";

import { Panel } from "@/components/ui/panel";
import { SystemOverview } from "@/components/widgets/system-overview";

const capabilities = [
  {
    title: "Browse the canonical catalog",
    description: "Publications, researchers and organizations stay aligned with the backend model.",
  },
  {
    title: "Read collaboration structure",
    description: "The coauthorship layer highlights who works together and how dense the links are.",
  },
  {
    title: "Compare semantic proximity",
    description: "The semantic layer connects publications by similarity rather than by shared authorship.",
  },
  {
    title: "Operate the prototype",
    description: "Admin workflows cover seed loading, normalization, embeddings and graph builds.",
  },
];

const applicationAreas = [
  {
    label: "Overview",
    description: "Product context, system snapshot and the key concepts behind the prototype.",
  },
  {
    label: "Dashboard",
    description: "Counts, workflow state and quick lookup across the catalog.",
  },
  {
    label: "Entities",
    description: "Read canonical records and follow relations across people, outputs and organizations.",
  },
  {
    label: "Graphs",
    description: "Switch between coauthorship and semantic graph exploration.",
  },
  {
    label: "Admin",
    description: "Run ingestion, graph operations and controlled manual data entry.",
  },
];

const systemLayers = [
  {
    title: "Canonical layer",
    description: "PostgreSQL keeps the normalized product, researcher and organization records used across the app.",
  },
  {
    title: "Operational layer",
    description: "Workflow status surfaces the state of seeds, embeddings and graph materializations.",
  },
  {
    title: "Graph layer",
    description: "Materialized coauthorship and semantic graphs turn the catalog into explorable network views.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-[color:var(--border)] bg-[radial-gradient(circle_at_top_left,rgba(245,158,11,0.07),transparent_26%),radial-gradient(circle_at_82%_18%,rgba(24,24,27,0.03),transparent_20%),linear-gradient(180deg,#ffffff,#fafafa)] px-6 py-7 shadow-panel sm:px-8 sm:py-8">
        <div className="pointer-events-none absolute inset-0 z-0 opacity-45">
          <div className="absolute left-[5%] top-[14%] h-24 w-24 rounded-full border border-zinc-200/70" />
          <div className="absolute left-[18%] top-[12%] h-3 w-3 rounded-full bg-zinc-900/55" />
          <div className="absolute left-[24%] top-[20%] h-px w-20 rotate-[14deg] bg-zinc-200" />
          <div className="absolute left-[8%] top-[32%] h-px w-28 -rotate-[20deg] bg-zinc-200/90" />
          <div className="absolute bottom-[12%] left-[9%] h-16 w-16 rounded-full border border-amber-200/70" />
          <div className="absolute bottom-[18%] left-[13%] h-2.5 w-2.5 rounded-full bg-amber-400/65" />
          <div className="absolute bottom-[24%] left-[17%] h-px w-14 rotate-[28deg] bg-zinc-200" />
        </div>
        <div className="pointer-events-none absolute inset-y-0 right-0 z-0 hidden w-[38%] opacity-40 lg:block">
          <div className="absolute left-[10%] top-[16%] h-2.5 w-2.5 rounded-full bg-amber-300/80" />
          <div className="absolute left-[36%] top-[28%] h-3 w-3 rounded-full bg-zinc-900/70" />
          <div className="absolute left-[22%] top-[52%] h-2 w-2 rounded-full bg-zinc-400/75" />
          <div className="absolute left-[58%] top-[48%] h-2.5 w-2.5 rounded-full bg-amber-400/80" />
          <div className="absolute left-[44%] top-[70%] h-2 w-2 rounded-full bg-zinc-500/75" />
          <div className="absolute left-[14%] top-[18%] h-px w-[28%] rotate-[18deg] bg-zinc-200" />
          <div className="absolute left-[25%] top-[34%] h-px w-[22%] rotate-[59deg] bg-zinc-200" />
          <div className="absolute left-[24%] top-[54%] h-px w-[34%] -rotate-[12deg] bg-zinc-200" />
          <div className="absolute left-[38%] top-[52%] h-px w-[16%] rotate-[44deg] bg-zinc-200" />
          <div className="absolute left-[52%] top-[50%] h-px w-[12%] -rotate-[72deg] bg-zinc-200" />
          <div className="absolute inset-x-[12%] inset-y-[14%] rounded-[1.75rem] border border-dashed border-zinc-200/70" />
        </div>

        <div className="relative z-10 grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)]">
          <div className="space-y-5">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-600">
                EuniGraph
              </p>
              <div className="space-y-3">
                <h1 className="max-w-3xl text-3xl font-semibold tracking-tight text-ink sm:text-5xl">
                  Research relations across the EUNICE network.
                </h1>
                <p className="max-w-2xl text-sm leading-7 text-zinc-600 sm:text-base">
                  EuniGraph is a demo product for reading research activity through canonical records,
                  operational workflows and graph-based views. It brings together catalog navigation,
                  pipeline status and network exploration in one coherent interface.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2.5">
              {["Canonical catalog", "Coauthorship graph", "Semantic graph", "Admin operations"].map((item) => (
                <span
                  key={item}
                  className="rounded-full border border-zinc-200 bg-white/90 px-3 py-1.5 text-xs font-semibold text-zinc-700 shadow-sm"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="grid gap-3 self-start">
            <div className="rounded-[1.4rem] border border-[color:var(--border)] bg-white/95 p-4 shadow-panel">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">Graph layers</p>
              <div className="mt-4 grid gap-3">
                <Link
                  href="/graphs?layer=coauthorship"
                  className="group rounded-[1rem] border border-zinc-200 bg-zinc-50 px-4 py-3 transition hover:border-zinc-300 hover:bg-white"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-ink">Coauthorship graph</p>
                    <span className="rounded-full border border-zinc-200 bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500 transition group-hover:border-zinc-300 group-hover:text-zinc-700">
                      Open
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-zinc-600">
                    Researchers as nodes, shared publications as edges.
                  </p>
                </Link>
                <Link
                  href="/graphs?layer=semantic"
                  className="group rounded-[1rem] border border-zinc-200 bg-zinc-50 px-4 py-3 transition hover:border-zinc-300 hover:bg-white"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-ink">Semantic graph</p>
                    <span className="rounded-full border border-zinc-200 bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500 transition group-hover:border-zinc-300 group-hover:text-zinc-700">
                      Open
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-zinc-600">
                    Publications as nodes, semantic similarity as edges.
                  </p>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <SystemOverview />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <Panel
          title="What the product does"
          description="A compact reading model for the prototype."
        >
          <div className="grid gap-3">
            {capabilities.map((item, index) => (
              <div
                key={item.title}
                className="flex gap-4 rounded-[1.2rem] border border-[color:var(--border)] bg-white px-4 py-4"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
                  0{index + 1}
                </div>
                <div>
                  <p className="text-sm font-semibold text-ink">{item.title}</p>
                  <p className="mt-1 text-sm leading-6 text-zinc-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title="Inside the app"
          description="Use the sidebar to move between these areas."
        >
          <div className="grid gap-3">
            {applicationAreas.map((item) => (
              <div
                key={item.label}
                className="rounded-[1.2rem] border border-[color:var(--border)] bg-white px-4 py-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-ink">{item.label}</p>
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                </div>
                <p className="mt-1 text-sm leading-6 text-zinc-600">{item.description}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <Panel
          title="How to read the graphs"
          description="Two complementary ways to understand the same research space."
        >
          <div className="grid gap-3">
            <div className="rounded-[1.2rem] border border-[color:var(--border)] bg-white px-4 py-4">
              <p className="text-sm font-semibold text-ink">Coauthorship is about collaboration</p>
              <p className="mt-1 text-sm leading-6 text-zinc-600">
                It shows who has published together, so the emphasis is on teams, density and shared work.
              </p>
            </div>
            <div className="rounded-[1.2rem] border border-[color:var(--border)] bg-white px-4 py-4">
              <p className="text-sm font-semibold text-ink">Semantic is about thematic proximity</p>
              <p className="mt-1 text-sm leading-6 text-zinc-600">
                It links publications that talk about similar topics, even when the author groups are different.
              </p>
            </div>
          </div>
        </Panel>

        <Panel
          title="System layers"
          description="From source data to graph exploration."
        >
          <div className="grid gap-3 sm:grid-cols-3">
            {systemLayers.map((item) => (
              <div
                key={item.title}
                className="rounded-[1.2rem] border border-[color:var(--border)] bg-white px-4 py-4"
              >
                <div className="mb-3 flex items-center gap-2">
                  <span className="inline-flex h-2.5 w-2.5 rounded-full bg-zinc-900" />
                  <p className="text-sm font-semibold text-ink">{item.title}</p>
                </div>
                <p className="text-sm leading-6 text-zinc-600">{item.description}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
