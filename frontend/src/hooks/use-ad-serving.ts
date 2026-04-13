"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AdUnit, AdUnitCreate, AdUnitUpdate, AdServingStats } from "@/types";

export function useAdUnits(campaignId: number) {
  return useQuery({
    queryKey: ["campaigns", campaignId, "ad-units"],
    queryFn: async () => {
      const response = await api.get<AdUnit[]>(
        `/campaigns/${campaignId}/ad-units`
      );
      return response.data;
    },
    enabled: !!campaignId,
  });
}

export function useCreateAdUnit(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AdUnitCreate) => {
      const response = await api.post<AdUnit>(
        `/campaigns/${campaignId}/ad-units`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["campaigns", campaignId, "ad-units"],
      });
    },
  });
}

export function useUpdateAdUnit(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      unitId,
      data,
    }: {
      unitId: number;
      data: AdUnitUpdate;
    }) => {
      const response = await api.put<AdUnit>(
        `/campaigns/${campaignId}/ad-units/${unitId}`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["campaigns", campaignId, "ad-units"],
      });
    },
  });
}

export function useDeleteAdUnit(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (unitId: number) => {
      await api.delete(`/campaigns/${campaignId}/ad-units/${unitId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["campaigns", campaignId, "ad-units"],
      });
    },
  });
}

export function useAdUnitStats(campaignId: number, unitId: number) {
  return useQuery({
    queryKey: ["campaigns", campaignId, "ad-units", unitId, "stats"],
    queryFn: async () => {
      const response = await api.get<AdServingStats>(
        `/campaigns/${campaignId}/ad-units/${unitId}/stats`
      );
      return response.data;
    },
    enabled: !!campaignId && !!unitId,
  });
}
