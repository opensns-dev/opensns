"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Template, TemplateIndustry, TemplatePlatform } from "@/types";

interface TemplateFilters {
  industry?: TemplateIndustry;
  platform?: TemplatePlatform;
}

export function useTemplates(filters?: TemplateFilters) {
  return useQuery({
    queryKey: ["templates", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.industry) params.set("industry", filters.industry);
      if (filters?.platform) params.set("platform", filters.platform);
      const query = params.toString();
      const url = query ? `/templates?${query}` : "/templates";
      const response = await api.get<Template[]>(url);
      return response.data;
    },
  });
}

export function useTemplate(id: number) {
  return useQuery({
    queryKey: ["templates", id],
    queryFn: async () => {
      const response = await api.get<Template>(`/templates/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
