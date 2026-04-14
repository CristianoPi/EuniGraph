import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { SystemOverview } from "@/components/widgets/system-overview";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Overview"
        title="A frontend shell that already knows how to talk to the platform."
        description="This first iteration is intentionally compact: shared navigation, backend proxying, cached server-state queries and clear placeholders for the next product slices."
      />

      <SystemOverview />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Panel
          title="What this foundation already solves"
          description="The frontend is structured to grow into dashboards, entity browsing and graph exploration without reshuffling the monorepo."
        >
          <ul className="space-y-3 text-sm leading-7 text-slate-700">
            <li>App Router layout with a stable shell and shared navigation.</li>
            <li>Centralized proxy layer toward FastAPI to avoid browser-side CORS friction.</li>
            <li>TanStack Query as the default server-state boundary.</li>
            <li>Reusable loading, error and empty-state patterns for future data views.</li>
          </ul>
        </Panel>
        <Panel
          title="Next slices already prepared"
          description="The route structure is in place so later issues can focus on domain views rather than on plumbing."
        >
          <div className="grid gap-3">
            {[
              "Dashboard for workflow status and operational metrics",
              "Entity browsing for publications, researchers and organizations",
              "Graph-oriented views for coauthorship and semantic layers",
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
