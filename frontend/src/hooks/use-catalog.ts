"use client";

import { useQueries, useQuery } from "@tanstack/react-query";

import {
  getOrganization,
  getPublication,
  getPublicationEmbedding,
  getResearcher,
  listOrganizations,
  listPublicationAuthors,
  listPublicationOrganizations,
  listPublications,
  listResearcherAffiliations,
  listResearchers,
  type OrganizationFilters,
  type PublicationFilters,
  type ResearcherFilters,
} from "@/lib/api/catalog";
import { queryKeys } from "@/lib/api/query-keys";

export function usePublications(filters: PublicationFilters) {
  return useQuery({
    queryKey: queryKeys.publications(filters),
    queryFn: () => listPublications(filters),
  });
}

export function usePublication(id: string) {
  return useQuery({
    queryKey: queryKeys.publication(id),
    queryFn: () => getPublication(id),
    enabled: Boolean(id),
  });
}

export function usePublicationAuthors(id: string) {
  return useQuery({
    queryKey: queryKeys.publicationAuthors(id),
    queryFn: () => listPublicationAuthors(id),
    enabled: Boolean(id),
  });
}

export function usePublicationOrganizations(id: string) {
  return useQuery({
    queryKey: queryKeys.publicationOrganizations(id),
    queryFn: () => listPublicationOrganizations(id),
    enabled: Boolean(id),
  });
}

export function usePublicationEmbedding(id: string) {
  return useQuery({
    queryKey: queryKeys.publicationEmbedding(id),
    queryFn: () => getPublicationEmbedding(id),
    enabled: Boolean(id),
    retry: false,
  });
}

export function useResearchers(filters: ResearcherFilters) {
  return useQuery({
    queryKey: queryKeys.researchers(filters),
    queryFn: () => listResearchers(filters),
  });
}

export function useResearcher(id: string) {
  return useQuery({
    queryKey: queryKeys.researcher(id),
    queryFn: () => getResearcher(id),
    enabled: Boolean(id),
  });
}

export function useResearcherAffiliations(id: string) {
  return useQuery({
    queryKey: queryKeys.researcherAffiliations(id),
    queryFn: () => listResearcherAffiliations(id),
    enabled: Boolean(id),
  });
}

export function useOrganizations(filters: OrganizationFilters) {
  return useQuery({
    queryKey: queryKeys.organizations(filters),
    queryFn: () => listOrganizations(filters),
  });
}

export function useOrganization(id: string) {
  return useQuery({
    queryKey: queryKeys.organization(id),
    queryFn: () => getOrganization(id),
    enabled: Boolean(id),
  });
}

export function useResearchersByIds(ids: string[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: queryKeys.researcher(id),
      queryFn: () => getResearcher(id),
      enabled: Boolean(id),
    })),
  });
}

export function useOrganizationsByIds(ids: string[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: queryKeys.organization(id),
      queryFn: () => getOrganization(id),
      enabled: Boolean(id),
    })),
  });
}
