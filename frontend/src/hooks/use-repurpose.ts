"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { RepurposeJob, RepurposeContent, RepurposeJobCreate } from "@/types";

export function useRepurposeJobs() {
  return useQuery({
    queryKey: ["repurpose-jobs"],
    queryFn: async () => {
      const response = await api.get<RepurposeJob[]>("/repurpose/");
      return response.data;
    },
  });
}

export function useRepurposeJob(id: number) {
  return useQuery({
    queryKey: ["repurpose-jobs", id],
    queryFn: async () => {
      const response = await api.get<RepurposeJob>(`/repurpose/${id}`);
      return response.data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && !["COMPLETED", "FAILED"].includes(status)) {
        return 3000;
      }
      return false;
    },
  });
}

export function useRepurposeContents(jobId: number) {
  return useQuery({
    queryKey: ["repurpose-contents", jobId],
    queryFn: async () => {
      const response = await api.get<RepurposeContent[]>(
        `/repurpose/${jobId}/contents`
      );
      return response.data;
    },
    enabled: !!jobId,
  });
}

export function useCreateRepurposeJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: RepurposeJobCreate) => {
      const response = await api.post<RepurposeJob>("/repurpose/", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repurpose-jobs"] });
    },
  });
}

export function useDeleteRepurposeJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/repurpose/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repurpose-jobs"] });
    },
  });
}
