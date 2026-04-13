"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PublishConnection, PublishLog, PublishRequest } from "@/types";

export function usePublishConnections() {
  return useQuery({
    queryKey: ["publish-connections"],
    queryFn: async () => {
      const response = await api.get<PublishConnection[]>(
        "/publishing/connections"
      );
      return response.data;
    },
  });
}

export function useDeleteConnection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (connectionId: number) => {
      await api.delete(`/publishing/connections/${connectionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["publish-connections"] });
    },
  });
}

export function useConnectMeta() {
  return useMutation({
    mutationFn: async () => {
      const response = await api.get<{ auth_url: string; state: string }>(
        "/publishing/meta/auth"
      );
      return response.data;
    },
  });
}

export function usePublishCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      campaignId,
      data,
    }: {
      campaignId: number;
      data: PublishRequest;
    }) => {
      const response = await api.post<PublishLog>(
        `/publishing/campaigns/${campaignId}/publish`,
        data
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["publish-logs", variables.campaignId],
      });
    },
  });
}

export function usePublishLogs(campaignId: number) {
  return useQuery({
    queryKey: ["publish-logs", campaignId],
    queryFn: async () => {
      const response = await api.get<PublishLog[]>(
        `/publishing/campaigns/${campaignId}/logs`
      );
      return response.data;
    },
    enabled: !!campaignId,
  });
}
