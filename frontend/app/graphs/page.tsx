import { PageHeader } from "@/components/ui/page-header";
import { UnifiedGraphExplorer } from "@/components/graphs/unified-graph-explorer";

export default function GraphsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Graphs"
        title="A shared explorer for coauthorship and semantic graph layers."
        description="Switch between collaboration and semantic layers, focus subgraphs and inspect node or edge detail from the same explorer."
      />

      <UnifiedGraphExplorer />
    </div>
  );
}
