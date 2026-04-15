"use client";

import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Panel } from "@/components/ui/panel";
import {
  useBackendHealth,
  useCoauthorshipStatus,
  useEmbeddingsStatus,
  useSemanticGraphStatus,
} from "@/hooks/use-overview";

function StatusValue({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "good";
}) {
  return (
    <div className="rounded-[1.15rem] border border-[color:var(--border)] bg-white p-4 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">{label}</p>
      <p
        className={
          tone === "good"
            ? "mt-2 text-lg font-semibold text-ink"
            : "mt-2 text-lg font-semibold text-ink"
        }
      >
        {value}
      </p>
    </div>
  );
}

export function SystemOverview() {
  const health = useBackendHealth();
  const embeddings = useEmbeddingsStatus();
  const coauthorship = useCoauthorshipStatus();
  const semantic = useSemanticGraphStatus();

  if (health.isLoading || embeddings.isLoading || coauthorship.isLoading || semantic.isLoading) {
    return <LoadingState label="Checking backend services and workflow snapshots..." />;
  }

  if (health.isError || embeddings.isError || coauthorship.isError || semantic.isError) {
    return (
      <ErrorState
        message="At least one backend integration request failed. Check the running services."
      />
    );
  }

  const healthData = health.data;
  const embeddingsData = embeddings.data;
  const coauthorshipData = coauthorship.data;
  const semanticData = semantic.data;

  if (!healthData || !embeddingsData || !coauthorshipData || !semanticData) {
    return <ErrorState message="Backend responses were empty or incomplete." />;
  }

  return (
    <div className="grid gap-4 xl:grid-cols-4">
      <StatusValue
        label="Backend"
        value={`${healthData.status} · ${healthData.service}`}
        tone="good"
      />
      <StatusValue
        label="Embeddings"
        value={
          embeddingsData.qdrant_collection_exists
            ? `${embeddingsData.provider} · ${embeddingsData.qdrant_points_count} points`
            : "Collection not built yet"
        }
      />
      <StatusValue
        label="Coauthorship"
        value={
          coauthorshipData.status === "completed"
            ? `${coauthorshipData.node_count ?? 0} nodes`
            : "Build pending"
        }
      />
      <StatusValue
        label="Semantic Graph"
        value={
          semanticData.status === "completed"
            ? `${semanticData.edge_count ?? 0} edges`
            : "Build pending"
        }
      />
    </div>
  );
}

export function GraphStatusPanels() {
  const coauthorship = useCoauthorshipStatus();
  const semantic = useSemanticGraphStatus();

  if (coauthorship.isLoading || semantic.isLoading) {
    return <LoadingState label="Loading graph build status..." />;
  }

  if (coauthorship.isError || semantic.isError) {
    return <ErrorState message="Graph build status could not be loaded from the backend." />;
  }

  const coauthorshipData = coauthorship.data;
  const semanticData = semantic.data;

  if (!coauthorshipData || !semanticData) {
    return <ErrorState message="Graph build responses were empty or incomplete." />;
  }

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <Panel
        title="Coauthorship"
        description="Researcher graph."
      >
        <dl className="grid gap-4 sm:grid-cols-2">
          <StatusValue label="Status" value={coauthorshipData.status} />
          <StatusValue label="Nodes" value={String(coauthorshipData.node_count ?? 0)} />
          <StatusValue label="Edges" value={String(coauthorshipData.edge_count ?? 0)} />
          <StatusValue
            label="Completed"
            value={coauthorshipData.completed_at ?? "Not available"}
          />
        </dl>
      </Panel>
      <Panel
        title="Semantic"
        description="Publication similarity graph."
      >
        <dl className="grid gap-4 sm:grid-cols-2">
          <StatusValue label="Status" value={semanticData.status} />
          <StatusValue label="Nodes" value={String(semanticData.node_count ?? 0)} />
          <StatusValue label="Edges" value={String(semanticData.edge_count ?? 0)} />
          <StatusValue label="Completed" value={semanticData.completed_at ?? "Not available"} />
        </dl>
      </Panel>
    </div>
  );
}
