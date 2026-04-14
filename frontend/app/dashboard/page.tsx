import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { GraphStatusPanels, SystemOverview } from "@/components/widgets/system-overview";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dashboard"
        title="Operational snapshots for the main backend workflows."
        description="This page is still intentionally lightweight, but it already gives the frontend a concrete place to surface workflow status from embeddings and graph pipelines."
      />

      <SystemOverview />

      <GraphStatusPanels />

      <Panel
        title="Placeholder scope"
        description="The full dashboard is deferred, but this route is now the stable slot for future KPIs, seed progress, normalization findings and ingestion health."
      >
        <p className="text-sm leading-7 text-slate-700">
          Later issues can add richer cards, charts and workflow detail without changing the shell
          or the data-fetching conventions introduced here.
        </p>
      </Panel>
    </div>
  );
}
