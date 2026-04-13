"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { PublicNav } from "@/components/layout/public-nav";
import { PublicFooter } from "@/components/layout/public-footer";
import { GL } from "@/components/gl";

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard/");
    }
  }, [isLoading, isAuthenticated, router]);

  const handleCopy = () => {
    navigator.clipboard.writeText("curl -fsSL https://raw.githubusercontent.com/opensns-dev/opensns/main/install.sh | bash");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white dark:bg-[#0a0a0a]">
        <div className="text-zinc-400 dark:text-zinc-500 text-sm">
          Loading OpenSNS...
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-white dark:bg-[#0a0a0a] text-zinc-900 dark:text-white">
      <PublicNav />

      <section className="relative min-h-screen flex flex-col justify-center px-6 overflow-hidden bg-white dark:bg-[#0a0a0a] text-zinc-900 dark:text-white">
        <div className="absolute inset-0 z-0">
          <GL />
        </div>
        <div className="max-w-6xl mx-auto relative z-10 pt-16">
          <h1 className="heading-serif text-5xl sm:text-6xl lg:text-7xl xl:text-8xl leading-[1.1] mb-8">
            Open-source AI agents
            <br />
            for marketing creatives
          </h1>

          <p className="text-lg sm:text-xl text-zinc-500 dark:text-zinc-400 max-w-2xl mb-10 leading-relaxed">
            Enter a product URL, and AI agents research, strategize,
            <br className="hidden sm:block" />
            and generate ad creatives across all platforms.
          </p>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Link
              href="/register/"
              className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 text-white dark:bg-white dark:text-zinc-950 rounded-md text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
            >
              Get started
            </Link>
            <Link
              href="https://github.com/opensns-dev/opensns"
              target="_blank"
              className="inline-flex items-center gap-2 px-6 py-3 border border-zinc-300 dark:border-zinc-700 rounded-md text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white hover:border-zinc-400 dark:hover:border-zinc-500 transition-colors"
            >
              GitHub
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <section className="py-24 px-6 border-t border-zinc-200 dark:border-zinc-800/50">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start lg:max-w-4xl mx-auto">
            <div>
              <span className="inline-block border border-zinc-300 dark:border-zinc-700 text-zinc-500 dark:text-zinc-400 text-xs px-3 py-1 rounded-full mb-6">
                Quickstart
              </span>
              <h2 className="heading-serif text-4xl sm:text-5xl mb-6">
                Get started in minutes
              </h2>
              <p className="text-zinc-500 dark:text-zinc-400 mb-8 leading-relaxed">
                Deploy OpenSNS with a single command. Self-host your own AI marketing platform with full control over your data.
              </p>
              <div className="flex flex-wrap items-center gap-4">
                <Link
                  href="https://github.com/opensns-dev/opensns"
                  target="_blank"
                  className="text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
                >
                  Star on GitHub →
                </Link>
                <Link
                  href="https://opensns-dev.github.io/opensns/"
                  target="_blank"
                  className="text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
                >
                  Read docs →
                </Link>
              </div>
            </div>

            <div className="bg-zinc-100 dark:bg-[#111] rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <div className="p-4 font-mono text-sm">
                <div className="flex items-center justify-between">
                  <code className="text-zinc-700 dark:text-zinc-300">
                    <span className="text-zinc-400 dark:text-zinc-500">$</span> curl -fsSL https://raw.githubusercontent.com/opensns-dev/opensns/main/install.sh | bash
                  </code>
                  <button
                    onClick={handleCopy}
                    className="text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors"
                    aria-label="Copy command"
                  >
                    {copied ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 px-6 border-t border-zinc-200 dark:border-zinc-800/50">
        <div className="max-w-6xl mx-auto">
          <span className="inline-block border border-zinc-300 dark:border-zinc-700 text-zinc-500 dark:text-zinc-400 text-xs px-3 py-1 rounded-full mb-6">
            Features
          </span>
          <h2 className="heading-serif text-4xl sm:text-5xl mb-16 text-zinc-900 dark:text-white">
            Everything you need.
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-zinc-200 dark:bg-zinc-800/50">
            {[
              { title: "Product Analysis", desc: "AI scrapes and analyzes product pages to understand features, benefits, and positioning." },
              { title: "Competitor Research", desc: "Automatic competitor analysis and market positioning strategy." },
              { title: "Multi-Angle Strategy", desc: "Generate multiple marketing angles for A/B testing." },
              { title: "AI Image Generation", desc: "Create stunning product images with Fal.ai or ComfyUI." },
              { title: "Video & UGC", desc: "Transform images into videos with AI avatars and voice." },
              { title: "Multi-Platform Export", desc: "Automatic resizing for Instagram, Facebook, Google Ads, Naver." },
            ].map((feature, i) => (
              <div
                key={i}
                className="bg-white dark:bg-[#0a0a0a] p-10 group"
              >
                <span className="heading-serif text-4xl sm:text-5xl text-zinc-200 dark:text-zinc-800 block mb-6">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="text-zinc-900 dark:text-white font-medium text-lg mb-2">
                  {feature.title}
                </h3>
                <p className="text-zinc-500 text-sm leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-24 px-6 border-t border-zinc-200 dark:border-zinc-800/50">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="heading-serif text-4xl sm:text-5xl mb-6 text-zinc-900 dark:text-white">
            Ready to start?
          </h2>
          <p className="text-zinc-500 dark:text-zinc-400 mb-8 max-w-xl mx-auto">
            Join the open-source community and start generating marketing creatives with AI.
          </p>
          <Link
            href="/register/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 text-white dark:bg-white dark:text-zinc-950 rounded-md text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
          >
            Get started
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
