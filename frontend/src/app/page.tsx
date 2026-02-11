"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { 
  Sparkles, 
  Zap, 
  Target, 
  ImageIcon, 
  Video, 
  BarChart3, 
  ArrowRight,
  Check,
  Globe,
  Layers
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard/");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="animate-pulse text-zinc-500 font-medium">
          Loading OpenSNS...
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-lg border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <Image 
                src="/logo-icon.svg" 
                alt="OpenSNS" 
                width={32} 
                height={32}
                className="w-8 h-8"
              />
              <span className="text-xl font-bold text-zinc-900 dark:text-white">OpenSNS</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/pricing/" className="text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
                Pricing
              </Link>
              <Link href="https://opensns-dev.github.io/opensns/" target="_blank" className="text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
                Docs
              </Link>
              <Link href="/login/">
                <Button variant="ghost" size="sm">Sign In</Button>
              </Link>
              <Link href="/register/">
                <Button size="sm" className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white border-0">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-amber-50/50 to-transparent dark:from-amber-950/20 dark:to-transparent" />
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-amber-400/20 rounded-full blur-3xl" />
        <div className="absolute top-40 right-1/4 w-96 h-96 bg-orange-400/20 rounded-full blur-3xl" />
        
        <div className="relative max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-sm font-medium mb-8">
            <Sparkles className="w-4 h-4" />
            Open Source AI Marketing Platform
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-zinc-900 dark:text-white tracking-tight mb-6">
            AI-Powered Ad Creatives
            <span className="block bg-gradient-to-r from-amber-500 to-orange-600 bg-clip-text text-transparent">
              in Seconds
            </span>
          </h1>
          
          <p className="text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto mb-10">
            Transform any product URL into complete marketing campaigns. OpenSNS automates
            research, strategy, copywriting, and creative production across all major ad platforms.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register/">
              <Button size="lg" className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white border-0 h-14 px-8 text-lg font-semibold shadow-lg shadow-amber-500/25">
                Start Creating Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="https://opensns-dev.github.io/opensns/" target="_blank">
              <Button size="lg" variant="outline" className="h-14 px-8 text-lg font-semibold">
                View Documentation
              </Button>
            </Link>
          </div>
          
          <div className="flex items-center justify-center gap-8 mt-12 text-sm text-zinc-500 dark:text-zinc-500">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-500" />
              No credit card required
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-500" />
              Open source
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-500" />
              Self-hostable
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-white dark:bg-zinc-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-zinc-900 dark:text-white mb-4">
              Everything You Need for Marketing Success
            </h2>
            <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
              Our AI agents work together to deliver professional-grade marketing assets
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Target,
                title: "Product Analysis",
                description: "AI scrapes and analyzes your product page to understand features, benefits, and unique selling points.",
                color: "from-blue-500 to-cyan-500"
              },
              {
                icon: BarChart3,
                title: "Competitor Research",
                description: "Automatic competitor analysis and market positioning to differentiate your marketing approach.",
                color: "from-purple-500 to-pink-500"
              },
              {
                icon: Layers,
                title: "Multi-Angle Strategy",
                description: "Generate multiple marketing angles for A/B testing - value, emotion, urgency, and more.",
                color: "from-amber-500 to-orange-500"
              },
              {
                icon: ImageIcon,
                title: "AI Image Generation",
                description: "Create stunning product images with AI. Supports Fal.ai, Flux, and self-hosted ComfyUI.",
                color: "from-green-500 to-emerald-500"
              },
              {
                icon: Video,
                title: "Video Generation",
                description: "Transform static images into engaging video ads for TikTok, Reels, and Stories.",
                color: "from-red-500 to-rose-500"
              },
              {
                icon: Globe,
                title: "Multi-Platform Export",
                description: "Automatic resizing for Instagram, Facebook, Google Ads, Naver GFA, and more.",
                color: "from-indigo-500 to-violet-500"
              }
            ].map((feature, i) => (
              <div 
                key={i}
                className="group relative p-8 rounded-2xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700 hover:border-amber-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-amber-500/5"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-zinc-900 dark:text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-zinc-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-lg text-zinc-600 dark:text-zinc-400">
              From product URL to ad creatives in three simple steps
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Enter Your Product URL",
                description: "Paste any product page URL. Our AI will automatically extract all relevant information."
              },
              {
                step: "02",
                title: "AI Analyzes & Strategizes",
                description: "Multiple AI agents collaborate to research, strategize, and plan your marketing campaign."
              },
              {
                step: "03",
                title: "Get Your Creatives",
                description: "Download ready-to-use ad copies, images, and videos optimized for each platform."
              }
            ].map((item, i) => (
              <div key={i} className="relative">
                <div className="text-7xl font-black text-amber-500/10 dark:text-amber-500/5 absolute -top-4 -left-2">
                  {item.step}
                </div>
                <div className="relative pt-8">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-bold mb-4">
                    {i + 1}
                  </div>
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-white mb-3">
                    {item.title}
                  </h3>
                  <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="relative rounded-3xl bg-gradient-to-r from-amber-500 to-orange-600 p-12 text-center overflow-hidden">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRjMC0yLjIgMS44LTQgNC00czQgMS44IDQgNC0xLjggNC00IDQtNC0xLjgtNC00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
            
            <div className="relative">
              <Zap className="w-12 h-12 text-white/80 mx-auto mb-6" />
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Ready to Transform Your Marketing?
              </h2>
              <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
                Join thousands of marketers using AI to create better ads faster. 
                Start free, no credit card required.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/register/">
                  <Button size="lg" className="bg-white text-amber-600 hover:bg-zinc-100 h-14 px-8 text-lg font-semibold">
                    Get Started Free
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
                <Link href="https://github.com/opensns-dev/opensns" target="_blank">
                  <Button size="lg" variant="outline" className="border-white/30 text-white hover:bg-white/10 h-14 px-8 text-lg font-semibold">
                    View on GitHub
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <Image src="/logo-icon.svg" alt="OpenSNS" width={32} height={32} className="w-8 h-8" />
              <span className="text-lg font-bold text-zinc-900 dark:text-white">OpenSNS</span>
            </div>
            <div className="flex items-center gap-8 text-sm text-zinc-600 dark:text-zinc-400">
              <Link href="/pricing/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">
                Pricing
              </Link>
              <Link href="https://opensns-dev.github.io/opensns/" target="_blank" className="hover:text-zinc-900 dark:hover:text-white transition-colors">
                Documentation
              </Link>
              <Link href="https://github.com/opensns-dev/opensns" target="_blank" className="hover:text-zinc-900 dark:hover:text-white transition-colors">
                GitHub
              </Link>
              <Link href="/terms/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">
                Terms
              </Link>
              <Link href="/privacy/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">
                Privacy
              </Link>
              <Link href="/refund/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">
                Refund Policy
              </Link>
              <Link href="/contact/" className="hover:text-zinc-900 dark:hover:text-white transition-colors">
                Contact
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
