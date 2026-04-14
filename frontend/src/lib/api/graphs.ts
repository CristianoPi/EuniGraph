import { apiRequest, buildApiPath } from "@/lib/api/client";
import type { GraphBuildStatus } from "@/lib/api/types";

import type {
  CoauthorshipGraphMetrics,
  CoauthorshipGraphNodeMetrics,
  CoauthorshipGraphPayload,
  CoauthorshipSubgraphFilters,
  SemanticGraphMetrics,
  SemanticGraphNodeMetrics,
  SemanticGraphPayload,
  SemanticSubgraphFilters,
} from "@/lib/graphs/types";

export function getCoauthorshipStatus() {
  return apiRequest<GraphBuildStatus>("/api/v1/coauthorship-graph/status");
}

export function getCoauthorshipGraph() {
  return apiRequest<CoauthorshipGraphPayload>("/api/v1/coauthorship-graph");
}

export function getCoauthorshipSubgraph(filters: CoauthorshipSubgraphFilters) {
  return apiRequest<CoauthorshipGraphPayload>(
    buildApiPath("/api/v1/coauthorship-graph/subgraph", filters),
  );
}

export function getCoauthorshipMetrics() {
  return apiRequest<CoauthorshipGraphMetrics>("/api/v1/coauthorship-graph/metrics");
}

export function getCoauthorshipNodeMetrics(researcherId: string) {
  return apiRequest<CoauthorshipGraphNodeMetrics>(
    `/api/v1/coauthorship-graph/nodes/${researcherId}`,
  );
}

export function getSemanticStatus() {
  return apiRequest<GraphBuildStatus>("/api/v1/semantic-graph/status");
}

export function getSemanticGraph() {
  return apiRequest<SemanticGraphPayload>("/api/v1/semantic-graph");
}

export function getSemanticSubgraph(filters: SemanticSubgraphFilters) {
  return apiRequest<SemanticGraphPayload>(
    buildApiPath("/api/v1/semantic-graph/subgraph", filters),
  );
}

export function getSemanticMetrics() {
  return apiRequest<SemanticGraphMetrics>("/api/v1/semantic-graph/metrics");
}

export function getSemanticNodeMetrics(publicationId: string) {
  return apiRequest<SemanticGraphNodeMetrics>(
    `/api/v1/semantic-graph/nodes/${publicationId}`,
  );
}
