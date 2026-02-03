"use client";

import { useSearchParams } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Check, X, Zap, CreditCard, ExternalLink, Image, Video, Plus, BarChart3 } from "lucide-react";
import {
  useBillingOverview,
  usePlans,
  useCreditPacks,
  useCreateCheckout,
  useCreatePortal,
  useCreateTopup,
} from "@/hooks/use-billing";
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

const TIER_ORDER = ["FREE", "BASIC", "PRO", "ULTRA"] as const;

const TIER_COLORS: Record<string, string> = {
  FREE: "bg-zinc-500",
  BASIC: "bg-blue-500",
  PRO: "bg-amber-500",
  ULTRA: "bg-purple-500",
};

export default function BillingPage() {
  const searchParams = useSearchParams();
  const { data: overview, isLoading: overviewLoading } = useBillingOverview();
  const { data: plans, isLoading: plansLoading } = usePlans();
  const { data: creditPacks, isLoading: packsLoading } = useCreditPacks();
  const createCheckout = useCreateCheckout();
  const createPortal = useCreatePortal();
  const createTopup = useCreateTopup();

  useEffect(() => {
    if (searchParams.get("success") === "true") {
      toast.success("Subscription activated!", {
        description: "Thank you for upgrading. Your new credits are now active.",
      });
    } else if (searchParams.get("canceled") === "true") {
      toast.info("Checkout canceled", {
        description: "You can upgrade anytime.",
      });
    } else if (searchParams.get("topup") === "success") {
      toast.success("Credits added!", {
        description: "Your bonus credits are now available.",
      });
    } else if (searchParams.get("topup") === "canceled") {
      toast.info("Top-up canceled", {
        description: "You can buy credits anytime.",
      });
    }
  }, [searchParams]);

  const isLoading = overviewLoading || plansLoading || packsLoading;

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
  const isPaid = currentTier !== "FREE";
  const totalAvailable = usage.credits_limit + usage.bonus_credits;
  const creditsRemaining = totalAvailable - usage.credits_used;

  const handleUpgrade = (tier: string) => {
    createCheckout.mutate(tier);
  };

  const handleTopup = (packId: string) => {
    createTopup.mutate(packId);
  };

  const handleManageBilling = () => {
    createPortal.mutate();
  };

  return (
    <div className="container max-w-4xl py-8 space-y-6">
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
                  "Upgrade to get more credits"
                )}
              </CardDescription>
            </div>
            {isPaid && (
              <Button
                variant="outline"
                onClick={handleManageBilling}
                disabled={createPortal.isPending}
              >
                <CreditCard className="h-4 w-4 mr-2" />
                {createPortal.isPending ? "Loading..." : "Manage Billing"}
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {TIER_ORDER.map((tier) => {
              const plan = plans[tier];
              if (!plan) return null;

              const isCurrent = tier === currentTier;
              const tierIndex = TIER_ORDER.indexOf(tier);
              const currentIndex = TIER_ORDER.indexOf(currentTier);
              const canUpgrade = tierIndex > currentIndex;
              const pricePerCredit = plan.price_monthly > 0 
                ? (plan.price_monthly / 100 / plan.credits_per_month).toFixed(3)
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
                        {plan.credits_per_month} credits/mo
                      </li>
                      <li className="text-xs text-zinc-500">
                        {pricePerCredit !== "Free" ? `$${pricePerCredit}/credit` : "Free"}
                      </li>
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

                    {canUpgrade && (
                      <Button
                        className="w-full"
                        onClick={() => handleUpgrade(tier)}
                        disabled={createCheckout.isPending}
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        {createCheckout.isPending ? "Loading..." : "Upgrade"}
                      </Button>
                    )}
                    {isCurrent && tier !== "FREE" && (
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={handleManageBilling}
                        disabled={createPortal.isPending}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Manage
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
                  <Button
                    className="w-full"
                    variant="outline"
                    onClick={() => handleTopup(packId)}
                    disabled={createTopup.isPending}
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    {createTopup.isPending ? "Loading..." : "Buy Now"}
                  </Button>
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
  );
}
