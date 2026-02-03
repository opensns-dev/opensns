import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface SubscriptionInfo {
  tier: "FREE" | "BASIC" | "PRO" | "ULTRA";
  status: "ACTIVE" | "CANCELED" | "PAST_DUE" | "TRIALING";
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  limits: Record<string, number | boolean>;
}

export interface UsageInfo {
  period_start: string;
  credits_used: number;
  credits_limit: number;
  bonus_credits: number;
}

export interface CreditCosts {
  image: number;
  video: number;
}

export interface BillingOverview {
  subscription: SubscriptionInfo;
  usage: UsageInfo;
  credit_costs: CreditCosts;
  usage_percentage: number;
}

export interface PlanInfo {
  name: string;
  price_monthly: number;
  price_display: string;
  credits_per_month: number;
  team_members: number;
  api_access: boolean;
  white_label: boolean;
  competitor_research: boolean;
  priority_queue: boolean;
}

export type PlansResponse = Record<string, PlanInfo>;

export interface CreditPackInfo {
  id: string;
  credits: number;
  price_cents: number;
  price_display: string;
}

export type CreditPacksResponse = Record<string, CreditPackInfo>;

export function useBillingOverview() {
  return useQuery<BillingOverview>({
    queryKey: ["billing", "overview"],
    queryFn: async () => {
      const { data } = await api.get("/billing/overview");
      return data;
    },
  });
}

export function usePlans() {
  return useQuery<PlansResponse>({
    queryKey: ["billing", "plans"],
    queryFn: async () => {
      const { data } = await api.get("/billing/plans");
      return data;
    },
  });
}

export function useCreateCheckout() {
  return useMutation({
    mutationFn: async (tier: string) => {
      const { data } = await api.post(`/billing/checkout?tier=${tier}`);
      return data as { checkout_url: string };
    },
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
  });
}

export function useCreatePortal() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post("/billing/portal");
      return data as { portal_url: string };
    },
    onSuccess: (data) => {
      window.location.href = data.portal_url;
    },
  });
}

export function useCreditPacks() {
  return useQuery<CreditPacksResponse>({
    queryKey: ["billing", "credit-packs"],
    queryFn: async () => {
      const { data } = await api.get("/billing/credit-packs");
      return data;
    },
  });
}

export function useCreateTopup() {
  return useMutation({
    mutationFn: async (packId: string) => {
      const { data } = await api.post(`/billing/topup?pack_id=${packId}`);
      return data as { checkout_url: string };
    },
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
  });
}

export interface UsageAnalytics {
  period_days: number;
  total_credits: number;
  by_type: { image: number; video: number };
  daily: Array<{ date: string; credits: number; image: number; video: number }>;
  lifetime: { total_credits: number; total_images: number; total_videos: number };
}

export function useUsageAnalytics(days: number = 30) {
  return useQuery<UsageAnalytics>({
    queryKey: ["billing", "analytics", days],
    queryFn: async () => {
      const { data } = await api.get(`/billing/analytics?days=${days}`);
      return data;
    },
  });
}
