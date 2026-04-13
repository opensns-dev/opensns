"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PredictionComparison, PredictionAccuracySummary } from "@/types";

export function usePredictions(campaignId: number) {
  return useQuery<PredictionComparison>({
    queryKey: ["predictions", campaignId],
    queryFn: async () => {
      const { data } = await api.get<PredictionComparison>(
        `/campaigns/${campaignId}/predictions`
      );
      return data;
    },
    enabled: !!campaignId,
    retry: false,
  });
}

export function useSyncPredictions(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<PredictionComparison>(
        `/campaigns/${campaignId}/predictions/sync`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["predictions", campaignId] });
    },
  });
}

interface ActualsUpdate {
  actual_ctr?: number;
  actual_engagement_rate?: number;
  actual_conversion_rate?: number;
  actual_impressions?: number;
  actual_clicks?: number;
  actual_conversions?: number;
}

export function useUpdateActuals(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (actuals: ActualsUpdate) => {
      const { data } = await api.put<PredictionComparison>(
        `/campaigns/${campaignId}/predictions/actuals`,
        actuals
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["predictions", campaignId] });
    },
  });
}

export function usePredictionSummary() {
  return useQuery<PredictionAccuracySummary>({
    queryKey: ["predictions", "summary"],
    queryFn: async () => {
      const { data } = await api.get<PredictionAccuracySummary>(
        `/campaigns/predictions/summary`
      );
      return data;
    },
  });
}
