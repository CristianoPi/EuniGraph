"use client";

import type { Core, ElementDefinition, EventObject, NodeSingular, EdgeSingular } from "cytoscape";
import { useEffect, useMemo, useRef, useState } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { GraphCanvas } from "@/components/graphs/graph-canvas";
import { GraphControls } from "@/components/graphs/graph-controls";
import { GraphDetailPanel } from "@/components/graphs/graph-detail-panel";
import { Panel } from "@/components/ui/panel";
import {
  useCoauthorshipGraph,
  useCoauthorshipGraphStatus,
  useCoauthorshipMetrics,
  useCoauthorshipNodeMetrics,
  useSemanticGraph,
  useSemanticGraphStatus,
  useSemanticMetrics,
  useSemanticNodeMetrics,
} from "@/hooks/use-graphs";
import { ApiError } from "@/lib/api/client";
import {
  COAUTHORSHIP_FALLBACK_COLOR,
  getCoauthorshipOrganizationColor,
  getCoauthorshipUniversityColor,
  mapCoauthorshipElements,
  mapSemanticElements,
} from "@/lib/graphs/mappers";
import type {
  CoauthorshipEdge,
  CoauthorshipNode,
  CoauthorshipSubgraphFilters,
  GraphLayer,
  SemanticEdge,
  SemanticNode,
  SemanticSubgraphFilters,
} from "@/lib/graphs/types";

type CoauthorshipControlState = {
  researcherId: string;
  organizationId: string;
  communityId: string;
  maxNodes: string;
  minEdgeWeight: string;
};

type SemanticControlState = {
  publicationId: string;
  organizationId: string;
  publicationYear: string;
  communityId: string;
  maxNodes: string;
  minEdgeWeight: string;
};

function toOptionalNumber(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function normalizeCoauthorshipFilters(
  state: CoauthorshipControlState,
): CoauthorshipSubgraphFilters {
  return {
    researcher_id: state.researcherId.trim() || undefined,
    organization_id: state.organizationId.trim() || undefined,
    community_id: toOptionalNumber(state.communityId),
    max_nodes: toOptionalNumber(state.maxNodes),
    min_edge_weight: toOptionalNumber(state.minEdgeWeight),
  };
}

function normalizeSemanticFilters(state: SemanticControlState): SemanticSubgraphFilters {
  return {
    publication_id: state.publicationId.trim() || undefined,
    organization_id: state.organizationId.trim() || undefined,
    publication_year: toOptionalNumber(state.publicationYear),
    community_id: toOptionalNumber(state.communityId),
    max_nodes: toOptionalNumber(state.maxNodes),
    min_edge_weight: toOptionalNumber(state.minEdgeWeight),
  };
}

function hasAnyValue(values: Record<string, string>): boolean {
  return Object.values(values).some((value) => value.trim().length > 0);
}

type CoauthorshipOrganizationLegendItem = {
  key: string | null;
  label: string;
  color: string;
  count: number;
  kind: "university" | "organization" | "fallback";
};

const DEFAULT_GRAPH_NODE_LIMIT = 250;

function defaultNodeLimitValue(): string {
  return String(DEFAULT_GRAPH_NODE_LIMIT);
}

function formatGraphError(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string" && error.detail.trim()) {
      return error.detail;
    }
    if (Array.isArray(error.detail)) {
      const firstDetail = error.detail[0];
      if (firstDetail && typeof firstDetail === "object" && "msg" in firstDetail) {
        return String(firstDetail.msg);
      }
    }
    return `Backend request failed with status ${error.status}.`;
  }
  return "The graph explorer could not load the requested graph layer from the backend.";
}

type UnifiedGraphExplorerProps = {
  initialLayer?: GraphLayer;
};

