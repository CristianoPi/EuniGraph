"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  buildCoauthorshipGraph,
  buildEmbeddings,
  buildSemanticGraph,
  createOrganization,
  createPublication,
  createResearcher,
  getCoauthorshipAdminStatus,
  getEmbeddingsProvider,
  getEmbeddingsStatus,
  getNormalizationStatus,
  getSeedStatus,
  getSemanticGraphAdminStatus,
  listNormalizationFindings,
  loadAllEmbeddings,
  loadSeed,
  resetEmbeddings,
  resetSeed,
  runNormalization,
  type EmbeddingsBuildRequest,
  type EmbeddingsLoadAllRequest,
  type GraphBuildRequest,
  type NormalizationRunRequest,
  type OrganizationCreatePayload,
  type PublicationCreatePayload,
  type ResearcherCreatePayload,
  type SeedLoadRequest,
  type SemanticGraphBuildRequest,
} from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/query-keys";

function useInvalidateAdminState() {
  const queryClient = useQueryClient();

  return {
    seed() {
      void queryClient.invalidateQueries({ queryKey: queryKeys.adminSeedStatus });
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboardCounts });
      void queryClient.invalidateQueries({ queryKey: ["publications"] });
      void queryClient.invalidateQueries({ queryKey: ["researchers"] });
      void queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
    normalization() {
      void queryClient.invalidateQueries({ queryKey: queryKeys.adminNormalizationStatus });
      void queryClient.invalidateQueries({ queryKey: queryKeys.adminNormalizationFindings });
      void queryClient.invalidateQueries({ queryKey: ["publications"] });
      void queryClient.invalidateQueries({ queryKey: ["researchers"] });
      void queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
    embeddings() {
      void queryClient.invalidateQueries({ queryKey: queryKeys.adminEmbeddingsStatus });
      void queryClient.invalidateQueries({ queryKey: queryKeys.embeddingsStatus });
      void queryClient.invalidateQueries({ queryKey: ["publication-embedding"] });
    },
    coauthorship() {
      void queryClient.invalidateQueries({ queryKey: queryKeys.adminCoauthorshipStatus });
      void queryClient.invalidateQueries({ queryKey: queryKeys.coauthorshipStatus });
      void queryClient.invalidateQueries({ queryKey: ["coauthorship-graph"] });
      void queryClient.invalidateQueries({ queryKey: queryKeys.coauthorshipMetrics });
    },
    semantic() {
      void queryClient.invalidateQueries({ queryKey: queryKeys.adminSemanticStatus });
      void queryClient.invalidateQueries({ queryKey: queryKeys.semanticGraphStatus });
      void queryClient.invalidateQueries({ queryKey: ["semantic-graph"] });
      void queryClient.invalidateQueries({ queryKey: queryKeys.semanticMetrics });
    },
    catalog() {
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboardCounts });
      void queryClient.invalidateQueries({ queryKey: ["publications"] });
      void queryClient.invalidateQueries({ queryKey: ["researchers"] });
      void queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  };
}

export function useAdminSeedStatus() {
  return useQuery({
    queryKey: queryKeys.adminSeedStatus,
    queryFn: getSeedStatus,
  });
}

export function useAdminNormalizationStatus() {
  return useQuery({
    queryKey: queryKeys.adminNormalizationStatus,
    queryFn: getNormalizationStatus,
  });
}

export function useAdminNormalizationFindings() {
  return useQuery({
    queryKey: queryKeys.adminNormalizationFindings,
    queryFn: listNormalizationFindings,
  });
}

export function useAdminEmbeddingsProvider() {
  return useQuery({
    queryKey: queryKeys.adminEmbeddingsProvider,
    queryFn: getEmbeddingsProvider,
  });
}

export function useAdminEmbeddingsStatus() {
  return useQuery({
    queryKey: queryKeys.adminEmbeddingsStatus,
    queryFn: getEmbeddingsStatus,
  });
}

export function useAdminCoauthorshipStatus() {
  return useQuery({
    queryKey: queryKeys.adminCoauthorshipStatus,
    queryFn: getCoauthorshipAdminStatus,
  });
}

export function useAdminSemanticGraphStatus() {
  return useQuery({
    queryKey: queryKeys.adminSemanticStatus,
    queryFn: getSemanticGraphAdminStatus,
  });
}

export function useLoadSeedMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: SeedLoadRequest) => loadSeed(payload),
    onSuccess: invalidate.seed,
  });
}

export function useResetSeedMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: resetSeed,
    onSuccess: invalidate.seed,
  });
}

export function useRunNormalizationMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: NormalizationRunRequest) => runNormalization(payload),
    onSuccess: invalidate.normalization,
  });
}

export function useBuildEmbeddingsMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: EmbeddingsBuildRequest) => buildEmbeddings(payload),
    onSuccess: invalidate.embeddings,
  });
}

export function useLoadAllEmbeddingsMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: EmbeddingsLoadAllRequest) => loadAllEmbeddings(payload),
    onSuccess: invalidate.embeddings,
  });
}

export function useResetEmbeddingsMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: resetEmbeddings,
    onSuccess: invalidate.embeddings,
  });
}

export function useBuildCoauthorshipGraphMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: GraphBuildRequest) => buildCoauthorshipGraph(payload),
    onSuccess: invalidate.coauthorship,
  });
}

export function useBuildSemanticGraphMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: SemanticGraphBuildRequest) => buildSemanticGraph(payload),
    onSuccess: invalidate.semantic,
  });
}

export function useCreatePublicationMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: PublicationCreatePayload) => createPublication(payload),
    onSuccess: invalidate.catalog,
  });
}

export function useCreateResearcherMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: ResearcherCreatePayload) => createResearcher(payload),
    onSuccess: invalidate.catalog,
  });
}

export function useCreateOrganizationMutation() {
  const invalidate = useInvalidateAdminState();

  return useMutation({
    mutationFn: (payload: OrganizationCreatePayload) => createOrganization(payload),
    onSuccess: invalidate.catalog,
  });
}
