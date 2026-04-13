"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import Script from "next/script";
import { toast } from "sonner";
import { Check, X, Zap, CreditCard, ExternalLink, Image, Video, Plus, BarChart3 } from "lucide-react";
import {
  useBillingOverview,
  usePlans,
  useCreditPacks,
  useLSConfig,
  useLSCheckout,
} from "@/hooks/use-billing";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const TIER_ORDER = ["FREE", "BASIC", "BYOK", "PRO", "ULTRA"] as const;

const TIER_COLORS: Record<string, string> = {
  FREE: "bg-zinc-500",
  BASIC: "bg-blue-500",
  BYOK: "bg-emerald-500",
  PRO: "bg-amber-500",
  ULTRA: "bg-purple-500",
};

declare global {
  interface Window {
    createLemonSqueezy?: () => void;
    LemonSqueezy?: {
      Url: { Open: (url: string) => void };
    };
  }
}

function BillingContent() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const { data: overview, isLoading: overviewLoading, refetch: refetchOverview } = useBillingOverview();
  const { data: plans, isLoading: plansLoading } = usePlans();
  const { data: creditPacks, isLoading: packsLoading } = useCreditPacks();
  const { data: lsConfig, isLoading: lsLoading } = useLSConfig();
  const lsCheckout = useLSCheckout();

  useEffect(() => {
    if (searchParams.get("success") === "true") {
      toast.success("Payment successful!", {
        description: "Your account will be updated shortly.",
      });
      setTimeout(() => refetchOverview(), 3000);
    } else if (searchParams.get("canceled") === "true") {
      toast.info("Checkout canceled", {
        description: "You can upgrade anytime.",
      });
    }
  }, [searchParams, refetchOverview]);

  useEffect(() => {
    if (lsConfig) {
      window.createLemonSqueezy?.();
    }
  }, [lsConfig]);

  const isLoading = overviewLoading || plansLoading || packsLoading || lsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-zinc-500">Loading billing information...</div>
      </div>
    );
  }

  if (!overview || !plans) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-red-500">Failed to load billing information</div>
      </div>
    );
  }

  const { subscription, usage, credit_costs, usage_percentage } = overview;
  const currentTier = subscription.tier;
  const isPaid = currentTier !== "FREE" && currentTier !== "BYOK";
  const totalAvailable = usage.credits_limit + usage.bonus_credits;
  const creditsRemaining = totalAvailable - usage.credits_used;

  const handleUpgrade = (variantId: string | null) => {
    if (!variantId) {
      toast.error("Pricing not configured");
      return;
    }
    if (!user) {
      toast.error("Please log in first");
      return;
    }
    lsCheckout.mutate({
      variantId,
      userId: user.id,
      checkoutType: "subscription",
    });
  };

  const handleTopup = (variantId: string | null, credits: number) => {
    if (!variantId) {
      toast.error("Pricing not configured");
      return;
    }
    if (!user) {
      toast.error("Please log in first");
      return;
    }
    lsCheckout.mutate({
      variantId,
      userId: user.id,
      checkoutType: "credit_topup",
      credits,
    });
  };

  return (
    <>
      <Script
        src="https://app.lemonsqueezy.com/js/lemon.js"
        defer
        onLoad={() => window.createLemonSqueezy?.()}
      />
      <div className="container max-w-6xl py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Billing & Subscription</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Manage your subscription and credits
          </p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  Current Plan
                  <Badge className={TIER_COLORS[currentTier]}>
                    {currentTier}
                  </Badge>
                </CardTitle>
                <CardDescription>
                  {isPaid ? (
                    subscription.cancel_at_period_end ? (
                      <span className="text-amber-600">
                        Cancels at end of billing period
                      </span>
                    ) : (
                      `Renews on ${subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : "N/A"}`
                    )
                  ) : (
                    currentTier === "BYOK"
                      ? "Use your own API keys for unlimited usage"
                      : "Upgrade to get more credits"
                  )}
                </CardDescription>
              </div>
              {isPaid && (
                <Button
                  variant="outline"
                  asChild
                >
                  <a
                    href="https://app.lemonsqueezy.com/my-orders"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <CreditCard className="h-4 w-4 mr-2" />
                    Manage Billing
                  </a>
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-600 dark:text-zinc-400">
                  Credits this month
                </span>
                <span
                  className={
                    usage_percentage >= 100
                      ? "text-red-600 font-medium"
                      : usage_percentage >= 80
                        ? "text-amber-600 font-medium"
                        : ""
                  }
                >
                  {usage.credits_used} / {totalAvailable} ({creditsRemaining} remaining)
                  {usage.bonus_credits > 0 && (
                    <span className="text-green-600 ml-1">
                      (+{usage.bonus_credits} bonus)
                    </span>
                  )}
                </span>
              </div>
              <Progress
                value={usage_percentage}
                className={
                  usage_percentage >= 100
                    ? "[&>div]:bg-red-500"
                    : usage_percentage >= 80
                      ? "[&>div]:bg-amber-500"
                      : ""
                }
              />
            </div>

            <div className="flex gap-6 pt-2 text-sm text-zinc-600 dark:text-zinc-400">
              <div className="flex items-center gap-2">
                <Image className="h-4 w-4" />
                <span>Image: {credit_costs.image} credit</span>
              </div>
              <div className="flex items-center gap-2">
                <Video className="h-4 w-4" />
                <span>Video: {credit_costs.video} credits</span>
              </div>
              <Link href="/settings/billing/analytics" className="ml-auto">
                <Button variant="outline" size="sm">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  View Analytics
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Available Plans</CardTitle>
            <CardDescription>
              Higher tiers = better value per credit
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
              {TIER_ORDER.map((tier) => {
                const plan = plans[tier];
                if (!plan) return null;

                const isCurrent = tier === currentTier;
                const isByok = tier === "BYOK";
                const tierIndex = TIER_ORDER.indexOf(tier);
                const currentIndex = TIER_ORDER.indexOf(currentTier);
                const canUpgrade = tierIndex > currentIndex;
                const pricePerCredit = !isByok && plan.price_monthly > 0 && plan.credits_per_month > 0
                  ? (plan.price_monthly / 100 / plan.credits_per_month).toFixed(3)
                  : isByok
                    ? "No markup on AI usage"
                    : "Free";

                return (
                  <div
                    key={tier}
                    className={`relative rounded-lg border p-4 ${
                      isCurrent
                        ? "border-amber-500 bg-amber-50 dark:bg-amber-950/20"
                        : "border-zinc-200 dark:border-zinc-800"
                    }`}
                  >
                    {isCurrent && (
                      <Badge className="absolute -top-2 left-4 bg-amber-500">
                        Current
                      </Badge>
                    )}
                    <div className="space-y-3">
                      <div>
                        <h3 className="font-semibold text-lg">{plan.name}</h3>
                        <p className="text-2xl font-bold">
                          {plan.price_display}
                        </p>
                      </div>

                      <ul className="space-y-2 text-sm">
                        <li className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-500" />
                          {isByok ? "Unlimited" : `${plan.credits_per_month} credits/mo`}
                        </li>
                        <li className="text-xs text-zinc-500">
                          {pricePerCredit === "Free"
                            ? "Free"
                            : pricePerCredit === "No markup on AI usage"
                              ? pricePerCredit
                              : `$${pricePerCredit}/credit`}
                        </li>
                        {isByok && (
                          <li className="flex items-center gap-2 rounded-md bg-emerald-50 px-2 py-1 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300">
                            <Check className="h-4 w-4 text-emerald-500" />
                            <span className="font-medium">Bring Your Own API Keys</span>
                          </li>
                        )}
                        <li className="flex items-center gap-2">
                          {plan.api_access ? (
                            <>
                              <Check className="h-4 w-4 text-green-500" />
                              API Access
                            </>
                          ) : (
                            <>
                              <X className="h-4 w-4 text-zinc-400" />
                              <span className="text-zinc-400">No API</span>
                            </>
                          )}
                        </li>
                      </ul>

                      {canUpgrade && plan.variant_id && (
                        <Button
                          className="w-full"
                          onClick={() => handleUpgrade(plan.variant_id)}
                          disabled={lsCheckout.isPending}
                        >
                          <Zap className="h-4 w-4 mr-2" />
                          {lsCheckout.isPending ? "Loading..." : "Upgrade"}
                        </Button>
                      )}
                      {canUpgrade && !plan.variant_id && tier !== "FREE" && (
                        <Button className="w-full" disabled>
                          Coming Soon
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {creditPacks && Object.keys(creditPacks).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Buy More Credits
              </CardTitle>
              <CardDescription>
                Need more credits this month? Top up instantly.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(creditPacks).map(([packId, pack]) => (
                  <div
                    key={packId}
                    className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-4 space-y-3"
                  >
                    <div>
                      <h3 className="font-semibold text-lg">{pack.credits} Credits</h3>
                      <p className="text-2xl font-bold text-green-600">
                        {pack.price_display}
                      </p>
                      <p className="text-xs text-zinc-500">
                        ${(pack.price_cents / 100 / pack.credits).toFixed(3)}/credit
                      </p>
                    </div>
                    {pack.variant_id ? (
                      <Button
                        className="w-full"
                        variant="outline"
                        onClick={() => handleTopup(pack.variant_id, pack.credits)}
                        disabled={lsCheckout.isPending}
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        {lsCheckout.isPending ? "Loading..." : "Buy Now"}
                      </Button>
                    ) : (
                      <Button className="w-full" variant="outline" disabled>
                        Coming Soon
                      </Button>
                    )}
                  </div>
                ))}
              </div>
              <p className="text-xs text-zinc-500 mt-4">
                Bonus credits never expire and carry over between billing periods.
              </p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Self-Hosted</CardTitle>
            <CardDescription>
              OpenSNS is open-source. Self-host for unlimited usage.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">
              Run OpenSNS on your own infrastructure with no credit limits. You
              only pay for the underlying AI APIs (OpenAI, Fal.ai, etc.).
            </p>
            <Button variant="outline" asChild>
              <a
                href="https://github.com/opensns-dev/opensns"
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View on GitHub
              </a>
            </Button>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-zinc-500">Loading billing information...</div>
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <BillingContent />
    </Suspense>
  );
}
