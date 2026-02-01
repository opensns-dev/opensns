"use client";

import { useSettings } from "./use-settings";
import { useCampaigns } from "./use-campaigns";

export type OnboardingStep = "api-keys" | "first-campaign" | "complete";

export function useOnboarding() {
  const { data: settings, isLoading: isLoadingSettings } = useSettings();
  const { data: campaigns, isLoading: isLoadingCampaigns } = useCampaigns();

  const isLoading = isLoadingSettings || isLoadingCampaigns;

  if (isLoading) {
    return {
      needsOnboarding: false,
      isLoading: true,
      step: "api-keys" as OnboardingStep,
    };
  }

  const hasApiKey = settings?.has_openai_key || settings?.has_fal_key;
  const hasCampaign = (campaigns?.length ?? 0) > 0;

  let step: OnboardingStep = "api-keys";
  let needsOnboarding = true;

  if (hasApiKey && hasCampaign) {
    step = "complete";
    needsOnboarding = false;
  } else if (hasApiKey) {
    step = "first-campaign";
    needsOnboarding = true;
  }

  return {
    needsOnboarding,
    isLoading: false,
    step,
  };
}
