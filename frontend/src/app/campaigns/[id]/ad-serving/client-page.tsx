"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
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
import { Skeleton } from "@/components/ui/skeleton";
import { useCampaign } from "@/hooks/use-campaigns";
import { useAssets } from "@/hooks/use-assets";
import {
  useAdUnits,
  useCreateAdUnit,
  useUpdateAdUnit,
  useDeleteAdUnit,
  useAdUnitStats,
} from "@/hooks/use-ad-serving";
import type { AdUnit, AdUnitCreate, AdServingStatus, Asset } from "@/types";

const STATUS_STYLES: Record<AdServingStatus, string> = {
  DRAFT: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
  ACTIVE: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  PAUSED: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  EXPIRED: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  ARCHIVED: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
};

function StatusBadge({ status }: { status: AdServingStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

function StatsPanel({ campaignId, unitId }: { campaignId: number; unitId: number }) {
  const { data: stats, isLoading } = useAdUnitStats(campaignId, unitId);

  if (isLoading) return <Skeleton className="h-16 w-full" />;
  if (!stats) return null;

  return (
    <div className="grid grid-cols-3 gap-3 text-center text-sm">
      <div>
        <p className="text-muted-foreground">Today</p>
        <p className="font-semibold">{stats.impressions_today} imp / {stats.clicks_today} clk</p>
      </div>
      <div>
        <p className="text-muted-foreground">Total</p>
        <p className="font-semibold">{stats.total_impressions} imp / {stats.total_clicks} clk</p>
      </div>
      <div>
        <p className="text-muted-foreground">CTR</p>
        <p className="font-semibold">{stats.ctr != null ? `${stats.ctr}%` : "—"}</p>
      </div>
    </div>
  );
}

function EmbedCodeBlock({ code }: { code: string }) {
  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    toast.success("Embed code copied");
  };

  return (
    <div className="relative">
      <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs font-mono">
        {code}
      </pre>
      <Button
        variant="outline"
        size="sm"
        className="absolute top-2 right-2"
        onClick={handleCopy}
      >
        Copy
      </Button>
    </div>
  );
}

interface CreateFormState {
  name: string;
  target_url: string;
  asset_id: string;
  starts_at: string;
  ends_at: string;
  daily_impression_cap: string;
  daily_click_cap: string;
}

const EMPTY_FORM: CreateFormState = {
  name: "",
  target_url: "",
  asset_id: "",
  starts_at: "",
  ends_at: "",
  daily_impression_cap: "",
  daily_click_cap: "",
};

function formToPayload(campaignId: number, form: CreateFormState): AdUnitCreate {
  return {
    campaign_id: campaignId,
    name: form.name,
    target_url: form.target_url,
    asset_id: form.asset_id ? Number(form.asset_id) : null,
    starts_at: form.starts_at || null,
    ends_at: form.ends_at || null,
    daily_impression_cap: form.daily_impression_cap ? Number(form.daily_impression_cap) : null,
    daily_click_cap: form.daily_click_cap ? Number(form.daily_click_cap) : null,
  };
}

function CreateDialog({
  campaignId,
  assets,
}: {
  campaignId: number;
  assets: Asset[];
}) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<CreateFormState>({ ...EMPTY_FORM });
  const createAdUnit = useCreateAdUnit(campaignId);

  const imageAssets = assets.filter((a) => a.type === "IMAGE");

  const handleCreate = async () => {
    if (!form.name.trim() || !form.target_url.trim()) {
      toast.error("Name and target URL are required");
      return;
    }
    try {
      await createAdUnit.mutateAsync(formToPayload(campaignId, form));
      toast.success("Ad unit created");
      setForm({ ...EMPTY_FORM });
      setOpen(false);
    } catch {
      toast.error("Failed to create ad unit");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create Ad Unit</Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Create Ad Unit</DialogTitle>
          <DialogDescription>Set up a new ad unit for serving</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              placeholder="e.g. Homepage Banner"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="target_url">Target URL</Label>
            <Input
              id="target_url"
              value={form.target_url}
              onChange={(e) => setForm((p) => ({ ...p, target_url: e.target.value }))}
              placeholder="https://example.com/landing"
            />
          </div>
          <div className="grid gap-2">
            <Label>Asset</Label>
            <Select
              value={form.asset_id}
              onValueChange={(v) => setForm((p) => ({ ...p, asset_id: v }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select an asset (optional)" />
              </SelectTrigger>
              <SelectContent>
                {imageAssets.map((asset) => (
                  <SelectItem key={asset.id} value={String(asset.id)}>
                    {asset.type} #{asset.id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="starts_at">Start Date</Label>
              <Input
                id="starts_at"
                type="datetime-local"
                value={form.starts_at}
                onChange={(e) => setForm((p) => ({ ...p, starts_at: e.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="ends_at">End Date</Label>
              <Input
                id="ends_at"
                type="datetime-local"
                value={form.ends_at}
                onChange={(e) => setForm((p) => ({ ...p, ends_at: e.target.value }))}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="daily_impression_cap">Daily Impression Cap</Label>
              <Input
                id="daily_impression_cap"
                type="number"
                value={form.daily_impression_cap}
                onChange={(e) => setForm((p) => ({ ...p, daily_impression_cap: e.target.value }))}
                placeholder="No limit"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="daily_click_cap">Daily Click Cap</Label>
              <Input
                id="daily_click_cap"
                type="number"
                value={form.daily_click_cap}
                onChange={(e) => setForm((p) => ({ ...p, daily_click_cap: e.target.value }))}
                placeholder="No limit"
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={createAdUnit.isPending}>
            {createAdUnit.isPending ? "Creating..." : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AdUnitCard({
  unit,
  campaignId,
}: {
  unit: AdUnit;
  campaignId: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const updateAdUnit = useUpdateAdUnit(campaignId);
  const deleteAdUnit = useDeleteAdUnit(campaignId);

  const handleStatusChange = async (status: AdServingStatus) => {
    try {
      await updateAdUnit.mutateAsync({ unitId: unit.id, data: { status } });
      toast.success(`Ad unit ${status.toLowerCase()}`);
    } catch {
      toast.error("Failed to update status");
    }
  };

  const handleArchive = async () => {
    try {
      await deleteAdUnit.mutateAsync(unit.id);
      toast.success("Ad unit archived");
    } catch {
      toast.error("Failed to archive ad unit");
    }
  };

  const formatDate = (d: string | null) => {
    if (!d) return "—";
    return new Date(d).toLocaleDateString();
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{unit.name}</CardTitle>
          <StatusBadge status={unit.status} />
        </div>
        <CardDescription className="truncate">{unit.target_url}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-3 text-center text-sm">
          <div>
            <p className="text-muted-foreground">Impressions</p>
            <p className="font-semibold">{unit.total_impressions}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Clicks</p>
            <p className="font-semibold">{unit.total_clicks}</p>
          </div>
          <div>
            <p className="text-muted-foreground">CTR</p>
            <p className="font-semibold">{unit.ctr != null ? `${unit.ctr}%` : "—"}</p>
          </div>
        </div>

        {(unit.starts_at || unit.ends_at) && (
          <p className="text-xs text-muted-foreground">
            {formatDate(unit.starts_at)} → {formatDate(unit.ends_at)}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
          {unit.status === "DRAFT" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleStatusChange("ACTIVE")}
              disabled={updateAdUnit.isPending}
            >
              Activate
            </Button>
          )}
          {unit.status === "ACTIVE" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleStatusChange("PAUSED")}
              disabled={updateAdUnit.isPending}
            >
              Pause
            </Button>
          )}
          {unit.status === "PAUSED" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleStatusChange("ACTIVE")}
              disabled={updateAdUnit.isPending}
            >
              Resume
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleArchive}
            disabled={deleteAdUnit.isPending}
            className="text-destructive hover:text-destructive"
          >
            Archive
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded((p) => !p)}
          >
            {expanded ? "Hide Details" : "Details"}
          </Button>
        </div>

        {expanded && (
          <div className="space-y-4 pt-2">
            <StatsPanel campaignId={campaignId} unitId={unit.id} />
            {unit.embed_code && <EmbedCodeBlock code={unit.embed_code} />}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function AdServingPage() {
  const params = useParams<{ id: string }>();
  const campaignId = Number(params.id);

  const { data: campaign, isLoading: campaignLoading } = useCampaign(campaignId);
  const { data: adUnits, isLoading: unitsLoading } = useAdUnits(campaignId);
  const { data: assets } = useAssets(campaignId);

  if (campaignLoading) {
    return (
      <div className="flex flex-col gap-6 p-6 max-w-5xl mx-auto">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[200px] w-full rounded-xl" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <h2 className="text-2xl font-bold">Campaign not found</h2>
        <Link href="/campaigns">
          <Button variant="outline">Back to Campaigns</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{campaign.title}</h1>
          <p className="text-muted-foreground">Ad Serving &amp; Embed</p>
        </div>
        <div className="flex items-center gap-2">
          <CreateDialog campaignId={campaignId} assets={assets ?? []} />
          <Link href="/campaigns">
            <Button variant="outline">Back</Button>
          </Link>
        </div>
      </div>

      {unitsLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-[200px] rounded-xl" />
          <Skeleton className="h-[200px] rounded-xl" />
        </div>
      ) : adUnits && adUnits.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {adUnits.map((unit) => (
            <AdUnitCard key={unit.id} unit={unit} campaignId={campaignId} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 gap-4">
            <p className="text-muted-foreground">
              No ad units yet. Create one to start serving ads.
            </p>
            <CreateDialog campaignId={campaignId} assets={assets ?? []} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
