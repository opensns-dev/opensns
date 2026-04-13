"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AIDisclosure } from "@/types";

interface AILabelingSettings {
  ai_disclosure_enabled: boolean;
  ai_label_text: string;
  ai_label_position: string;
}

interface LabelAssetResponse {
  asset_id: number;
  disclosure: AIDisclosure & {
    ai_generated: boolean;
    tool: string;
    model: string;
    timestamp: string;
  };
}

interface LabelCampaignResponse {
  campaign_id: number;
  labeled_count: number;
}

export function useAILabelingSettings() {
  return useQuery({
    queryKey: ["ai-labeling-settings"],
    queryFn: async () => {
      const response = await api.get<AILabelingSettings>(
        "/ai-labeling/settings"
      );
      return response.data;
    },
  });
}

export function useLabelAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (assetId: number) => {
      const response = await api.post<LabelAssetResponse>(
        `/ai-labeling/assets/${assetId}/label`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useLabelCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (campaignId: number) => {
      const response = await api.post<LabelCampaignResponse>(
        `/ai-labeling/campaigns/${campaignId}/label`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}
