"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Minus,
  RefreshCw,
  Target,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  usePredictions,
  useSyncPredictions,
  useUpdateActuals,
} from "@/hooks/use-predictions";

function formatRate(value: number | null): string {
  if (value === null) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

function formatDeviation(value: number | null): string {
  if (value === null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(2)}pp`;
}

function DeviationIcon({ value }: { value: number | null }) {
  if (value === null) return <Minus className="h-4 w-4 text-zinc-400" />;
  if (value > 0) return <ArrowUp className="h-4 w-4 text-red-500" />;
  if (value < 0) return <ArrowDown className="h-4 w-4 text-green-500" />;
  return <Minus className="h-4 w-4 text-zinc-400" />;
}

function accuracyColor(score: number | null): string {
  if (score === null) return "text-zinc-400";
  if (score >= 80) return "text-green-600 dark:text-green-400";
  if (score >= 50) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
}

function accuracyBadgeVariant(
  score: number | null
): "default" | "secondary" | "destructive" | "outline" {
  if (score === null) return "outline";
  if (score >= 80) return "default";
  if (score >= 50) return "secondary";
  return "destructive";
}

interface ComparisonRow {
  label: string;
  predicted: number | null;
  actual: number | null;
  deviation: number | null;
}

export default function CampaignPredictionsPage() {
  const params = useParams<{ id: string }>();
  const campaignId = Number(params.id);

  const { data: prediction, isLoading, isError } = usePredictions(campaignId);
  const syncMutation = useSyncPredictions(campaignId);
  const updateActuals = useUpdateActuals(campaignId);

  const [actualsForm, setActualsForm] = useState({
    actual_ctr: "",
    actual_engagement_rate: "",
    actual_conversion_rate: "",
    actual_impressions: "",
    actual_clicks: "",
    actual_conversions: "",
  });

  function handleSync() {
    syncMutation.mutate(undefined, {
      onSuccess: () => toast.success("Predictions synced"),
      onError: () => toast.error("Failed to sync predictions"),
    });
  }

  function handleUpdateActuals() {
    const payload: Record<string, number> = {};
    if (actualsForm.actual_ctr)
      payload.actual_ctr = Number(actualsForm.actual_ctr) / 100;
    if (actualsForm.actual_engagement_rate)
      payload.actual_engagement_rate =
        Number(actualsForm.actual_engagement_rate) / 100;
    if (actualsForm.actual_conversion_rate)
      payload.actual_conversion_rate =
        Number(actualsForm.actual_conversion_rate) / 100;
    if (actualsForm.actual_impressions)
      payload.actual_impressions = Number(actualsForm.actual_impressions);
    if (actualsForm.actual_clicks)
      payload.actual_clicks = Number(actualsForm.actual_clicks);
    if (actualsForm.actual_conversions)
      payload.actual_conversions = Number(actualsForm.actual_conversions);

    if (Object.keys(payload).length === 0) {
      toast.error("Enter at least one value");
      return;
    }

    updateActuals.mutate(payload, {
      onSuccess: () => {
        toast.success("Actuals updated");
        setActualsForm({
          actual_ctr: "",
          actual_engagement_rate: "",
          actual_conversion_rate: "",
          actual_impressions: "",
          actual_clicks: "",
          actual_conversions: "",
        });
      },
      onError: () => toast.error("Failed to update actuals"),
    });
  }

  const rows: ComparisonRow[] = prediction
    ? [
        {
          label: "CTR",
          predicted: prediction.predicted_ctr,
          actual: prediction.actual_ctr,
          deviation: prediction.ctr_deviation,
        },
        {
          label: "Engagement Rate",
          predicted: prediction.predicted_engagement_rate,
          actual: prediction.actual_engagement_rate,
          deviation:
            prediction.predicted_engagement_rate !== null &&
            prediction.actual_engagement_rate !== null
              ? prediction.predicted_engagement_rate -
                prediction.actual_engagement_rate
              : null,
        },
        {
          label: "Conversion Rate",
          predicted: prediction.predicted_conversion_rate,
          actual: prediction.actual_conversion_rate,
          deviation:
            prediction.predicted_conversion_rate !== null &&
            prediction.actual_conversion_rate !== null
              ? prediction.predicted_conversion_rate -
                prediction.actual_conversion_rate
              : null,
        },
      ]
    : [];

  if (isLoading) {
    return (
      <div className="container max-w-6xl py-8 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="container max-w-6xl py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/campaigns/view?id=${campaignId}`}>
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Prediction Accuracy</h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              Compare AI predictions against actual performance
            </p>
          </div>
        </div>
        <Button onClick={handleSync} disabled={syncMutation.isPending}>
          <RefreshCw
            className={`h-4 w-4 mr-2 ${syncMutation.isPending ? "animate-spin" : ""}`}
          />
          {syncMutation.isPending ? "Syncing..." : "Sync Predictions"}
        </Button>
      </div>

      {prediction && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <Target className="h-3 w-3" />
                Accuracy Score
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-2">
                <span
                  className={`text-4xl font-bold ${accuracyColor(prediction.accuracy_score)}`}
                >
                  {prediction.accuracy_score !== null
                    ? prediction.accuracy_score.toFixed(0)
                    : "—"}
                </span>
                <span className="text-zinc-500 mb-1">/100</span>
              </div>
              {prediction.accuracy_score !== null && (
                <Progress
                  value={prediction.accuracy_score}
                  className="mt-3 h-2"
                />
              )}
              <Badge
                variant={accuracyBadgeVariant(prediction.accuracy_score)}
                className="mt-2"
              >
                {prediction.accuracy_score === null
                  ? "No data"
                  : prediction.accuracy_score >= 80
                    ? "High accuracy"
                    : prediction.accuracy_score >= 50
                      ? "Moderate accuracy"
                      : "Low accuracy"}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                CTR Deviation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <DeviationIcon value={prediction.ctr_deviation} />
                <span className="text-2xl font-bold">
                  {formatDeviation(prediction.ctr_deviation)}
                </span>
              </div>
              <p className="text-xs text-zinc-500 mt-1">Predicted minus actual</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Quality Score</CardDescription>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold">
                {prediction.predicted_quality_score !== null
                  ? prediction.predicted_quality_score.toFixed(1)
                  : "—"}
              </span>
              <p className="text-xs text-zinc-500 mt-1">AI-predicted quality</p>
            </CardContent>
          </Card>
        </div>
      )}

      {!prediction && !isError && (
        <Card>
          <CardContent className="py-12 text-center text-zinc-500">
            <Target className="h-12 w-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium">No prediction data yet</p>
            <p className="text-sm mt-1">
              Click &quot;Sync Predictions&quot; to extract predictions from this
              campaign.
            </p>
          </CardContent>
        </Card>
      )}

      {isError && (
        <Card>
          <CardContent className="py-12 text-center text-zinc-500">
            <Target className="h-12 w-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium">No prediction data found</p>
            <p className="text-sm mt-1">
              Click &quot;Sync Predictions&quot; to generate a comparison.
            </p>
          </CardContent>
        </Card>
      )}

      {prediction && rows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Predicted vs Actual</CardTitle>
            <CardDescription>Side-by-side comparison of metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Metric</TableHead>
                    <TableHead className="text-right">Predicted</TableHead>
                    <TableHead className="text-right">Actual</TableHead>
                    <TableHead className="text-right">Deviation</TableHead>
                    <TableHead className="w-[40px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((row) => (
                    <TableRow key={row.label}>
                      <TableCell className="font-medium">{row.label}</TableCell>
                      <TableCell className="text-right">
                        {formatRate(row.predicted)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatRate(row.actual)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatDeviation(row.deviation)}
                      </TableCell>
                      <TableCell>
                        <DeviationIcon value={row.deviation} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {prediction.actual_impressions !== null && (
              <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-zinc-500">Impressions</span>
                  <p className="font-medium">
                    {prediction.actual_impressions?.toLocaleString() ?? "—"}
                  </p>
                </div>
                <div>
                  <span className="text-zinc-500">Clicks</span>
                  <p className="font-medium">
                    {prediction.actual_clicks?.toLocaleString() ?? "—"}
                  </p>
                </div>
                <div>
                  <span className="text-zinc-500">Conversions</span>
                  <p className="font-medium">
                    {prediction.actual_conversions?.toLocaleString() ?? "—"}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Enter Actual Results</CardTitle>
          <CardDescription>
            Manually enter actual performance data if auto-tracking is not set up
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="actual_ctr">CTR (%)</Label>
              <Input
                id="actual_ctr"
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={actualsForm.actual_ctr}
                onChange={(e) =>
                  setActualsForm({ ...actualsForm, actual_ctr: e.target.value })
                }
                placeholder="e.g. 2.5"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="actual_engagement">Engagement Rate (%)</Label>
              <Input
                id="actual_engagement"
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={actualsForm.actual_engagement_rate}
                onChange={(e) =>
                  setActualsForm({
                    ...actualsForm,
                    actual_engagement_rate: e.target.value,
                  })
                }
                placeholder="e.g. 5.0"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="actual_conversion">Conversion Rate (%)</Label>
              <Input
                id="actual_conversion"
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={actualsForm.actual_conversion_rate}
                onChange={(e) =>
                  setActualsForm({
                    ...actualsForm,
                    actual_conversion_rate: e.target.value,
                  })
                }
                placeholder="e.g. 1.2"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="actual_impressions">Impressions</Label>
              <Input
                id="actual_impressions"
                type="number"
                min="0"
                value={actualsForm.actual_impressions}
                onChange={(e) =>
                  setActualsForm({
                    ...actualsForm,
                    actual_impressions: e.target.value,
                  })
                }
                placeholder="0"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="actual_clicks">Clicks</Label>
              <Input
                id="actual_clicks"
                type="number"
                min="0"
                value={actualsForm.actual_clicks}
                onChange={(e) =>
                  setActualsForm({
                    ...actualsForm,
                    actual_clicks: e.target.value,
                  })
                }
                placeholder="0"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="actual_conversions">Conversions</Label>
              <Input
                id="actual_conversions"
                type="number"
                min="0"
                value={actualsForm.actual_conversions}
                onChange={(e) =>
                  setActualsForm({
                    ...actualsForm,
                    actual_conversions: e.target.value,
                  })
                }
                placeholder="0"
              />
            </div>
          </div>
          <Button
            onClick={handleUpdateActuals}
            disabled={updateActuals.isPending}
            className="mt-4"
          >
            {updateActuals.isPending ? "Updating..." : "Update Actuals"}
          </Button>
        </CardContent>
      </Card>

      {prediction?.last_synced_at && (
        <p className="text-xs text-zinc-400 text-right">
          Last synced: {new Date(prediction.last_synced_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}
