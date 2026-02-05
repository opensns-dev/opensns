"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSettings, useUpdateSettings } from "@/hooks/use-settings";
import { useCreateCampaign } from "@/hooks/use-campaigns";
import { useOnboarding } from "@/hooks/use-onboarding";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Key, Sparkles, Rocket, CheckCircle, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function OnboardingPage() {
  const router = useRouter();
  const { step, isLoading, needsOnboarding } = useOnboarding();
  useSettings(); // Fetch settings in background
  const updateSettings = useUpdateSettings();
  const createCampaign = useCreateCampaign();

  const [currentStep, setCurrentStep] = useState<1 | 2>(1);
  const [openaiKey, setOpenaiKey] = useState("");
  const [falKey, setFalKey] = useState("");
  const [campaignTitle, setCampaignTitle] = useState("");
  const [productUrl, setProductUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && !needsOnboarding) {
      router.push("/dashboard");
    }
  }, [isLoading, needsOnboarding, router]);

  useEffect(() => {
    if (step === "first-campaign") {
      setCurrentStep(2);
    }
  }, [step]);

  const handleApiKeySubmit = async () => {
    if (!openaiKey && !falKey) {
      setCurrentStep(2);
      return;
    }

    setIsSubmitting(true);
    try {
      await updateSettings.mutateAsync({
        openai_api_key: openaiKey || undefined,
        fal_api_key: falKey || undefined,
      });
      setCurrentStep(2);
    } catch (error) {
      console.error("Failed to update settings", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCampaignSubmit = async () => {
    if (!campaignTitle || !productUrl) return;

    setIsSubmitting(true);
    try {
      const campaign = await createCampaign.mutateAsync({
        title: campaignTitle,
        product_url: productUrl,
      });
      router.push(`/campaigns/view?id=${campaign.id}`);
    } catch (error) {
      console.error("Failed to create campaign", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-zinc-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 p-4 dark:bg-zinc-950">
      <div className="mb-8 w-full max-w-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-zinc-500">
            Step {currentStep} of 2
          </span>
          <span className="text-sm font-medium text-zinc-500">
            {currentStep === 1 ? "50%" : "100%"}
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
          <div
            className="h-full bg-amber-500 transition-all duration-500 ease-in-out"
            style={{ width: currentStep === 1 ? "50%" : "100%" }}
          />
        </div>
      </div>

      <div className="w-full max-w-md space-y-8">
        {currentStep === 1 ? (
          <Card className="border-zinc-200 shadow-xl dark:border-zinc-800 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
                <Key className="h-6 w-6 text-amber-600 dark:text-amber-400" />
              </div>
              <CardTitle className="text-2xl font-bold">
                Welcome to OpenSNS!
              </CardTitle>
              <CardDescription className="text-zinc-500">
                Let&apos;s get you set up. To generate AI marketing assets,
                you&apos;ll need to configure at least one API key.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800 bg-white dark:bg-zinc-900/50">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <Label htmlFor="openai" className="font-semibold">
                    OpenAI API Key
                  </Label>
                </div>
                <Input
                  id="openai"
                  placeholder="sk-..."
                  type="password"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="bg-zinc-50 dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800"
                />
              </div>
              <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800 bg-white dark:bg-zinc-900/50">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-2 w-2 rounded-full bg-blue-500" />
                  <Label htmlFor="fal" className="font-semibold">
                    Fal.ai API Key
                  </Label>
                </div>
                <Input
                  id="fal"
                  placeholder="Enter your Fal.ai key"
                  type="password"
                  value={falKey}
                  onChange={(e) => setFalKey(e.target.value)}
                  className="bg-zinc-50 dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800"
                />
              </div>
              <p className="text-xs text-center text-zinc-400">
                Your keys are encrypted and never shared. You can also skip this
                if using local engines.
              </p>
            </CardContent>
            <CardFooter className="flex gap-3">
              <Button
                variant="ghost"
                className="flex-1"
                onClick={() => setCurrentStep(2)}
              >
                Skip for now
              </Button>
              <Button
                className="flex-1 bg-amber-500 hover:bg-amber-600 text-white"
                onClick={handleApiKeySubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Saving..." : "Continue"}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardFooter>
          </Card>
        ) : (
          <Card className="border-zinc-200 shadow-xl dark:border-zinc-800 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
                <Rocket className="h-6 w-6 text-amber-600 dark:text-amber-400" />
              </div>
              <CardTitle className="text-2xl font-bold">
                First Campaign
              </CardTitle>
              <CardDescription className="text-zinc-500">
                Great! Now let&apos;s create your first marketing campaign to
                see the AI in action.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label
                  htmlFor="title"
                  className="text-sm font-semibold uppercase tracking-wider text-zinc-500"
                >
                  Campaign Title
                </Label>
                <Input
                  id="title"
                  placeholder="e.g. Summer Collection Launch"
                  value={campaignTitle}
                  onChange={(e) => setCampaignTitle(e.target.value)}
                  className="h-12 text-lg border-zinc-200 dark:border-zinc-800 focus:ring-amber-500"
                />
              </div>
              <div className="space-y-2">
                <Label
                  htmlFor="url"
                  className="text-sm font-semibold uppercase tracking-wider text-zinc-500"
                >
                  Product URL
                </Label>
                <Input
                  id="url"
                  placeholder="https://yourstore.com/product"
                  value={productUrl}
                  onChange={(e) => setProductUrl(e.target.value)}
                  className="h-12 text-lg border-zinc-200 dark:border-zinc-800 focus:ring-amber-500"
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button
                className="w-full bg-amber-500 hover:bg-amber-600 text-white"
                onClick={handleCampaignSubmit}
                disabled={isSubmitting || !campaignTitle || !productUrl}
              >
                {isSubmitting ? (
                  "Creating..."
                ) : (
                  <>
                    Create Campaign
                    <Sparkles className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        )}

        <div className="flex justify-center gap-8">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "h-8 w-8 rounded-full border-2 flex items-center justify-center text-sm font-bold transition-colors",
                currentStep === 1
                  ? "border-amber-500 text-amber-500"
                  : "border-zinc-300 text-zinc-300 bg-zinc-100 dark:bg-zinc-800 dark:border-zinc-700"
              )}
            >
              {currentStep > 1 ? <CheckCircle className="h-5 w-5 text-amber-500" /> : "1"}
            </div>
            <span
              className={cn(
                "text-sm font-medium transition-colors",
                currentStep === 1 ? "text-amber-500" : "text-zinc-400"
              )}
            >
              API Keys
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "h-8 w-8 rounded-full border-2 flex items-center justify-center text-sm font-bold transition-colors",
                currentStep === 2
                  ? "border-amber-500 text-amber-500"
                  : "border-zinc-300 text-zinc-300 bg-zinc-100 dark:bg-zinc-800 dark:border-zinc-700"
              )}
            >
              2
            </div>
            <span
              className={cn(
                "text-sm font-medium transition-colors",
                currentStep === 2 ? "text-amber-500" : "text-zinc-400"
              )}
            >
              First Campaign
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