export function UnifiedGraphExplorer({
  initialLayer = "coauthorship",
}: UnifiedGraphExplorerProps) {
  const [layer, setLayer] = useState<GraphLayer>(initialLayer);

  const [coauthorshipDraft, setCoauthorshipDraft] = useState<CoauthorshipControlState>({
    researcherId: "",
    organizationId: "",
    communityId: "",
    maxNodes: defaultNodeLimitValue(),
    minEdgeWeight: "",
  });
  const [semanticDraft, setSemanticDraft] = useState<SemanticControlState>({
    publicationId: "",
    organizationId: "",
    publicationYear: "",
    communityId: "",
    maxNodes: defaultNodeLimitValue(),
    minEdgeWeight: "",
  });

  const [coauthorshipFilters, setCoauthorshipFilters] = useState<CoauthorshipSubgraphFilters>({
    max_nodes: DEFAULT_GRAPH_NODE_LIMIT,
  });
  const [semanticFilters, setSemanticFilters] = useState<SemanticSubgraphFilters>({
    max_nodes: DEFAULT_GRAPH_NODE_LIMIT,
  });

  const coauthorshipStatus = useCoauthorshipGraphStatus(layer === "coauthorship");
  const semanticStatus = useSemanticGraphStatus(layer === "semantic");
  const coauthorshipGraph = useCoauthorshipGraph(coauthorshipFilters, layer === "coauthorship");
  const semanticGraph = useSemanticGraph(semanticFilters, layer === "semantic");
  const coauthorshipMetrics = useCoauthorshipMetrics(layer === "coauthorship");
  const semanticMetrics = useSemanticMetrics(layer === "semantic");

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  const coauthorshipNodeMetrics = useCoauthorshipNodeMetrics(
    layer === "coauthorship" ? selectedNodeId : null,
    layer === "coauthorship",
  );
  const semanticNodeMetrics = useSemanticNodeMetrics(
    layer === "semantic" ? selectedNodeId : null,
    layer === "semantic",
  );

  const canvasRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  const activeStatus = layer === "coauthorship" ? coauthorshipStatus : semanticStatus;
  const activeGraph = layer === "coauthorship" ? coauthorshipGraph : semanticGraph;
  const activeMetrics = layer === "coauthorship" ? coauthorshipMetrics : semanticMetrics;

  const elements = useMemo<ElementDefinition[]>(() => {
    if (!activeGraph.data) {
      return [];
    }

    return layer === "coauthorship"
      ? mapCoauthorshipElements(activeGraph.data.nodes as CoauthorshipNode[], activeGraph.data.edges as CoauthorshipEdge[])
      : mapSemanticElements(activeGraph.data.nodes as SemanticNode[], activeGraph.data.edges as SemanticEdge[]);
  }, [activeGraph.data, layer]);

  const nodeMap = useMemo(() => {
    if (!activeGraph.data) {
      return new Map<string, CoauthorshipNode | SemanticNode>();
    }
    return new Map(activeGraph.data.nodes.map((node) => [node.id, node]));
  }, [activeGraph.data]);

  const edgeMap = useMemo(() => {
    if (!activeGraph.data) {
      return new Map<string, CoauthorshipEdge | SemanticEdge>();
    }
    return new Map(
      activeGraph.data.edges.map((edge) => [`${edge.source}__${edge.target}`, edge]),
    );
  }, [activeGraph.data]);

  const selectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) ?? null : null;
  const selectedEdge = selectedEdgeId ? edgeMap.get(selectedEdgeId) ?? null : null;
  const coauthorshipOrganizationLegend = useMemo<CoauthorshipOrganizationLegendItem[]>(() => {
    if (layer !== "coauthorship" || !coauthorshipGraph.data) {
      return [];
    }

    const counts = new Map<string, CoauthorshipOrganizationLegendItem>();
    for (const node of coauthorshipGraph.data.nodes) {
      const universityCode = node.university_code ?? null;
      const organizationKey = node.primary_organization_id ?? null;
      const mapKey = organizationKey
        ? `organization:${organizationKey}`
        : universityCode
          ? `university:${universityCode}`
          : "__unassigned__";
      const current = counts.get(mapKey);
      if (current) {
        current.count += 1;
        continue;
      }

      counts.set(mapKey, {
        key: organizationKey ?? universityCode,
        label:
          node.primary_organization_name ?? node.university_name ?? "Not attributed",
        color: organizationKey
          ? universityCode
            ? getCoauthorshipUniversityColor(universityCode)
            : getCoauthorshipOrganizationColor(organizationKey)
          : universityCode
            ? getCoauthorshipUniversityColor(universityCode)
            : COAUTHORSHIP_FALLBACK_COLOR,
        count: 1,
        kind: organizationKey
          ? "organization"
          : universityCode
            ? "university"
            : "fallback",
      });
    }

    return [...counts.values()].sort(
      (left, right) => right.count - left.count || left.label.localeCompare(right.label),
    );
  }, [coauthorshipGraph.data, layer]);
  const hasUnassignedCoauthorshipNodes = useMemo(() => {
    if (layer !== "coauthorship" || !coauthorshipGraph.data) {
      return false;
    }
    return coauthorshipGraph.data.nodes.some(
      (node) => !node.university_code && !node.primary_organization_id,
    );
  }, [coauthorshipGraph.data, layer]);

  useEffect(() => {
    let active = true;

    async function mountGraph() {
      if (!canvasRef.current) {
        return;
      }

      const cytoscape = (await import("cytoscape")).default;
      if (!active || !canvasRef.current) {
        return;
      }

      cyRef.current?.destroy();
      cyRef.current = cytoscape({
        container: canvasRef.current,
        elements,
        layout: {
          name: "cose",
          animate: false,
          fit: true,
          padding: 36,
          nodeRepulsion: 8000,
          idealEdgeLength: layer === "coauthorship" ? 80 : 110,
        },
        style: [
          {
            selector: "node",
            style: {
              width: "data(size)",
              height: "data(size)",
              label: "",
              "background-color": "data(nodeColor)",
              "border-color": "#ffffff",
              "border-width": 2,
              opacity: 0.9,
            },
          },
          {
            selector: "node:selected",
            style: {
              label: "data(label)",
              "text-wrap": "wrap",
              "text-max-width": "160px",
              "font-size": "12px",
              color: "#18181b",
              "text-background-color": "#ffffff",
              "text-background-opacity": 0.95,
              "text-background-padding": "6px",
              "text-background-shape": "roundrectangle",
              "text-margin-y": -22,
              "border-color": "#18181b",
              "border-width": 3,
            },
          },
          {
            selector: "edge",
            style: {
              width: "data(lineWidth)",
              "line-color":
                layer === "coauthorship"
                  ? "rgba(24, 24, 27, 0.22)"
                  : "rgba(245, 158, 11, 0.35)",
              "curve-style": "bezier",
              opacity: 0.72,
            },
          },
          {
            selector: "edge:selected",
            style: {
              width: "mapData(lineWidth, 1, 8, 3, 10)",
              "line-color": "#18181b",
              opacity: 1,
            },
          },
        ],
        wheelSensitivity: 0.18,
      });

      cyRef.current.on("tap", "node", (event: EventObject) => {
        const target = event.target as NodeSingular;
        setSelectedNodeId(target.id());
        setSelectedEdgeId(null);
      });

      cyRef.current.on("tap", "edge", (event: EventObject) => {
        const target = event.target as EdgeSingular;
        setSelectedEdgeId(target.id());
        setSelectedNodeId(null);
      });

      cyRef.current.on("tap", (event: EventObject) => {
        if (event.target === cyRef.current) {
          setSelectedNodeId(null);
          setSelectedEdgeId(null);
        }
      });
    }

    mountGraph();

    return () => {
      active = false;
      cyRef.current?.destroy();
      cyRef.current = null;
    };
  }, [elements, layer]);

  function handleLayerChange(nextLayer: GraphLayer) {
    setLayer(nextLayer);
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
  }

  function applyFilters() {
    if (layer === "coauthorship") {
      setCoauthorshipFilters(normalizeCoauthorshipFilters(coauthorshipDraft));
      return;
    }
    setSemanticFilters(normalizeSemanticFilters(semanticDraft));
  }

  function resetFilters() {
    if (layer === "coauthorship") {
      const nextDraft = {
        researcherId: "",
        organizationId: "",
        communityId: "",
        maxNodes: defaultNodeLimitValue(),
        minEdgeWeight: "",
      };
      setCoauthorshipDraft(nextDraft);
      setCoauthorshipFilters(normalizeCoauthorshipFilters(nextDraft));
    } else {
      const nextDraft = {
        publicationId: "",
        organizationId: "",
        publicationYear: "",
        communityId: "",
        maxNodes: defaultNodeLimitValue(),
        minEdgeWeight: "",
      };
      setSemanticDraft(nextDraft);
      setSemanticFilters(normalizeSemanticFilters(nextDraft));
    }
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
  }

  function resetView() {
    cyRef.current?.fit(undefined, 40);
  }

  function centerSelection() {
    if (!selectedNodeId || !cyRef.current) {
      return;
    }
    const node = cyRef.current.getElementById(selectedNodeId);
    if (node.nonempty()) {
      cyRef.current.animate({
        fit: {
          eles: node,
          padding: 120,
        },
        duration: 260,
      });
    }
  }

  function focusSelectedNode() {
    if (!selectedNodeId) {
      return;
    }

    if (layer === "coauthorship") {
      const nextDraft = {
        ...coauthorshipDraft,
        researcherId: selectedNodeId,
      };
      setCoauthorshipDraft(nextDraft);
      setCoauthorshipFilters(normalizeCoauthorshipFilters(nextDraft));
      return;
    }

    const nextDraft = {
      ...semanticDraft,
      publicationId: selectedNodeId,
    };
    setSemanticDraft(nextDraft);
    setSemanticFilters(normalizeSemanticFilters(nextDraft));
  }

  const activeHasFilters =
    layer === "coauthorship"
      ? hasAnyValue(coauthorshipDraft)
      : hasAnyValue(semanticDraft);

  const selectedNodePayload =
    layer === "coauthorship" && selectedNode && "full_name" in selectedNode
      ? {
          kind: "coauthorship" as const,
          node: selectedNode,
          metrics: coauthorshipNodeMetrics.data ?? null,
        }
      : layer === "semantic" && selectedNode && "title" in selectedNode
        ? {
            kind: "semantic" as const,
            node: selectedNode,
            metrics: semanticNodeMetrics.data ?? null,
          }
        : null;

  const selectedEdgePayload =
    layer === "coauthorship" && selectedEdge && "shared_publication_count" in selectedEdge
      ? {
          kind: "coauthorship" as const,
          edge: selectedEdge,
          sourceLabel:
            ("full_name" in (nodeMap.get(selectedEdge.source) ?? {}) &&
              (nodeMap.get(selectedEdge.source) as CoauthorshipNode).full_name) ||
            selectedEdge.source,
          targetLabel:
            ("full_name" in (nodeMap.get(selectedEdge.target) ?? {}) &&
              (nodeMap.get(selectedEdge.target) as CoauthorshipNode).full_name) ||
            selectedEdge.target,
        }
      : layer === "semantic" && selectedEdge && "similarity_score" in selectedEdge
        ? {
            kind: "semantic" as const,
            edge: selectedEdge,
            sourceLabel:
              ("title" in (nodeMap.get(selectedEdge.source) ?? {}) &&
                (nodeMap.get(selectedEdge.source) as SemanticNode).title) ||
              selectedEdge.source,
            targetLabel:
              ("title" in (nodeMap.get(selectedEdge.target) ?? {}) &&
                (nodeMap.get(selectedEdge.target) as SemanticNode).title) ||
              selectedEdge.target,
          }
        : null;

  return (
    <div className="space-y-6">
      <Panel
        title="Graph controls"
        description="Choose a layer, filter, then inspect nodes or edges."
      >
        <GraphControls
          layer={layer}
          onLayerChange={handleLayerChange}
          coauthorship={coauthorshipDraft}
          semantic={semanticDraft}
          onCoauthorshipChange={(key, value) =>
            setCoauthorshipDraft((current) => ({ ...current, [key]: value }))
          }
          onSemanticChange={(key, value) =>
            setSemanticDraft((current) => ({ ...current, [key]: value }))
          }
          onApply={applyFilters}
          onResetFilters={resetFilters}
          onResetView={resetView}
          onCenterSelection={centerSelection}
          canCenterSelection={Boolean(selectedNodeId)}
        />
        {layer === "coauthorship" && coauthorshipOrganizationLegend.length > 0 ? (
          <div className="mt-5 space-y-3 border-t border-zinc-100 pt-4">
            <div className="flex items-center justify-between gap-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                Node colors
              </p>
              <p className="text-xs text-zinc-400">Institutional when mapped, organization otherwise</p>
            </div>
            <div className="grid max-h-56 gap-2 overflow-y-auto pr-1 sm:grid-cols-2 xl:grid-cols-3">
              {coauthorshipOrganizationLegend.map((item) => (
                <div
                  key={item.key ?? "__unassigned__"}
                  className="inline-flex items-center gap-2 rounded-full border border-[color:var(--border)] bg-white px-3 py-1.5 text-xs text-zinc-600"
                >
                  <span
                    className="inline-flex h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="max-w-[220px] truncate">{item.label}</span>
                  <span className="text-zinc-400">
                    {item.kind === "university"
                      ? "EUNICE"
                      : item.kind === "organization"
                        ? "Org"
                        : "n/a"}
                  </span>
                  <span className="text-zinc-400">{item.count}</span>
                </div>
              ))}
              {hasUnassignedCoauthorshipNodes &&
              !coauthorshipOrganizationLegend.some((item) => item.key === null) ? (
                <div className="inline-flex items-center gap-2 rounded-full border border-[color:var(--border)] bg-white px-3 py-1.5 text-xs text-zinc-600">
                  <span
                    className="inline-flex h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: COAUTHORSHIP_FALLBACK_COLOR }}
                  />
                  <span>Not attributed</span>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
      </Panel>

      {activeStatus.isLoading || activeGraph.isLoading ? (
        <LoadingState label="Loading the materialized graph and its current build status..." />
      ) : activeStatus.isError || activeGraph.isError ? (
        <ErrorState
          message={formatGraphError(activeGraph.error ?? activeStatus.error)}
        />
      ) : activeStatus.data?.status !== "completed" ? (
        <EmptyState
          title="Graph build not available"
          message={`The active ${layer} graph is not completed yet. Build it from admin operations.`}
        />
      ) : !activeGraph.data || activeGraph.data.nodes.length === 0 ? (
        <EmptyState
          title="No graph data available"
          message={
            activeHasFilters
              ? "The selected filters returned an empty graph payload."
              : "The graph payload is empty for the current build."
          }
        />
      ) : (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.7fr)]">
          <div className="space-y-5">
            <Panel
              title={layer === "coauthorship" ? "Coauthorship layer" : "Semantic layer"}
              description={`Build ${activeStatus.data?.build_id ?? "n/a"} · ${activeGraph.data.nodes.length} nodes · ${activeGraph.data.edges.length} edges`}
            >
              <GraphCanvas
                ref={canvasRef}
                hint="Drag, zoom, select."
              />
            </Panel>

            <div className="grid gap-4 xl:grid-cols-3">
              <Panel
                title="Build"
                description="Current metadata."
              >
                <dl className="space-y-2 text-sm leading-7 text-zinc-600">
                  <div>
                    <dt className="font-semibold text-ink">Status</dt>
                    <dd>{activeStatus.data?.status}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-ink">Completed</dt>
                    <dd>{activeStatus.data?.completed_at ?? "n/a"}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-ink">Communities</dt>
                    <dd>{activeStatus.data?.community_count ?? "n/a"}</dd>
                  </div>
                </dl>
              </Panel>
              <Panel
                title="Metrics"
                description="Latest active build."
              >
                {activeMetrics.data ? (
                  <dl className="space-y-2 text-sm leading-7 text-zinc-600">
                    <div>
                      <dt className="font-semibold text-ink">Nodes</dt>
                      <dd>{activeMetrics.data.node_count}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-ink">Edges</dt>
                      <dd>{activeMetrics.data.edge_count}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-ink">Components</dt>
                      <dd>{activeMetrics.data.component_count}</dd>
                    </div>
                  </dl>
                ) : (
                  <EmptyState
                    title="Metrics unavailable"
                    message="Graph metrics could not be loaded for this layer."
                  />
                )}
              </Panel>
              <Panel
                title="Mode"
                description="Full graph or subgraph."
              >
                <p className="text-sm leading-7 text-zinc-600">
                  {activeHasFilters
                    ? "Filtered subgraph from the persisted payload."
                    : "Full active graph payload."}
                </p>
              </Panel>
            </div>
          </div>

          <div className="space-y-5">
            <GraphDetailPanel
              layer={layer}
              selectedNode={selectedNodePayload}
              selectedEdge={selectedEdgePayload}
              onFocusSelectedNode={focusSelectedNode}
            />
          </div>
        </div>
      )}
    </div>
  );
}
