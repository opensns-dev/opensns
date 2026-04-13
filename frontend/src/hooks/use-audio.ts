"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { TTSVoicesResponse } from "@/types";

export function useTTSVoices(engine: string | null) {
  return useQuery<TTSVoicesResponse>({
    queryKey: ["tts-voices", engine],
    queryFn: async () => {
      const params = engine ? { engine } : {};
      const { data } = await api.get("/api/audio/tts/voices", { params });
      return data;
    },
    enabled: !!engine,
  });
}
