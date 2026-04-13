"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Campaign, CampaignCreate } from "@/types";

export function useCampaigns() {
  return useQuery({
    queryKey: ["campaigns"],
    queryFn: async () => {
      const response = await api.get<Campaign[]>("/campaigns");
      return response.data;
    },
    staleTime: 30000,
  });
}

export function useCampaign(id: number) {
  return useQuery({
    queryKey: ["campaigns", id],
    queryFn: async () => {
      const response = await api.get<Campaign>(`/campaigns/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CampaignCreate) => {
      const response = await api.post<Campaign>("/campaigns", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/campaigns/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}
