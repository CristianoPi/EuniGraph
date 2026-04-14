export type HealthResponse = {
  service: string;
  status: string;
};

export type Publication = {
  id: string;
  title: string;
  publication_year?: number | null;
  doi?: string | null;
  openaire_id?: string | null;
};

export type GraphBuildStatus = {
  id?: string | null;
  graph_type?: string | null;
  status: string;
  node_count?: number | null;
  edge_count?: number | null;
  created_at?: string | null;
  completed_at?: string | null;
  artifact_paths?: Record<string, string> | null;
  error_message?: string | null;
};

export type EmbeddingsStatus = {
  enabled: boolean;
  provider: string;
  model: string;
  version: string;
  collection: string;
  collection_exists: boolean;
  points_count?: number | null;
};
