"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { UserSettings, UserSettingsUpdate } from "@/types";

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const response = await api.get<UserSettings>("/settings");
      return response.data;
    },
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UserSettingsUpdate) => {
      const response = await api.put<UserSettings>("/settings", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: async () => {
      const response = await api.post<{ openai: boolean; fal: boolean }>(
        "/settings/test-connection"
      );
      return response.data;
    },
  });
}
