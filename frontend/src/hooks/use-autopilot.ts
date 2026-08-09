"use client";

import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  AutopilotRule,
  AutopilotRuleCreate,
  AutopilotRuleUpdate,
  AutopilotRunLog,
} from "@/types";

export function useAutopilotRules() {
  return useQuery({
    queryKey: ["autopilot-rules"],
    queryFn: async () => {
      const response = await api.get<AutopilotRule[]>("/autopilot/rules");
      return response.data;
    },
  });
}

export function useCreateAutopilotRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AutopilotRuleCreate) => {
      const response = await api.post<AutopilotRule>("/autopilot/rules", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["autopilot-rules"] });
    },
  });
}

export function useUpdateAutopilotRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      ruleId,
      data,
    }: {
      ruleId: number;
      data: AutopilotRuleUpdate;
    }) => {
      const response = await api.put<AutopilotRule>(
        `/autopilot/rules/${ruleId}`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["autopilot-rules"] });
    },
  });
}

export function useDeleteAutopilotRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ruleId: number) => {
      await api.delete(`/autopilot/rules/${ruleId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["autopilot-rules"] });
    },
  });
}

export function useToggleAutopilotRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ruleId: number) => {
      const response = await api.post<AutopilotRule>(
        `/autopilot/rules/${ruleId}/toggle`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["autopilot-rules"] });
    },
  });
}

export function useAutopilotHistory(ruleId: number) {
  return useQuery({
    queryKey: ["autopilot-history", ruleId],
    queryFn: async () => {
      const response = await api.get<AutopilotRunLog[]>(
        `/autopilot/rules/${ruleId}/history`
      );
      return response.data;
    },
    enabled: !!ruleId,
  });
}

export function useAutopilotHistories(ruleIds: number[]) {
  return useQueries({
    queries: ruleIds.map((ruleId) => ({
      queryKey: ["autopilot-history", ruleId],
      queryFn: async () => {
        const response = await api.get<AutopilotRunLog[]>(
          `/autopilot/rules/${ruleId}/history`
        );
        return response.data;
      },
      enabled: !!ruleId,
    })),
  });
}

export function useRunAutopilotNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ruleId: number) => {
      const response = await api.post<AutopilotRule>(
        `/autopilot/rules/${ruleId}/run-now`
      );
      return response.data;
    },
    onSuccess: (_data, ruleId) => {
      queryClient.invalidateQueries({ queryKey: ["autopilot-rules"] });
      queryClient.invalidateQueries({ queryKey: ["autopilot-history", ruleId] });
      queryClient.invalidateQueries({ queryKey: ["autopilot-history"] });
    },
  });
}
