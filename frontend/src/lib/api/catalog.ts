import { apiRequest, buildApiPath } from "@/lib/api/client";
import type {
  Organization,
  Publication,
  PublicationAuthor,
  PublicationEmbedding,
  PublicationOrganization,
  Researcher,
  ResearcherAffiliation,
} from "@/lib/api/types";

export type PublicationFilters = {
  title?: string;
  publication_year?: number;
  doi?: string;
  openaire_id?: string;
  limit?: number;
  offset?: number;
};

export type ResearcherFilters = {
  name?: string;
  orcid?: string;
  primary_organization_id?: string;
  limit?: number;
  offset?: number;
};

export type OrganizationFilters = {
  name?: string;
  organization_type?: string;
  parent_organization_id?: string;
  limit?: number;
  offset?: number;
};

export function listPublications(filters: PublicationFilters = {}) {
  return apiRequest<Publication[]>(buildApiPath("/api/v1/publications", filters));
}

export function getPublication(id: string) {
  return apiRequest<Publication>(`/api/v1/publications/${id}`);
}

export function listPublicationAuthors(id: string) {
  return apiRequest<PublicationAuthor[]>(`/api/v1/publications/${id}/authors`);
}

export function listPublicationOrganizations(id: string) {
  return apiRequest<PublicationOrganization[]>(`/api/v1/publications/${id}/organizations`);
}

export function getPublicationEmbedding(id: string) {
  return apiRequest<PublicationEmbedding>(`/api/v1/publications/${id}/embedding`);
}

export function listResearchers(filters: ResearcherFilters = {}) {
  return apiRequest<Researcher[]>(buildApiPath("/api/v1/researchers", filters));
}

export function getResearcher(id: string) {
  return apiRequest<Researcher>(`/api/v1/researchers/${id}`);
}

export function listResearcherAffiliations(id: string) {
  return apiRequest<ResearcherAffiliation[]>(`/api/v1/researchers/${id}/affiliations`);
}

export function listOrganizations(filters: OrganizationFilters = {}) {
  return apiRequest<Organization[]>(buildApiPath("/api/v1/organizations", filters));
}

export function getOrganization(id: string) {
  return apiRequest<Organization>(`/api/v1/organizations/${id}`);
}
