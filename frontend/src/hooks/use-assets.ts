"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Asset } from "@/types";

export function useAssets(campaignId: number) {
  return useQuery({
    queryKey: ["assets", campaignId],
    queryFn: async () => {
      const response = await api.get<Asset[]>(`/assets/campaign/${campaignId}`);
      return response.data;
    },
    enabled: !!campaignId,
  });
}
