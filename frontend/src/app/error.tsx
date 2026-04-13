"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const isDev = process.env.NODE_ENV === "development";

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center p-6">
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
          <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
        </div>
        <div className="flex flex-col items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Something went wrong
          </h1>
          <p className="max-w-md text-zinc-600 dark:text-zinc-400">
            An unexpected error occurred. Please try again or contact support if the problem persists.
          </p>
        </div>
        {isDev && (
          <div className="max-w-md rounded-lg border border-red-200 bg-red-50 p-4 text-left dark:border-red-800 dark:bg-red-900/20">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">
              Error: {error.message}
            </p>
            {error.digest && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                Digest: {error.digest}
              </p>
            )}
          </div>
        )}
        <div className="flex items-center gap-3">
          <Button
            onClick={reset}
            className="bg-amber-500 hover:bg-orange-600 text-white dark:bg-amber-500 dark:hover:bg-orange-600"
          >
            Try Again
          </Button>
          <Button
            variant="outline"
            asChild
            className="border-zinc-300 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            <Link href="/">Go Home</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
