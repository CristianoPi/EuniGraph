import { apiRequest } from "@/lib/api/client";
import type { Organization, Publication, Researcher } from "@/lib/api/types";

export type SeedStatus = {
  dataset_path: string;
  dataset_path_exists: boolean;
  required_files: Record<string, boolean>;
  table_counts: Record<string, number>;
  latest_ingestion_run_id: string | null;
  latest_ingestion_status: string | null;
};

export type SeedLoadRequest = {
  limit_per_file?: number | null;
};

export type SeedLoadResponse = {
  dataset_path: string;
  ingestion_run_id: string | null;
  limit_per_file: number | null;
  datasource_records: number;
  organization_records: number;
  publication_records: number;
  project_records: number;
  relation_records: number;
};

export type SeedResetResponse = {
  publication_author: number;
  publication_organization: number;
  external_identifier: number;
  publication: number;
  researcher: number;
  organization: number;
  source_record: number;
  ingestion_run: number;
  data_source: number;
};

export type NormalizationRunRequest = {
  notes?: string | null;
};

export type NormalizationRun = {
  run_id: string;
  status: string;
  normalized_publications: number;
  normalized_researchers: number;
  normalized_organizations: number;
  auto_merged_publications: number;
  auto_merged_researchers: number;
  auto_merged_organizations: number;
  findings_count: number;
  completed_at: string | null;
};

export type NormalizationFinding = {
  id: string;
  run_id: string;
  entity_type: string;
  entity_id: string | null;
  candidate_entity_id: string | null;
  finding_type: string;
  confidence: string;
  auto_applied: boolean;
  message: string;
  details: Record<string, unknown> | null;
  created_at: string;
};

export type EmbeddingsProvider = {
  enabled: boolean;
  provider: string;
  model: string;
  embedding_version: string;
  batch_size: number;
  request_timeout_seconds: number;
  max_retries: number;
  content_fields: string[];
  qdrant_collection: string;
  qdrant_api_key_configured: boolean;
  gemini_api_key_configured: boolean;
};

export type EmbeddingsStatus = {
  enabled: boolean;
  provider: string;
  model: string;
  embedding_version: string;
  qdrant_collection: string;
  qdrant_collection_exists: boolean;
  qdrant_points_count: number;
  qdrant_collection_status: string | null;
  total_publications: number;
  active_embeddings_count: number;
  latest_embedding_updated_at: string | null;
};

export type EmbeddingsBuildRequest = {
  publication_ids?: string[] | null;
  limit?: number | null;
  force: boolean;
};

export type EmbeddingsLoadAllRequest = {
  force: boolean;
};

export type PublicationEmbeddingBuildOutcome = {
  publication_id: string;
  status: string;
  reason: string | null;
  embedding_id: string | null;
  qdrant_point_id: string | null;
};

export type EmbeddingsBuildResponse = {
  provider: string;
  model: string;
  embedding_version: string;
  collection_name: string;
  processed_count: number;
  generated_count: number;
  skipped_count: number;
  failed_count: number;
  results: PublicationEmbeddingBuildOutcome[];
};

export type EmbeddingsResetResponse = {
  collection_name: string;
  collection_deleted: boolean;
  deleted_metadata_count: number;
  provider: string;
  model: string;
  embedding_version: string;
};

export type GraphBuildRequest = {
  triggered_by?: string | null;
  include_isolated_nodes: boolean;
};

export type SemanticGraphBuildRequest = {
  triggered_by?: string | null;
  top_k: number;
  score_threshold?: number | null;
  edge_symmetry_policy: string;
  mutual_knn: boolean;
  include_isolated_nodes: boolean;
  publication_type?: string | null;
  language_code?: string | null;
  year_from?: number | null;
  year_to?: number | null;
};

export type GraphBuildStatus = {
  build_id: string | null;
  graph_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  triggered_by: string | null;
  is_active: boolean;
  node_count: number | null;
  edge_count: number | null;
  component_count: number | null;
  community_count: number | null;
  graph_version: string | null;
  artifact_paths: Record<string, string> | null;
  build_params: Record<string, unknown> | null;
  data_snapshot: Record<string, unknown> | null;
  error_message: string | null;
  latest_successful_build_id: string | null;
};

