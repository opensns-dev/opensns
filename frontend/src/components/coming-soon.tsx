"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { api } from "@/lib/api";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function ComingSoon() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedEmail = email.trim();

    if (!EMAIL_REGEX.test(trimmedEmail)) {
      setError("Please enter a valid email address.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      await api.post("/waitlist", { email: trimmedEmail });
      setEmail("");
      setIsSuccess(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-white px-6 text-zinc-900 dark:bg-[#0a0a0a] dark:text-white">
      <div className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center py-24 text-center">
        <Link href="/" className="mb-10 flex items-center gap-3">
          <Image
            src="/logo-icon.svg"
            alt="OpenSNS"
            width={28}
            height={28}
            className="h-7 w-7"
          />
          <span className="text-sm font-medium text-zinc-900 dark:text-white">
            OpenSNS
          </span>
        </Link>

        <h1 className="heading-serif mb-5 text-5xl leading-none sm:text-6xl">
          Coming Soon
        </h1>

        <p className="mb-12 max-w-lg text-base leading-relaxed text-zinc-500 dark:text-zinc-400 sm:text-lg">
          We&apos;re building the open-source AI marketing platform. Join the
          waitlist to get early access.
        </p>

        {isSuccess ? (
          <div className="w-full rounded-md border border-zinc-200 px-6 py-5 text-sm text-zinc-900 dark:border-zinc-800 dark:text-white">
            You&apos;re on the list! We&apos;ll notify you when we launch.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="w-full">
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                aria-label="Email address"
                disabled={isSubmitting}
                className="w-full rounded-md border border-zinc-300 bg-transparent px-4 py-3 text-sm text-zinc-900 outline-none transition-colors placeholder:text-zinc-400 focus:border-zinc-900 dark:border-zinc-700 dark:text-white dark:placeholder:text-zinc-500 dark:focus:border-white"
              />
              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-md bg-zinc-900 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-zinc-950 dark:hover:bg-zinc-200"
              >
                {isSubmitting ? "Joining..." : "Join waitlist"}
              </button>
            </div>

            {error ? (
              <p className="mt-3 text-left text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            ) : null}
          </form>
        )}

        <div className="mt-10 flex flex-col items-center gap-4 text-sm sm:flex-row sm:gap-6">
          <Link
            href="/"
            className="text-zinc-500 transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
          >
            ← Back to homepage
          </Link>
          <Link
            href="https://github.com/opensns-dev/opensns"
            target="_blank"
            className="text-zinc-500 transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
          >
            GitHub
          </Link>
          <Link
            href="/docs/"
            className="text-zinc-500 transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
          >
            Docs
          </Link>
        </div>
      </div>
    </div>
  );
}
