"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ProductPhoto, ProductPhotoCreate } from "@/types";

export function useProductPhotos(refetchInterval?: number | false) {
  return useQuery({
    queryKey: ["product-photos"],
    queryFn: async () => {
      const response = await api.get<ProductPhoto[]>("/product-photos");
      return response.data;
    },
    refetchInterval: refetchInterval ?? false,
  });
}

export function useProductPhoto(id: number) {
  return useQuery({
    queryKey: ["product-photos", id],
    queryFn: async () => {
      const response = await api.get<ProductPhoto>(`/product-photos/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateProductPhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ProductPhotoCreate) => {
      const response = await api.post<ProductPhoto>("/product-photos", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["product-photos"] });
    },
  });
}

export function useDeleteProductPhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/product-photos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["product-photos"] });
    },
  });
}

export function useRetryProductPhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post<ProductPhoto>(
        `/product-photos/${id}/retry`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["product-photos"] });
    },
  });
}
