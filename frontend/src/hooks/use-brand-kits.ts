"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BrandKit, BrandKitCreate, BrandKitUpdate } from "@/types";

export function useBrandKits() {
  return useQuery({
    queryKey: ["brand-kits"],
    queryFn: async () => {
      const response = await api.get<BrandKit[]>("/brand-kits");
      return response.data;
    },
  });
}

export function useBrandKit(id: number) {
  return useQuery({
    queryKey: ["brand-kits", id],
    queryFn: async () => {
      const response = await api.get<BrandKit>(`/brand-kits/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateBrandKit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: BrandKitCreate) => {
      const response = await api.post<BrandKit>("/brand-kits", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand-kits"] });
    },
  });
}

export function useUpdateBrandKit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: BrandKitUpdate }) => {
      const response = await api.put<BrandKit>(`/brand-kits/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand-kits"] });
    },
  });
}

export function useDeleteBrandKit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/brand-kits/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand-kits"] });
    },
  });
}
