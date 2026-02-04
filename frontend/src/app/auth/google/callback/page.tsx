"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function GoogleCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const savedState = sessionStorage.getItem("oauth_state");

    if (!code) {
      setError("No authorization code received from Google");
      return;
    }

    if (!state || state !== savedState) {
      setError("Invalid state parameter. Please try again.");
      sessionStorage.removeItem("oauth_state");
      return;
    }

    sessionStorage.removeItem("oauth_state");

    const handleCallback = async () => {
      try {
        await api.post(
          `/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
        );
        router.push("/dashboard");
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Google login failed. Please try again."
        );
      }
    };

    handleCallback();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <div className="rounded-full bg-red-100 p-3 dark:bg-red-900/20">
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
            </div>
            <CardTitle>Login failed</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <div className="p-6 pt-0 flex justify-center">
            <Link href="/login">
              <Button>Back to login</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
          </div>
          <CardTitle>Completing login...</CardTitle>
          <CardDescription>Please wait while we sign you in</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
