import type { GraphBuildStatus } from "@/lib/api/types";

export type GraphLayer = "coauthorship" | "semantic";

export type CoauthorshipNode = {
  id: string;
  label: string;
  full_name: string;
  normalized_name: string;
  primary_organization_id: string | null;
  primary_organization_name: string | null;
  university_code: string | null;
  university_name: string | null;
  is_eunice_university: boolean;
  degree: number;
  strength: number;
  betweenness: number;
  component_id: number | null;
  community_id: number | null;
};

export type CoauthorshipEdge = {
  source: string;
  target: string;
  weight: number;
  shared_publication_count: number;
  first_collaboration_year: number | null;
  last_collaboration_year: number | null;
  shared_publication_ids: string[];
};

export type CoauthorshipGraphPayload = {
  build_id: string | null;
  graph_type: string;
  generated_at: string;
  summary: Record<string, unknown>;
  nodes: CoauthorshipNode[];
  edges: CoauthorshipEdge[];
  data_snapshot: Record<string, unknown>;
};

export type CoauthorshipGraphMetrics = {
  build_id: string | null;
  graph_version: string;
  node_count: number;
  edge_count: number;
  component_count: number;
  community_count: number | null;
  top_degree_nodes: CoauthorshipNode[];
  top_strength_nodes: CoauthorshipNode[];
  top_betweenness_nodes: CoauthorshipNode[];
};

export type CoauthorshipNodeMetricsNeighbor = {
  researcher_id: string;
  shared_publication_count: number;
  first_collaboration_year: number | null;
  last_collaboration_year: number | null;
  weight: number;
};

export type CoauthorshipGraphNodeMetrics = {
  build_id: string | null;
  node: CoauthorshipNode;
  incident_edges: CoauthorshipEdge[];
  neighbors: CoauthorshipNodeMetricsNeighbor[];
};

export type SemanticNode = {
  id: string;
  label: string;
  title: string;
  normalized_title: string;
  publication_year: number | null;
  doi: string | null;
  openaire_id: string | null;
  publication_type: string | null;
  language_code: string | null;
  journal_name: string | null;
  venue_name: string | null;
  authors: string[];
  organization_ids: string[];
  organization_names: string[];
  degree: number;
  strength: number;
  betweenness: number;
  component_id: number | null;
  community_id: number | null;
};

export type SemanticEdge = {
  source: string;
  target: string;
  weight: number;
  similarity_score: number;
  rank: number;
  mutual_match: boolean;
  source_rank: number | null;
  target_rank: number | null;
  source_score: number | null;
  target_score: number | null;
};

export type SemanticGraphPayload = {
  build_id: string | null;
  graph_type: string;
  generated_at: string;
  summary: Record<string, unknown>;
  nodes: SemanticNode[];
  edges: SemanticEdge[];
  data_snapshot: Record<string, unknown>;
};

export type SemanticGraphMetrics = {
  build_id: string | null;
  graph_version: string;
  node_count: number;
  edge_count: number;
  component_count: number;
  community_count: number | null;
  top_degree_nodes: SemanticNode[];
  top_strength_nodes: SemanticNode[];
  top_betweenness_nodes: SemanticNode[];
};

export type SemanticGraphNodeMetricsNeighbor = {
  publication_id: string;
  weight: number;
  similarity_score: number;
  rank: number;
  mutual_match: boolean;
};

export type SemanticGraphNodeMetrics = {
  build_id: string | null;
  node: SemanticNode;
  incident_edges: SemanticEdge[];
  neighbors: SemanticGraphNodeMetricsNeighbor[];
};

export type CoauthorshipSubgraphFilters = {
  researcher_id?: string;
  organization_id?: string;
  max_nodes?: number;
  min_edge_weight?: number;
  community_id?: number;
};

export type SemanticSubgraphFilters = {
  publication_id?: string;
  organization_id?: string;
  publication_year?: number;
  max_nodes?: number;
  min_edge_weight?: number;
  community_id?: number;
};

export type ExplorerGraphStatus = GraphBuildStatus;
