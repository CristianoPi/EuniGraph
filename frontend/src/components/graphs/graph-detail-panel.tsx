"use client";

import Link from "next/link";
import type { Route } from "next";

import { EmptyState } from "@/components/states/empty-state";
import { DetailList } from "@/components/ui/detail-list";
import { Panel } from "@/components/ui/panel";
import type {
  CoauthorshipEdge,
  CoauthorshipGraphNodeMetrics,
  CoauthorshipNode,
  GraphLayer,
  SemanticEdge,
  SemanticGraphNodeMetrics,
  SemanticNode,
} from "@/lib/graphs/types";

function researcherRoute(id: string): Route {
  return `/entities/researchers/${id}` as Route;
}

function publicationRoute(id: string): Route {
  return `/entities/publications/${id}` as Route;
}

type GraphDetailPanelProps = {
  layer: GraphLayer;
  selectedNode:
    | { kind: "coauthorship"; node: CoauthorshipNode; metrics?: CoauthorshipGraphNodeMetrics | null }
    | { kind: "semantic"; node: SemanticNode; metrics?: SemanticGraphNodeMetrics | null }
    | null;
  selectedEdge:
    | { kind: "coauthorship"; edge: CoauthorshipEdge; sourceLabel: string; targetLabel: string }
    | { kind: "semantic"; edge: SemanticEdge; sourceLabel: string; targetLabel: string }
    | null;
  onFocusSelectedNode: () => void;
};

export function GraphDetailPanel({
  layer,
  selectedNode,
  selectedEdge,
  onFocusSelectedNode,
}: GraphDetailPanelProps) {
  if (selectedNode) {
    if (selectedNode.kind === "coauthorship") {
      const { node, metrics } = selectedNode;
      return (
        <Panel
          title={node.full_name}
          description="Coauthorship node."
        >
          <DetailList
            items={[
              { label: "Degree", value: node.degree },
              { label: "Strength", value: node.strength },
              { label: "Betweenness", value: node.betweenness.toFixed(4) },
              { label: "EUNICE university", value: node.university_name ?? "n/a" },
              { label: "Organization", value: node.primary_organization_name ?? "n/a" },
              { label: "Community", value: node.community_id ?? "n/a" },
              { label: "Component", value: node.component_id ?? "n/a" },
            ]}
          />
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={onFocusSelectedNode}
              className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Focus neighborhood
            </button>
            <Link
              href={researcherRoute(node.id)}
              className="rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm font-semibold text-zinc-700 hover:border-zinc-300"
            >
              Open researcher
            </Link>
          </div>
          {metrics ? (
            <div className="mt-5 rounded-[1rem] border border-[color:var(--border)] bg-white p-4 text-sm text-zinc-600">
              <p className="font-semibold text-ink">Neighbor snapshot</p>
              <p className="mt-2 leading-6">
                {metrics.neighbors.length} neighbors and {metrics.incident_edges.length} incident
                edges in the current build.
              </p>
            </div>
          ) : null}
        </Panel>
      );
    }

    const { node, metrics } = selectedNode;
    return (
      <Panel
        title={node.title}
        description="Semantic node."
      >
        <DetailList
          items={[
            { label: "Year", value: node.publication_year ?? "n/a" },
            { label: "DOI", value: node.doi ?? "n/a" },
            { label: "Degree", value: node.degree },
            { label: "Strength", value: node.strength.toFixed(3) },
            { label: "Community", value: node.community_id ?? "n/a" },
            { label: "Venue", value: node.venue_name ?? node.journal_name ?? "n/a" },
          ]}
        />
        <div className="mt-5 rounded-[1rem] border border-[color:var(--border)] bg-white p-4 text-sm text-zinc-600">
          <p className="font-semibold text-ink">Authors</p>
          <p className="mt-2 leading-6">
            {node.authors.length > 0 ? node.authors.join(", ") : "No author list available"}
          </p>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onFocusSelectedNode}
            className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-semibold text-white"
          >
            Focus neighborhood
          </button>
          <Link
            href={publicationRoute(node.id)}
            className="rounded-full border border-[color:var(--border)] bg-white px-4 py-2 text-sm font-semibold text-zinc-700 hover:border-zinc-300"
          >
            Open publication
          </Link>
        </div>
        {metrics ? (
          <div className="mt-5 rounded-[1rem] border border-[color:var(--border)] bg-white p-4 text-sm text-zinc-600">
            <p className="font-semibold text-ink">Neighbor snapshot</p>
            <p className="mt-2 leading-6">
              {metrics.neighbors.length} neighbors and {metrics.incident_edges.length} incident
              edges in the current build.
            </p>
          </div>
        ) : null}
      </Panel>
    );
  }

  if (selectedEdge) {
    if (selectedEdge.kind === "coauthorship") {
      const { edge, sourceLabel, targetLabel } = selectedEdge;
      return (
        <Panel
          title={`${sourceLabel} × ${targetLabel}`}
          description="Coauthorship edge."
        >
          <DetailList
            items={[
              { label: "Weight", value: edge.weight },
              { label: "Shared publications", value: edge.shared_publication_count },
              { label: "First year", value: edge.first_collaboration_year ?? "n/a" },
              { label: "Last year", value: edge.last_collaboration_year ?? "n/a" },
            ]}
          />
        </Panel>
      );
    }

    const { edge, sourceLabel, targetLabel } = selectedEdge;
    return (
      <Panel
        title={`${sourceLabel} ⇄ ${targetLabel}`}
        description="Semantic edge."
      >
        <DetailList
          items={[
            { label: "Similarity", value: edge.similarity_score.toFixed(3) },
            { label: "Weight", value: edge.weight.toFixed(3) },
            { label: "Rank", value: edge.rank },
            { label: "Mutual match", value: edge.mutual_match ? "yes" : "no" },
          ]}
        />
      </Panel>
    );
  }

  return (
    <EmptyState
      title={`No ${layer === "coauthorship" ? "researcher" : "publication"} selected`}
      message="Select a node or edge to inspect details."
    />
  );
}
