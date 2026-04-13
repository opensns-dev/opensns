import Link from "next/link";
import {
  Check,
  X,
  ArrowRight,
  Zap,
  Image as ImageIcon,
  Video,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const PLANS = [
  {
    name: "Free",
    tier: "FREE",
    price: "$0",
    period: "forever",
    description: "Get started with AI marketing",
    credits: "50",
    features: [
      { label: "50 credits/month", included: true },
      { label: "1 team member", included: true },
      { label: "All platforms supported", included: true },
      { label: "Competitor research", included: false },
      { label: "API access", included: false },
      { label: "White label", included: false },
      { label: "Priority queue", included: false },
    ],
    highlight: false,
    cta: "Get Started Free",
  },
  {
    name: "Basic",
    tier: "BASIC",
    price: "$9",
    period: "/month",
    description: "For growing businesses",
    credits: "150",
    features: [
      { label: "150 credits/month", included: true },
      { label: "1 team member", included: true },
      { label: "All platforms supported", included: true },
      { label: "Competitor research", included: true },
      { label: "API access", included: false },
      { label: "White label", included: false },
      { label: "Priority queue", included: false },
    ],
    highlight: false,
    cta: "Start Basic",
  },
  {
    name: "BYOK",
    tier: "BYOK",
    price: "$15",
    period: "/month",
    description: "For self-serve teams using their own AI providers",
    credits: "Unlimited",
    features: [
      { label: "Bring Your Own API Keys", included: true },
      { label: "Unlimited generations", included: true },
      { label: "$15/mo platform fee", included: true },
      { label: "3 team members", included: true },
      { label: "All platforms supported", included: true },
      { label: "Competitor research", included: true },
      { label: "White label", included: false },
    ],
    highlight: false,
    cta: "Start BYOK",
  },
  {
    name: "Pro",
    tier: "PRO",
    price: "$29",
    period: "/month",
    description: "For professional marketers",
    credits: "500",
    features: [
      { label: "500 credits/month", included: true },
      { label: "3 team members", included: true },
      { label: "All platforms supported", included: true },
      { label: "Competitor research", included: true },
      { label: "API access", included: true },
      { label: "White label", included: false },
      { label: "Priority queue", included: true },
    ],
    highlight: true,
    cta: "Start Pro",
  },
  {
    name: "Ultra",
    tier: "ULTRA",
    price: "$59",
    period: "/month",
    description: "For power users and fast-moving teams",
    credits: "1,200",
    features: [
      { label: "1,200 credits/month", included: true },
      { label: "20 team members", included: true },
      { label: "All platforms supported", included: true },
      { label: "Competitor research", included: true },
      { label: "API access", included: true },
      { label: "White label", included: true },
      { label: "Priority queue", included: true },
    ],
    highlight: false,
    cta: "Start Ultra",
  },
];

const CREDIT_PACKS = [
  { credits: 50, price: "$4.99", perCredit: "$0.100" },
  { credits: 150, price: "$12.99", perCredit: "$0.087" },
  { credits: 500, price: "$39.99", perCredit: "$0.080" },
];

const CREDIT_COSTS = [
  { icon: ImageIcon, label: "Image generation", cost: "1 credit" },
  { icon: Video, label: "Video generation", cost: "12 credits" },
  { icon: RotateCcw, label: "Content repurpose", cost: "5 credits" },
];

const FAQ = [
  {
    q: "What are credits?",
    a: "Credits are the currency used to generate marketing assets. Each action costs a set number of credits — 1 for images, 12 for videos, and 5 for content repurposing.",
  },
  {
    q: "Can I change plans anytime?",
    a: "Yes. You can upgrade or downgrade your plan at any time. Changes take effect immediately, and your billing is prorated.",
  },
  {
    q: "Do unused credits roll over?",
    a: "Monthly plan credits reset each billing cycle. However, bonus credits from credit packs never expire and carry over between periods.",
  },
  {
    q: "Can I self-host OpenSNS?",
    a: "Absolutely. OpenSNS is 100% open-source under the MIT license. Self-host on your own infrastructure with no credit limits — you only pay for the underlying AI API costs.",
  },
  {
    q: "What payment methods do you accept?",
    a: "We accept all major credit cards and additional payment methods through our payment partner Lemon Squeezy. Lemon Squeezy handles all billing, taxes, and compliance as our Merchant of Record.",
  },
  {
    q: "How do refunds work?",
    a: "We offer refunds within 14 days of purchase for subscriptions. Credit packs are non-refundable once credits have been used. See our Refund Policy for full details.",
  },
];

export default function PricingPage() {
  return (
    <>
      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-zinc-900 dark:text-white tracking-tight mb-4">
          Simple, Transparent Pricing
        </h1>
        <p className="text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
          Start free. Upgrade as you grow. No hidden fees.
        </p>
      </section>

      {/* Plans */}
      <section className="pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.tier}
              className={`relative rounded-2xl border p-6 flex flex-col ${
                plan.highlight
                  ? "border-amber-500 bg-white dark:bg-zinc-900 shadow-xl shadow-amber-500/10 ring-2 ring-amber-500"
                  : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-amber-500 to-orange-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">
                  {plan.name}
                </h3>
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
                  {plan.description}
                </p>
                <div className="mt-4">
                  <span className="text-4xl font-extrabold text-zinc-900 dark:text-white">
                    {plan.price}
                  </span>
                  <span className="text-zinc-500 dark:text-zinc-400 ml-1">
                    {plan.period}
                  </span>
                </div>
                  <p className="text-sm text-zinc-500 mt-1">
                    {plan.credits === "Unlimited"
                      ? "Unlimited credits"
                      : `${plan.credits} credits/month`}
                  </p>
              </div>

              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((feature) => (
                  <li
                    key={feature.label}
                    className="flex items-center gap-2 text-sm"
                  >
                    {feature.included ? (
                      <Check className="h-4 w-4 text-green-500 shrink-0" />
                    ) : (
                      <X className="h-4 w-4 text-zinc-300 dark:text-zinc-600 shrink-0" />
                    )}
                    <span
                      className={
                        feature.included
                          ? "text-zinc-700 dark:text-zinc-300"
                          : "text-zinc-400 dark:text-zinc-600"
                      }
                    >
                      {feature.label}
                    </span>
                  </li>
                ))}
              </ul>

              <Link href="/register/">
                <Button
                  className={`w-full ${
                    plan.highlight
                      ? "bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white border-0"
                      : ""
                  }`}
                  variant={plan.highlight ? "default" : "outline"}
                >
                  {plan.cta}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Credit Costs */}
      <section className="pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-white text-center mb-8">
            Credit Usage
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {CREDIT_COSTS.map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-3 p-4 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800"
              >
                <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <item.icon className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-white">
                    {item.label}
                  </p>
                  <p className="text-sm text-zinc-500">{item.cost}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Credit Packs */}
      <section className="pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-white text-center mb-2">
            Need More Credits?
          </h2>
          <p className="text-center text-zinc-500 dark:text-zinc-400 mb-8">
            Buy credit packs anytime. Bonus credits never expire.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {CREDIT_PACKS.map((pack) => (
              <div
                key={pack.credits}
                className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-center"
              >
                <p className="text-3xl font-bold text-zinc-900 dark:text-white">
                  {pack.credits}
                </p>
                <p className="text-sm text-zinc-500 mb-2">credits</p>
                <p className="text-2xl font-bold text-green-600">
                  {pack.price}
                </p>
                <p className="text-xs text-zinc-400 mt-1">
                  {pack.perCredit}/credit
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-white text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {FAQ.map((item) => (
              <div
                key={item.q}
                className="p-6 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800"
              >
                <h3 className="font-semibold text-zinc-900 dark:text-white mb-2">
                  {item.q}
                </h3>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                  {item.a}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="rounded-2xl bg-gradient-to-r from-amber-500 to-orange-600 p-12">
            <Zap className="w-10 h-10 text-white/80 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">
              Ready to Get Started?
            </h2>
            <p className="text-white/80 mb-6">
              Create your free account and generate your first ad creative in
              minutes.
            </p>
            <Link href="/register/">
              <Button
                size="lg"
                className="bg-white text-amber-600 hover:bg-zinc-100 h-12 px-8 font-semibold"
              >
                Start Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
