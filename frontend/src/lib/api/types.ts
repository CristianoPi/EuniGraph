export type HealthResponse = {
  service: string;
  status: string;
};

export type Publication = {
  id: string;
  title: string;
  normalized_title: string;
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
  canonical_source_record_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type PublicationAuthor = {
  id: string;
  publication_id: string;
  researcher_id: string;
  author_position: number;
  author_list_name?: string | null;
  is_corresponding?: boolean | null;
  source_record_id?: string | null;
  created_at: string;
};

export type PublicationOrganization = {
  id: string;
  publication_id: string;
  organization_id: string;
  relation_type: string;
  source_record_id?: string | null;
  created_at: string;
};

export type PublicationEmbedding = {
  publication_id: string;
  qdrant_collection: string;
  qdrant_point_id: string;
  embedding_provider: string;
  embedding_model: string;
  embedding_version: string;
  content_hash: string;
  created_at: string;
  updated_at: string;
};

export type Researcher = {
  id: string;
  full_name: string;
  given_name?: string | null;
  family_name?: string | null;
  normalized_name: string;
  display_name?: string | null;
  orcid?: string | null;
  email?: string | null;
  profile_url?: string | null;
  primary_organization_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type ResearcherAffiliation = {
  id: string;
  researcher_id: string;
  organization_id: string;
  role_title?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_primary: boolean;
  source_record_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type Organization = {
  id: string;
  name: string;
  normalized_name: string;
  organization_type?: string | null;
  country_code?: string | null;
  city?: string | null;
  website?: string | null;
  parent_organization_id?: string | null;
  ror_id?: string | null;
  openaire_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type GraphBuildStatus = {
  build_id?: string | null;
  graph_type: string;
  status: string;
  started_at?: string | null;
  node_count?: number | null;
  edge_count?: number | null;
  component_count?: number | null;
  community_count?: number | null;
  created_at?: string | null;
  completed_at?: string | null;
  is_active?: boolean;
  graph_version?: string | null;
  artifact_paths?: Record<string, string> | null;
  build_params?: Record<string, unknown> | null;
  data_snapshot?: Record<string, unknown> | null;
  error_message?: string | null;
};

export type EmbeddingsStatus = {
  enabled: boolean;
  provider: string;
  model: string;
  embedding_version: string;
  qdrant_collection: string;
  qdrant_collection_exists: boolean;
  qdrant_points_count: number;
  qdrant_collection_status?: string | null;
  total_publications: number;
  active_embeddings_count: number;
  latest_embedding_updated_at?: string | null;
};
