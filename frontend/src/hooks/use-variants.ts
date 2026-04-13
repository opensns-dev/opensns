"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AdVariant, AdVariantCreate } from "@/types";

export function useVariants(campaignId: number) {
  return useQuery({
    queryKey: ["campaigns", campaignId, "variants"],
    queryFn: async () => {
      const response = await api.get<AdVariant[]>(
        `/campaigns/${campaignId}/variants`
      );
      return response.data;
    },
    enabled: !!campaignId,
  });
}

export function useCreateVariant(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AdVariantCreate) => {
      const response = await api.post<AdVariant>(
        `/campaigns/${campaignId}/variants`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["campaigns", campaignId, "variants"],
      });
    },
  });
}

export function useAutoGenerateVariants(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post<AdVariant[]>(
        `/campaigns/${campaignId}/variants/auto-generate`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["campaigns", campaignId, "variants"],
      });
    },
  });
}

export function useUpdateVariant(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      variantId,
      data,
    }: {
      variantId: number;
      data: AdVariantCreate;
    }) => {
      const response = await api.put<AdVariant>(
        `/campaigns/${campaignId}/variants/${variantId}`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["campaigns", campaignId, "variants"],
      });
    },
  });
}

export function useDeleteVariant(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (variantId: number) => {
      await api.delete(`/campaigns/${campaignId}/variants/${variantId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["campaigns", campaignId, "variants"],
      });
    },
  });
}
