"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CalendarView,
  ScheduledPost,
  ScheduledPostCreate,
  ScheduledPostUpdate,
  ScheduleStatus,
} from "@/types";

interface ScheduledPostFilters {
  status?: ScheduleStatus;
  platform?: string;
  from_date?: string;
  to_date?: string;
}

export function useScheduledPosts(filters?: ScheduledPostFilters) {
  return useQuery({
    queryKey: ["scheduled-posts", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.platform) params.set("platform", filters.platform);
      if (filters?.from_date) params.set("from_date", filters.from_date);
      if (filters?.to_date) params.set("to_date", filters.to_date);
      const query = params.toString();
      const response = await api.get<ScheduledPost[]>(
        `/scheduling${query ? `?${query}` : ""}`
      );
      return response.data;
    },
  });
}

export function useCalendarView(month: number, year: number) {
  return useQuery({
    queryKey: ["calendar", month, year],
    queryFn: async () => {
      const response = await api.get<CalendarView>(
        `/scheduling/calendar?month=${month}&year=${year}`
      );
      return response.data;
    },
    enabled: month >= 1 && month <= 12 && year >= 2000,
  });
}

export function useCreateScheduledPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ScheduledPostCreate) => {
      const response = await api.post<ScheduledPost>("/scheduling", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-posts"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
  });
}

export function useUpdateScheduledPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      postId,
      data,
    }: {
      postId: number;
      data: ScheduledPostUpdate;
    }) => {
      const response = await api.put<ScheduledPost>(
        `/scheduling/${postId}`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-posts"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
  });
}

export function useCancelScheduledPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (postId: number) => {
      await api.delete(`/scheduling/${postId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-posts"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
  });
}

export function useReschedulePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      postId,
      scheduled_at,
    }: {
      postId: number;
      scheduled_at: string;
    }) => {
      const response = await api.post<ScheduledPost>(
        `/scheduling/${postId}/reschedule`,
        { scheduled_at }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-posts"] });
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
  });
}
