import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { GraphStatusPanels } from "@/components/widgets/system-overview";

export default function GraphsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Graphs"
        title="A route boundary already aligned with the graph-capable backend."
        description="The backend already exposes materialized coauthorship and semantic graph APIs. This page keeps the frontend ready for later visual exploration without building the explorer too early."
      />

      <GraphStatusPanels />

      <Panel
        title="Future graph views"
        description="The route is intentionally broad enough to host overview cards, graph selectors, static previews and later interactive exploration."
      >
        <ul className="space-y-3 text-sm leading-7 text-slate-700">
          <li>Coauthorship graph explorer entry point</li>
          <li>Semantic similarity graph explorer entry point</li>
          <li>Shared filtering controls and graph detail panels</li>
        </ul>
      </Panel>
    </div>
  );
}
