"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import {
  ArrowLeft,
  BarChart3,
  DollarSign,
  Eye,
  MousePointerClick,
  Plus,
  Target,
  Trash2,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useCampaignAnalytics,
  useCampaignAnalyticsSummary,
  useAddPerformanceEntry,
  useDeletePerformanceEntry,
} from "@/hooks/use-analytics";
import type { AdPerformanceSource } from "@/types";

const SOURCE_LABELS: Record<AdPerformanceSource, string> = {
  FACEBOOK: "Facebook",
  INSTAGRAM: "Instagram",
  GOOGLE_ADS: "Google Ads",
  MANUAL: "Manual",
};

const SOURCE_COLORS: Record<AdPerformanceSource, string> = {
  FACEBOOK: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  INSTAGRAM: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
  GOOGLE_ADS: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  MANUAL: "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200",
};

function formatCents(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatPercent(value: number | null): string {
  if (value === null) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

function formatRoas(value: number | null): string {
  if (value === null) return "—";
  return `${value.toFixed(2)}x`;
}

export default function CampaignAnalyticsPage() {
  const params = useParams<{ id: string }>();
  const campaignId = Number(params.id);

  const [sourceFilter, setSourceFilter] = useState<AdPerformanceSource | "ALL">("ALL");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const [form, setForm] = useState({
    source: "MANUAL" as AdPerformanceSource,
    date: new Date().toISOString().split("T")[0],
    impressions: "",
    clicks: "",
    conversions: "",
    spend_cents: "",
    revenue_cents: "",
  });

  const filters = {
    source: sourceFilter === "ALL" ? undefined : sourceFilter,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  };

  const { data: entries, isLoading } = useCampaignAnalytics(campaignId, filters);
  const { data: summary } = useCampaignAnalyticsSummary(campaignId);
  const addEntry = useAddPerformanceEntry(campaignId);
  const deleteEntry = useDeletePerformanceEntry(campaignId);

  function handleSubmit() {
    if (!form.date || !form.impressions) {
      toast.error("Date and impressions are required");
      return;
    }

    addEntry.mutate(
      {
        source: form.source,
        date: form.date,
        impressions: Number(form.impressions),
        clicks: Number(form.clicks) || 0,
        conversions: Number(form.conversions) || 0,
        spend_cents: Number(form.spend_cents) || 0,
        revenue_cents: Number(form.revenue_cents) || 0,
      },
      {
        onSuccess: () => {
          toast.success("Performance entry added");
          setDialogOpen(false);
          setForm({
            source: "MANUAL",
            date: new Date().toISOString().split("T")[0],
            impressions: "",
            clicks: "",
            conversions: "",
            spend_cents: "",
            revenue_cents: "",
          });
        },
        onError: () => {
          toast.error("Failed to add entry");
        },
      }
    );
  }

  function handleDelete(entryId: number) {
    deleteEntry.mutate(entryId, {
      onSuccess: () => toast.success("Entry deleted"),
      onError: () => toast.error("Failed to delete entry"),
    });
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-zinc-500">Loading analytics...</div>
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
            <h1 className="text-2xl font-bold">Ad Performance</h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              Track and analyze ad performance across platforms
            </p>
          </div>
        </div>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Manual Entry
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Performance Data</DialogTitle>
              <DialogDescription>
                Manually enter ad performance metrics for this campaign.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="source">Source</Label>
                <Select
                  value={form.source}
                  onValueChange={(v) =>
                    setForm({ ...form, source: v as AdPerformanceSource })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FACEBOOK">Facebook</SelectItem>
                    <SelectItem value="INSTAGRAM">Instagram</SelectItem>
                    <SelectItem value="GOOGLE_ADS">Google Ads</SelectItem>
                    <SelectItem value="MANUAL">Manual</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="date">Date</Label>
                <Input
                  id="date"
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="impressions">Impressions</Label>
                  <Input
                    id="impressions"
                    type="number"
                    min="0"
                    value={form.impressions}
                    onChange={(e) =>
                      setForm({ ...form, impressions: e.target.value })
                    }
                    placeholder="0"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="clicks">Clicks</Label>
                  <Input
                    id="clicks"
                    type="number"
                    min="0"
                    value={form.clicks}
                    onChange={(e) =>
                      setForm({ ...form, clicks: e.target.value })
                    }
                    placeholder="0"
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="conversions">Conversions</Label>
                <Input
                  id="conversions"
                  type="number"
                  min="0"
                  value={form.conversions}
                  onChange={(e) =>
                    setForm({ ...form, conversions: e.target.value })
                  }
                  placeholder="0"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="spend">Spend (cents)</Label>
                  <Input
                    id="spend"
                    type="number"
                    min="0"
                    value={form.spend_cents}
                    onChange={(e) =>
                      setForm({ ...form, spend_cents: e.target.value })
                    }
                    placeholder="0"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="revenue">Revenue (cents)</Label>
                  <Input
                    id="revenue"
                    type="number"
                    min="0"
                    value={form.revenue_cents}
                    onChange={(e) =>
                      setForm({ ...form, revenue_cents: e.target.value })
                    }
                    placeholder="0"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={addEntry.isPending}>
                {addEntry.isPending ? "Adding..." : "Add Entry"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <Eye className="h-3 w-3" />
                Impressions
              </CardDescription>
              <CardTitle className="text-xl">
                {summary.total_impressions.toLocaleString()}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <MousePointerClick className="h-3 w-3" />
                Clicks
              </CardDescription>
              <CardTitle className="text-xl">
                {summary.total_clicks.toLocaleString()}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <Target className="h-3 w-3" />
                CTR
              </CardDescription>
              <CardTitle className="text-xl">
                {formatPercent(summary.avg_ctr)}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                Total Spend
              </CardDescription>
              <CardTitle className="text-xl">
                {formatCents(summary.total_spend_cents)}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                Revenue
              </CardDescription>
              <CardTitle className="text-xl">
                {formatCents(summary.total_revenue_cents)}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                ROAS
              </CardDescription>
              <CardTitle className="text-xl">
                {formatRoas(summary.avg_roas)}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Performance Data
              </CardTitle>
              <CardDescription>
                {summary ? `${summary.days_tracked} days tracked` : "No data yet"}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value={sourceFilter}
                onValueChange={(v) =>
                  setSourceFilter(v as AdPerformanceSource | "ALL")
                }
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="All sources" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Sources</SelectItem>
                  <SelectItem value="FACEBOOK">Facebook</SelectItem>
                  <SelectItem value="INSTAGRAM">Instagram</SelectItem>
                  <SelectItem value="GOOGLE_ADS">Google Ads</SelectItem>
                  <SelectItem value="MANUAL">Manual</SelectItem>
                </SelectContent>
              </Select>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-[150px]"
                placeholder="From"
              />
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-[150px]"
                placeholder="To"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!entries || entries.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg font-medium">No performance data yet</p>
              <p className="text-sm mt-1">
                Add manual entries or connect your ad platforms to start tracking.
              </p>
            </div>
          ) : (
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead className="text-right">Impressions</TableHead>
                    <TableHead className="text-right">Clicks</TableHead>
                    <TableHead className="text-right">CTR</TableHead>
                    <TableHead className="text-right">Spend</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                    <TableHead className="text-right">ROAS</TableHead>
                    <TableHead className="w-[50px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="font-medium">
                        {new Date(entry.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={SOURCE_COLORS[entry.source]}
                        >
                          {SOURCE_LABELS[entry.source]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {entry.impressions.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        {entry.clicks.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatPercent(entry.ctr)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCents(entry.spend_cents)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCents(entry.revenue_cents)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatRoas(entry.roas)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-zinc-400 hover:text-red-500"
                          onClick={() => handleDelete(entry.id)}
                          disabled={deleteEntry.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
