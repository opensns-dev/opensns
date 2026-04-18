"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { PublicNav } from "@/components/layout/public-nav";
import { PublicFooter } from "@/components/layout/public-footer";
import { GL } from "@/components/gl";

export function LandingContent() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const [copied, setCopied] = useState(false);
  const [isDemoVideoAvailable, setIsDemoVideoAvailable] = useState(true);
  const [isDemoVideoReady, setIsDemoVideoReady] = useState(false);

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
          <div className="max-w-3xl mb-12">
            <span className="inline-block border border-zinc-300 dark:border-zinc-700 text-zinc-500 dark:text-zinc-400 text-xs px-3 py-1 rounded-full mb-6">
              Demo
            </span>
            <h2 className="heading-serif text-4xl sm:text-5xl mb-6 text-zinc-900 dark:text-white">
              See it in action
            </h2>
            <p className="text-zinc-500 dark:text-zinc-400 leading-relaxed">
              Watch how OpenSNS turns a single product URL into a complete set of AI-generated marketing creatives with a workflow designed for speed and clarity.
            </p>
          </div>

          <div className="group bg-zinc-100 dark:bg-[#111] rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-800 transition-shadow duration-300 hover:shadow-lg dark:hover:shadow-2xl">
            <div className="flex items-center gap-3 px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2 shrink-0">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="h-9 rounded-full border border-zinc-200 bg-white/80 text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900/80 dark:text-zinc-400 text-sm px-4 flex items-center justify-center backdrop-blur-sm">
                  <span className="truncate">opensns.app</span>
                </div>
              </div>
            </div>

            <div className="relative aspect-video bg-white dark:bg-[#0a0a0a]">
              {isDemoVideoAvailable && (
                <video
                  className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-300 ${isDemoVideoReady ? "opacity-100" : "opacity-0"}`}
                  controls
                  playsInline
                  preload="metadata"
                  onLoadedData={() => setIsDemoVideoReady(true)}
                  onError={() => {
                    setIsDemoVideoAvailable(false);
                    setIsDemoVideoReady(false);
                  }}
                  poster="/demo-poster.jpg"
                >
                  <source src="/demo.mp4" type="video/mp4" />
                </video>
              )}

              {!isDemoVideoReady && (
                <div className="absolute inset-0 flex items-center justify-center p-6 sm:p-10 bg-gradient-to-br from-zinc-50 via-white to-zinc-100 dark:from-[#0a0a0a] dark:via-[#101010] dark:to-[#161616]">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_45%)] dark:bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.05),transparent_45%)]" />
                  <div className="relative w-full max-w-2xl rounded-[28px] border border-zinc-200/80 dark:border-zinc-800/80 bg-white/70 dark:bg-white/[0.03] backdrop-blur-sm px-6 py-10 sm:px-10 sm:py-14 text-center">
                    <div className="mx-auto mb-6 flex h-18 w-18 items-center justify-center rounded-full border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
                      <div className="ml-1 flex h-14 w-14 items-center justify-center rounded-full bg-zinc-900 text-white dark:bg-white dark:text-zinc-950">
                        <svg
                          className="w-5 h-5"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                          aria-hidden="true"
                        >
                          <path d="M8.75 7.5v9l7-4.5-7-4.5Z" />
                        </svg>
                      </div>
                    </div>
                    <p className="text-xs uppercase tracking-[0.18em] text-zinc-400 dark:text-zinc-500 mb-4">
                      Product walkthrough
                    </p>
                    <h3 className="heading-serif text-3xl sm:text-4xl text-zinc-900 dark:text-white mb-4">
                      Demo video coming soon
                    </h3>
                    <p className="max-w-xl mx-auto text-sm sm:text-base leading-relaxed text-zinc-500 dark:text-zinc-400">
                      A full walkthrough showing URL input to campaign output will be available here shortly.
                    </p>
                  </div>
                </div>
              )}
            </div>
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
