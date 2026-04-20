"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  ProviderRegistryResponse,
  ProviderCredentialsResponse,
  ProviderCredentialCreate,
  ProviderCredentialTestResult,
  ProviderRegistryItem,
  ProviderCredentialSummary,
} from "@/types";

export function useProviderRegistry() {
  return useQuery({
    queryKey: ["providers", "registry"],
    queryFn: async () => {
      const response = await api.get<ProviderRegistryResponse>("/providers/registry");
      return response.data;
    },
  });
}

export function useProviderCredentials() {
  return useQuery({
    queryKey: ["providers", "credentials"],
    queryFn: async () => {
      const response = await api.get<ProviderCredentialsResponse>("/providers/credentials");
      return response.data;
    },
  });
}

export function useSaveProviderCredential() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ProviderCredentialCreate) => {
      const response = await api.post<ProviderCredentialSummary>("/providers/credentials", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers", "credentials"] });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
}

export function useRemoveProviderCredential() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (providerName: string) => {
      await api.delete(`/providers/credentials/${providerName}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers", "credentials"] });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
}

export function useTestProviderCredential() {
  return useMutation({
    mutationFn: async (providerName: string) => {
      const response = await api.post<ProviderCredentialTestResult>(
        `/providers/credentials/${providerName}/test`
      );
      return response.data;
    },
  });
}

export function useTestProviderCompatibility() {
  return useMutation({
    mutationFn: async (providerName: string) => {
      const response = await api.post<ProviderCredentialTestResult>(
        `/providers/credentials/${providerName}/test-compatibility`
      );
      return response.data;
    },
  });
}

// Helper hook to group providers by type with their credential status
export function useGroupedProviders() {
  const { data: registryData, isLoading: registryLoading } = useProviderRegistry();
  const { data: credentialsData, isLoading: credentialsLoading } = useProviderCredentials();

  const isLoading = registryLoading || credentialsLoading;

  const grouped = {
    llm: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
    image: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
    video: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
    ugc: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
    scraper: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
    tts: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
    stt: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
    bgm: [] as Array<{ provider: ProviderRegistryItem; credential?: ProviderCredentialSummary }>,
  };

  if (registryData?.providers && credentialsData?.credentials) {
    for (const provider of registryData.providers) {
      const credential = credentialsData.credentials.find(
        (c) => c.provider_name === provider.name
      );
      grouped[provider.provider_type].push({ provider, credential });
    }
  }

  return {
    grouped,
    isLoading,
    registry: registryData?.providers ?? [],
    credentials: credentialsData?.credentials ?? [],
  };
}
