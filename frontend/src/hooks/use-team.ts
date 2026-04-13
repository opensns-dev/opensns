"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { TeamMember, TeamMemberCreate, TeamMemberUpdate } from "@/types";

export function useTeamMembers() {
  return useQuery({
    queryKey: ["team"],
    queryFn: async () => {
      const response = await api.get<TeamMember[]>("/team");
      return response.data;
    },
  });
}

export function useInviteMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TeamMemberCreate) => {
      const response = await api.post<TeamMember>("/team/invite", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
    },
  });
}

export function useUpdateMemberRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      memberId,
      data,
    }: {
      memberId: number;
      data: TeamMemberUpdate;
    }) => {
      const response = await api.put<TeamMember>(`/team/${memberId}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
    },
  });
}

export function useRemoveMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (memberId: number) => {
      await api.delete(`/team/${memberId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team"] });
    },
  });
}
