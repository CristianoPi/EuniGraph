"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getCoauthorshipGraph,
  getCoauthorshipMetrics,
  getCoauthorshipNodeMetrics,
  getCoauthorshipStatus,
  getCoauthorshipSubgraph,
  getSemanticGraph,
  getSemanticMetrics,
  getSemanticNodeMetrics,
  getSemanticStatus,
  getSemanticSubgraph,
} from "@/lib/api/graphs";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  CoauthorshipSubgraphFilters,
  GraphLayer,
  SemanticSubgraphFilters,
} from "@/lib/graphs/types";

function hasCoauthorshipFilters(filters: CoauthorshipSubgraphFilters): boolean {
  return Boolean(
    filters.researcher_id ||
      filters.organization_id ||
      filters.max_nodes ||
      filters.min_edge_weight ||
      filters.community_id !== undefined,
  );
}

function hasSemanticFilters(filters: SemanticSubgraphFilters): boolean {
  return Boolean(
    filters.publication_id ||
      filters.organization_id ||
      filters.publication_year ||
      filters.max_nodes ||
      filters.min_edge_weight ||
      filters.community_id !== undefined,
  );
}

export function useCoauthorshipGraphStatus(enabled = true) {
  return useQuery({
    queryKey: queryKeys.coauthorshipStatus,
    queryFn: getCoauthorshipStatus,
    enabled,
  });
}

export function useSemanticGraphStatus(enabled = true) {
  return useQuery({
    queryKey: queryKeys.semanticGraphStatus,
    queryFn: getSemanticStatus,
    enabled,
  });
}

export function useCoauthorshipGraph(
  filters: CoauthorshipSubgraphFilters,
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.coauthorshipGraph(filters),
    queryFn: () =>
      hasCoauthorshipFilters(filters)
        ? getCoauthorshipSubgraph(filters)
        : getCoauthorshipGraph(),
    enabled,
  });
}

export function useSemanticGraph(filters: SemanticSubgraphFilters, enabled = true) {
  return useQuery({
    queryKey: queryKeys.semanticGraph(filters),
    queryFn: () =>
      hasSemanticFilters(filters) ? getSemanticSubgraph(filters) : getSemanticGraph(),
    enabled,
  });
}

export function useCoauthorshipMetrics(enabled = true) {
  return useQuery({
    queryKey: queryKeys.coauthorshipMetrics,
    queryFn: getCoauthorshipMetrics,
    enabled,
  });
}

export function useSemanticMetrics(enabled = true) {
  return useQuery({
    queryKey: queryKeys.semanticMetrics,
    queryFn: getSemanticMetrics,
    enabled,
  });
}

export function useCoauthorshipNodeMetrics(researcherId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.coauthorshipNode(researcherId ?? "none"),
    queryFn: () => getCoauthorshipNodeMetrics(researcherId!),
    enabled: enabled && Boolean(researcherId),
  });
}

export function useSemanticNodeMetrics(publicationId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.semanticNode(publicationId ?? "none"),
    queryFn: () => getSemanticNodeMetrics(publicationId!),
    enabled: enabled && Boolean(publicationId),
  });
}

export function useGraphStatus(layer: GraphLayer) {
  return layer === "coauthorship" ? useCoauthorshipGraphStatus() : useSemanticGraphStatus();
}

export function useGraphMetrics(layer: GraphLayer) {
  return layer === "coauthorship" ? useCoauthorshipMetrics() : useSemanticMetrics();
}
