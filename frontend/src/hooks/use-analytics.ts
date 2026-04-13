"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AdPerformance, AdPerformanceSummary, AdPerformanceSource } from "@/types";

interface AnalyticsFilters {
  source?: AdPerformanceSource;
  from_date?: string;
  to_date?: string;
}

export function useCampaignAnalytics(campaignId: number, filters?: AnalyticsFilters) {
  return useQuery<AdPerformance[]>({
    queryKey: ["analytics", campaignId, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.source) params.set("source", filters.source);
      if (filters?.from_date) params.set("from_date", filters.from_date);
      if (filters?.to_date) params.set("to_date", filters.to_date);
      const qs = params.toString();
      const url = `/campaigns/${campaignId}/analytics${qs ? `?${qs}` : ""}`;
      const { data } = await api.get<AdPerformance[]>(url);
      return data;
    },
    enabled: !!campaignId,
  });
}

export function useCampaignAnalyticsSummary(campaignId: number) {
  return useQuery<AdPerformanceSummary>({
    queryKey: ["analytics", campaignId, "summary"],
    queryFn: async () => {
      const { data } = await api.get<AdPerformanceSummary>(
        `/campaigns/${campaignId}/analytics/summary`
      );
      return data;
    },
    enabled: !!campaignId,
  });
}

interface AddPerformanceEntry {
  source: AdPerformanceSource;
  date: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend_cents: number;
  revenue_cents: number;
}

export function useAddPerformanceEntry(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (entry: AddPerformanceEntry) => {
      const { data } = await api.post<AdPerformance>(
        `/campaigns/${campaignId}/analytics`,
        entry
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analytics", campaignId] });
    },
  });
}

export function useDeletePerformanceEntry(campaignId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (entryId: number) => {
      await api.delete(`/campaigns/${campaignId}/analytics/${entryId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analytics", campaignId] });
    },
  });
}
