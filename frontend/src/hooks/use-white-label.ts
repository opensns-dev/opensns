"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  WhiteLabelConfig,
  WhiteLabelConfigCreate,
  WhiteLabelConfigUpdate,
} from "@/types";

export function useWhiteLabelConfig() {
  return useQuery({
    queryKey: ["white-label"],
    queryFn: async () => {
      const response = await api.get<WhiteLabelConfig>("/white-label");
      return response.data;
    },
    retry: (failureCount, error) => {
      if ((error as { response?: { status?: number } }).response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

export function useCreateWhiteLabel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: WhiteLabelConfigCreate) => {
      const response = await api.post<WhiteLabelConfig>("/white-label", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["white-label"] });
    },
  });
}

export function useUpdateWhiteLabel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: WhiteLabelConfigUpdate) => {
      const response = await api.put<WhiteLabelConfig>("/white-label", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["white-label"] });
    },
  });
}

export function useDeleteWhiteLabel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await api.delete("/white-label");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["white-label"] });
    },
  });
}

export function useActivateWhiteLabel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post<WhiteLabelConfig>("/white-label/activate");
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["white-label"] });
    },
  });
}

export function useDeactivateWhiteLabel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post<WhiteLabelConfig>("/white-label/deactivate");
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["white-label"] });
    },
  });
}
