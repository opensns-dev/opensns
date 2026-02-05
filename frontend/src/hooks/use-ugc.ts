"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  UGCEnginesResponse,
  AvatarsResponse,
  VoicesResponse,
} from "@/types";

export function useUGCEngines() {
  return useQuery({
    queryKey: ["ugc", "engines"],
    queryFn: async () => {
      const response = await api.get<UGCEnginesResponse>("/ugc/engines");
      return response.data;
    },
  });
}

export function useAvatars(engine: string = "heygen") {
  return useQuery({
    queryKey: ["ugc", "avatars", engine],
    queryFn: async () => {
      const response = await api.get<AvatarsResponse>("/ugc/avatars", {
        params: { engine },
      });
      return response.data;
    },
    enabled: !!engine,
  });
}

export function useVoices(engine: string = "heygen") {
  return useQuery({
    queryKey: ["ugc", "voices", engine],
    queryFn: async () => {
      const response = await api.get<VoicesResponse>("/ugc/voices", {
        params: { engine },
      });
      return response.data;
    },
    enabled: !!engine,
  });
}
