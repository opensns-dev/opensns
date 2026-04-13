"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CustomVoice,
  CustomVoiceCreate,
  CustomAvatar,
  CustomAvatarCreate,
} from "@/types";

export function useCustomVoices() {
  return useQuery({
    queryKey: ["custom-voices"],
    queryFn: async () => {
      const response = await api.get<CustomVoice[]>("/custom-media/voices");
      return response.data;
    },
  });
}

export function useCreateVoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CustomVoiceCreate) => {
      const response = await api.post<CustomVoice>(
        "/custom-media/voices",
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-voices"] });
    },
  });
}

export function useDeleteVoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/custom-media/voices/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-voices"] });
    },
  });
}

export function useVoiceStatus(voiceId: number | null) {
  return useQuery({
    queryKey: ["custom-voices", voiceId, "status"],
    queryFn: async () => {
      const response = await api.get<CustomVoice>(
        `/custom-media/voices/${voiceId}/status`,
      );
      return response.data;
    },
    enabled: voiceId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "PENDING" || status === "PROCESSING") return 10_000;
      return false;
    },
  });
}

export function useCustomAvatars() {
  return useQuery({
    queryKey: ["custom-avatars"],
    queryFn: async () => {
      const response = await api.get<CustomAvatar[]>("/custom-media/avatars");
      return response.data;
    },
  });
}

export function useCreateAvatar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CustomAvatarCreate) => {
      const response = await api.post<CustomAvatar>(
        "/custom-media/avatars",
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-avatars"] });
    },
  });
}

export function useDeleteAvatar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/custom-media/avatars/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-avatars"] });
    },
  });
}

export function useAvatarStatus(avatarId: number | null) {
  return useQuery({
    queryKey: ["custom-avatars", avatarId, "status"],
    queryFn: async () => {
      const response = await api.get<CustomAvatar>(
        `/custom-media/avatars/${avatarId}/status`,
      );
      return response.data;
    },
    enabled: avatarId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "PENDING" || status === "PROCESSING") return 10_000;
      return false;
    },
  });
}
