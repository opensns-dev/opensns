"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useOnboarding } from "@/hooks/use-onboarding";

export default function Home() {
  const router = useRouter();
  const { needsOnboarding, isLoading } = useOnboarding();

  useEffect(() => {
    if (!isLoading) {
      if (needsOnboarding) {
        router.push("/onboarding");
      } else {
        router.push("/dashboard");
      }
    }
  }, [isLoading, needsOnboarding, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <div className="animate-pulse text-zinc-500 font-medium">
        Loading OpenSNS...
      </div>
    </div>
  );
}