export type PublicationCreatePayload = {
  title: string;
  abstract?: string | null;
  publication_year?: number | null;
  publication_date?: string | null;
  doi?: string | null;
  openaire_id?: string | null;
  publication_type?: string | null;
  language_code?: string | null;
  journal_name?: string | null;
  venue_name?: string | null;
  publisher?: string | null;
  open_access?: boolean | null;
  source_url?: string | null;
};

export type ResearcherCreatePayload = {
  full_name: string;
  given_name?: string | null;
  family_name?: string | null;
  display_name?: string | null;
  orcid?: string | null;
  email?: string | null;
  profile_url?: string | null;
  primary_organization_id?: string | null;
};

export type OrganizationCreatePayload = {
  name: string;
  organization_type?: string | null;
  country_code?: string | null;
  city?: string | null;
  website?: string | null;
  parent_organization_id?: string | null;
  ror_id?: string | null;
  openaire_id?: string | null;
};

function postJson<TResponse, TPayload>(path: string, payload: TPayload): Promise<TResponse> {
  return apiRequest<TResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getSeedStatus() {
  return apiRequest<SeedStatus>("/api/v1/admin/seeds/openaire-beginners-kit/status");
}

export function loadSeed(payload: SeedLoadRequest) {
  return postJson<SeedLoadResponse, SeedLoadRequest>(
    "/api/v1/admin/seeds/openaire-beginners-kit/load",
    payload,
  );
}

export function resetSeed() {
  return apiRequest<SeedResetResponse>("/api/v1/admin/seeds/openaire-beginners-kit/reset", {
    method: "POST",
  });
}

export function getNormalizationStatus() {
  return apiRequest<NormalizationRun | null>("/api/v1/admin/normalization/status");
}

export function runNormalization(payload: NormalizationRunRequest) {
  return postJson<NormalizationRun, NormalizationRunRequest>(
    "/api/v1/admin/normalization/run",
    payload,
  );
}

export function listNormalizationFindings() {
  return apiRequest<NormalizationFinding[]>("/api/v1/admin/normalization/findings?limit=10");
}

export function getEmbeddingsProvider() {
  return apiRequest<EmbeddingsProvider>("/api/v1/embeddings/provider");
}

export function getEmbeddingsStatus() {
  return apiRequest<EmbeddingsStatus>("/api/v1/embeddings/status");
}

export function buildEmbeddings(payload: EmbeddingsBuildRequest) {
  return postJson<EmbeddingsBuildResponse, EmbeddingsBuildRequest>(
    "/api/v1/embeddings/build",
    payload,
  );
}

export function loadAllEmbeddings(payload: EmbeddingsLoadAllRequest) {
  return postJson<EmbeddingsBuildResponse, EmbeddingsLoadAllRequest>(
    "/api/v1/embeddings/load-all",
    payload,
  );
}

export function resetEmbeddings() {
  return apiRequest<EmbeddingsResetResponse>("/api/v1/embeddings/reset", {
    method: "POST",
  });
}

export function getCoauthorshipAdminStatus() {
  return apiRequest<GraphBuildStatus>("/api/v1/coauthorship-graph/status");
}

export function buildCoauthorshipGraph(payload: GraphBuildRequest) {
  return postJson<GraphBuildStatus, GraphBuildRequest>(
    "/api/v1/coauthorship-graph/build",
    payload,
  );
}

export function getSemanticGraphAdminStatus() {
  return apiRequest<GraphBuildStatus>("/api/v1/semantic-graph/status");
}

export function buildSemanticGraph(payload: SemanticGraphBuildRequest) {
  return postJson<GraphBuildStatus, SemanticGraphBuildRequest>(
    "/api/v1/semantic-graph/build",
    payload,
  );
}

export function createPublication(payload: PublicationCreatePayload) {
  return postJson<Publication, PublicationCreatePayload>("/api/v1/publications", payload);
}

export function createResearcher(payload: ResearcherCreatePayload) {
  return postJson<Researcher, ResearcherCreatePayload>("/api/v1/researchers", payload);
}

export function createOrganization(payload: OrganizationCreatePayload) {
  return postJson<Organization, OrganizationCreatePayload>("/api/v1/organizations", payload);
}
