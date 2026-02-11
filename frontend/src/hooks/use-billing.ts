import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  paddle_price_id: string | null;
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
  paddle_price_id: string | null;
}

export type CreditPacksResponse = Record<string, CreditPackInfo>;

export interface PaddleConfig {
  environment: "sandbox" | "production";
  customer_email: string;
}

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

export function useCreditPacks() {
  return useQuery<CreditPacksResponse>({
    queryKey: ["billing", "credit-packs"],
    queryFn: async () => {
      const { data } = await api.get("/billing/credit-packs");
      return data;
    },
  });
}

export function usePaddleConfig() {
  return useQuery<PaddleConfig>({
    queryKey: ["billing", "paddle-config"],
    queryFn: async () => {
      const { data } = await api.get("/billing/paddle-config");
      return data;
    },
    retry: false,
    meta: { suppressError: true },
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

declare global {
  interface Window {
    Paddle?: {
      Environment: {
        set: (env: "sandbox" | "production") => void;
      };
      Checkout: {
        open: (options: {
          items: Array<{ priceId: string; quantity: number }>;
          customer?: { email: string };
          customData?: Record<string, string>;
          settings?: {
            successUrl?: string;
            displayMode?: "overlay" | "inline";
          };
        }) => void;
      };
      Initialized: boolean;
      Setup: (options: { token: string }) => void;
    };
  }
}

export function usePaddleCheckout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      priceId,
      email,
      userId,
      type = "subscription",
      credits,
    }: {
      priceId: string;
      email: string;
      userId: number;
      type?: "subscription" | "credit_topup";
      credits?: number;
    }) => {
      if (!window.Paddle) {
        throw new Error("Paddle not loaded");
      }

      const customData: Record<string, string> = {
        user_id: String(userId),
        type,
      };

      if (credits) {
        customData.credits = String(credits);
      }

      window.Paddle.Checkout.open({
        items: [{ priceId, quantity: 1 }],
        customer: { email },
        customData,
        settings: {
          successUrl: `${window.location.origin}/settings/billing?success=true`,
          displayMode: "overlay",
        },
      });
    },
    onSuccess: () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["billing"] });
      }, 2000);
    },
  });
}
