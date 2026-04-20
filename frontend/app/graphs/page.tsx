import { PageHeader } from "@/components/ui/page-header";
import { UnifiedGraphExplorer } from "@/components/graphs/unified-graph-explorer";
import type { GraphLayer } from "@/lib/graphs/types";

type GraphsPageProps = {
  searchParams?: Promise<{ layer?: string }>;
};

function normalizeLayer(value: string | undefined): GraphLayer {
  return value === "semantic" ? "semantic" : "coauthorship";
}

export default async function GraphsPage({ searchParams }: GraphsPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const initialLayer = normalizeLayer(params?.layer);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Graphs"
        title="Two graph layers."
        description="Switch layer, filter subgraphs and inspect nodes or edges."
      />

      <UnifiedGraphExplorer initialLayer={initialLayer} />
    </div>
  );
}
