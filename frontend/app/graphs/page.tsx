import { PageHeader } from "@/components/ui/page-header";
import { UnifiedGraphExplorer } from "@/components/graphs/unified-graph-explorer";

export default function GraphsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Graphs"
        title="Two graph layers."
        description="Switch layer, filter subgraphs and inspect nodes or edges."
      />

      <UnifiedGraphExplorer />
    </div>
  );
}
