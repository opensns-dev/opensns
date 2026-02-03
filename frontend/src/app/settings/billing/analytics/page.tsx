"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Image, Video, Zap, TrendingUp } from "lucide-react";
import { useUsageAnalytics } from "@/hooks/use-billing";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const PERIOD_OPTIONS = [
  { value: 7, label: "7 days" },
  { value: 30, label: "30 days" },
  { value: 90, label: "90 days" },
];

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const { data: analytics, isLoading } = useUsageAnalytics(days);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-zinc-500">Loading analytics...</div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-red-500">Failed to load analytics</div>
      </div>
    );
  }

  const maxCredits = Math.max(...analytics.daily.map((d) => d.credits), 1);

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/settings/billing">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Usage Analytics</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Track your credit usage over time
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        {PERIOD_OPTIONS.map((option) => (
          <Button
            key={option.value}
            variant={days === option.value ? "default" : "outline"}
            size="sm"
            onClick={() => setDays(option.value)}
          >
            {option.label}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Period Total</CardDescription>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500" />
              {analytics.total_credits} credits
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Images Generated</CardDescription>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Image className="h-5 w-5 text-blue-500" />
              {analytics.by_type.image} credits
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Videos Generated</CardDescription>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Video className="h-5 w-5 text-purple-500" />
              {analytics.by_type.video} credits
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Daily Usage
          </CardTitle>
          <CardDescription>Credits used per day</CardDescription>
        </CardHeader>
        <CardContent>
          {analytics.daily.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              No usage data for this period
            </div>
          ) : (
            <div className="flex items-end gap-1 h-48">
              {analytics.daily.map((day) => (
                <div
                  key={day.date}
                  className="flex-1 flex flex-col items-center gap-1"
                >
                  <div
                    className="w-full bg-amber-500 rounded-t transition-all hover:bg-amber-600"
                    style={{
                      height: `${(day.credits / maxCredits) * 100}%`,
                      minHeight: day.credits > 0 ? "4px" : "0",
                    }}
                    title={`${day.date}: ${day.credits} credits`}
                  />
                </div>
              ))}
            </div>
          )}
          {analytics.daily.length > 0 && (
            <div className="flex justify-between text-xs text-zinc-500 mt-2">
              <span>{analytics.daily[0]?.date}</span>
              <span>{analytics.daily[analytics.daily.length - 1]?.date}</span>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lifetime Stats</CardTitle>
          <CardDescription>All-time usage since account creation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold">
                {analytics.lifetime.total_credits}
              </div>
              <div className="text-sm text-zinc-500">Total Credits</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-500">
                {analytics.lifetime.total_images}
              </div>
              <div className="text-sm text-zinc-500">Images</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-500">
                {analytics.lifetime.total_videos}
              </div>
              <div className="text-sm text-zinc-500">Videos</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
