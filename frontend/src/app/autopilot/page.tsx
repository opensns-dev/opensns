"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Bot,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  History,
  Loader2,
  Pencil,
  Play,
  Plus,
  Sparkles,
  Trash2,
  TriangleAlert,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useAutopilotHistories,
  useAutopilotHistory,
  useAutopilotRules,
  useCreateAutopilotRule,
  useDeleteAutopilotRule,
  useRunAutopilotNow,
  useToggleAutopilotRule,
  useUpdateAutopilotRule,
} from "@/hooks/use-autopilot";
import { useAutopilotWebSocket } from "@/hooks/use-autopilot-ws";
import { useBillingOverview } from "@/hooks/use-billing";
import { useBrandKits } from "@/hooks/use-brand-kits";
import { usePublishConnections } from "@/hooks/use-publishing";
import { cn } from "@/lib/utils";
import type {
  AutopilotCadence,
  AutopilotRule,
  AutopilotRuleCreate,
  AutopilotRunLog,
  AutopilotRunStatus,
} from "@/types";

const PLATFORM_OPTIONS = [
  { value: "INSTAGRAM", label: "Instagram" },
  { value: "FACEBOOK", label: "Facebook" },
  { value: "GOOGLE_ADS", label: "Google Ads" },
  { value: "TIKTOK", label: "TikTok" },
  { value: "NAVER", label: "Naver" },
] as const;

const ASSET_TYPE_OPTIONS = [
  { value: "image", label: "Image", locked: true },
  { value: "video", label: "Video", locked: false },
  { value: "ugc", label: "UGC", locked: false },
] as const;

const TIMEZONE_OPTIONS = [
  "Asia/Seoul",
  "America/New_York",
  "America/Los_Angeles",
  "Europe/London",
  "Asia/Tokyo",
  "UTC",
] as const;

const WEEKDAY_OPTIONS = [
  { label: "Mon", value: 0 },
  { label: "Tue", value: 1 },
  { label: "Wed", value: 2 },
  { label: "Thu", value: 3 },
  { label: "Fri", value: 4 },
  { label: "Sat", value: 5 },
  { label: "Sun", value: 6 },
] as const;

const CALENDAR_WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const TAB_OPTIONS = [
  { value: "schedules", label: "Schedules" },
  { value: "calendar", label: "Calendar" },
  { value: "performance", label: "Performance" },
] as const;

const STATUS_VARIANT: Record<
  AutopilotRunStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  RUNNING: "secondary",
  AWAITING_APPROVAL: "outline",
  COMPLETED: "default",
  FAILED: "destructive",
  EXPIRED: "outline",
  SKIPPED: "outline",
};

const PUBLISH_STATUS_STYLES: Record<string, string> = {
  published:
    "border-emerald-200 bg-emerald-500/10 text-emerald-700 dark:border-emerald-500/30 dark:text-emerald-300",
  partial:
    "border-amber-200 bg-amber-500/10 text-amber-700 dark:border-amber-500/30 dark:text-amber-300",
  failed:
    "border-destructive/30 bg-destructive/10 text-destructive",
};

const CADENCE_LABELS: Record<AutopilotCadence, string> = {
  DAILY: "Daily",
  WEEKLY: "Weekly",
  MONTHLY: "Monthly",
};

interface AutopilotFormState {
  product_url: string;
  cadence: AutopilotCadence;
  weeklyDays: number[];
  monthlyDays: string;
  time_of_day: string;
  timezone: string;
  num_variations: string;
  platform_targets: string[];
  assetTypes: string[];
  brand_kit_id: string;
  requiresApproval: boolean;
  autoPublish: boolean;
  publishConnectionIds: number[];
}

const EMPTY_FORM: AutopilotFormState = {
  product_url: "",
  cadence: "DAILY",
  weeklyDays: [],
  monthlyDays: "",
  time_of_day: "09:00",
  timezone: "Asia/Seoul",
  num_variations: "3",
  platform_targets: ["INSTAGRAM", "FACEBOOK"],
  assetTypes: ["image"],
  brand_kit_id: "none",
  requiresApproval: true,
  autoPublish: false,
  publishConnectionIds: [],
};

interface CalendarEventItem {
  key: string;
  type: "scheduled" | "completed" | "failed" | "awaiting";
  title: string;
  description: string;
  timestamp: string;
  ruleId: number;
}

interface CalendarDayCell {
  key: string;
  date: Date;
  isCurrentMonth: boolean;
  items: CalendarEventItem[];
}

interface RulePerformanceRow {
  ruleId: number;
  productUrl: string;
  totalRuns: number;
  successCount: number;
  failCount: number;
  awaitingCount: number;
  creditsUsed: number;
  avgCreditsPerRun: number;
  publishCount: number;
}

function formatDateTime(value: string | null) {
  if (!value) return "—";

  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatRelativeTime(value: string | null) {
  if (!value) return "—";

  const diffMs = new Date(value).getTime() - Date.now();
  const diffMinutes = Math.round(diffMs / (1000 * 60));
  const absMinutes = Math.abs(diffMinutes);

  if (absMinutes < 60) {
    return diffMinutes >= 0
      ? `in ${absMinutes}m`
      : `${absMinutes}m ago`;
  }

  const diffHours = Math.round(absMinutes / 60);
  if (diffHours < 24) {
    return diffMinutes >= 0 ? `in ${diffHours}h` : `${diffHours}h ago`;
  }

  const diffDays = Math.round(diffHours / 24);
  return diffMinutes >= 0 ? `in ${diffDays}d` : `${diffDays}d ago`;
}

function truncateUrl(url: string, maxLength = 64) {
  if (url.length <= maxLength) return url;
  return `${url.slice(0, maxLength - 1)}…`;
}

function getStatusVariant(status: string) {
  return STATUS_VARIANT[status as AutopilotRunStatus] ?? "outline";
}

function normalizePublishStatus(value: string | null) {
  return value?.toLowerCase() ?? null;
}

function getPublishStatusClassName(value: string | null) {
  const normalized = normalizePublishStatus(value);
  if (!normalized) {
    return null;
  }

  return (
    PUBLISH_STATUS_STYLES[normalized] ??
    "border-border bg-muted text-muted-foreground"
  );
}

function parseMonthlyDays(input: string) {
  if (!input.trim()) return null;

  const days = input
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value) => Number(value));

  if (days.some((day) => Number.isNaN(day) || day < 1 || day > 31)) {
    throw new Error("Monthly day numbers must be between 1 and 31");
  }

  return Array.from(new Set(days)).sort((a, b) => a - b);
}

function parseTimeOfDay(timeOfDay: string) {
  const [hours, minutes] = timeOfDay.split(":").map(Number);
  return { hours, minutes };
}

function startOfDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function isSameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function startOfCalendarGrid(month: Date) {
  const firstDay = new Date(month.getFullYear(), month.getMonth(), 1);
  const offset = firstDay.getDay();
  const start = new Date(firstDay);
  start.setDate(firstDay.getDate() - offset);
  return startOfDay(start);
}

function monthLabel(date: Date) {
  return date.toLocaleDateString([], {
    month: "long",
    year: "numeric",
  });
}

function countScheduledOccurrences(rule: AutopilotRule, month: Date) {
  const occurrences = computeRuleOccurrences(rule, month, 12);
  return occurrences.filter(
    (date) =>
      date.getFullYear() === month.getFullYear() &&
      date.getMonth() === month.getMonth()
  ).length;
}

function computeRuleOccurrences(
  rule: AutopilotRule,
  fromDate: Date,
  limit: number
): Date[] {
  const occurrences: Date[] = [];
  const cursor = new Date(fromDate);
  const safeLimit = Math.max(limit, 1);
  const { hours, minutes } = parseTimeOfDay(rule.time_of_day);
  const maxIterations = 420;

  for (let step = 0; step < maxIterations && occurrences.length < safeLimit; step += 1) {
    const candidate = new Date(
      cursor.getFullYear(),
      cursor.getMonth(),
      cursor.getDate(),
      hours,
      minutes,
      0,
      0
    );

    const isAfterStart = candidate.getTime() >= fromDate.getTime();
    const isMatch =
      rule.cadence === "DAILY"
        ? true
        : rule.cadence === "WEEKLY"
          ? (rule.days_of_week ?? []).includes((candidate.getDay() + 6) % 7)
          : (rule.days_of_week ?? []).includes(candidate.getDate());

    if (isAfterStart && isMatch) {
      occurrences.push(candidate);
    }

    cursor.setDate(cursor.getDate() + 1);
  }

  return occurrences;
}

function buildPayload(form: AutopilotFormState): AutopilotRuleCreate {
  const numVariations = Number(form.num_variations);

  if (!form.product_url.trim()) {
    throw new Error("Product URL is required");
  }

  if (!/^\d{2}:\d{2}$/.test(form.time_of_day)) {
    throw new Error("Time of day must use HH:MM format");
  }

  if (Number.isNaN(numVariations) || numVariations < 1 || numVariations > 10) {
    throw new Error("Number of variations must be between 1 and 10");
  }

  if (form.platform_targets.length === 0) {
    throw new Error("Select at least one platform target");
  }

  if (!form.assetTypes.includes("image")) {
    throw new Error("Image assets are required for autopilot runs");
  }

  let days_of_week: number[] | null | undefined;
  if (form.cadence === "WEEKLY") {
    if (form.weeklyDays.length === 0) {
      throw new Error("Choose at least one day for weekly cadence");
    }
    days_of_week = [...form.weeklyDays].sort((a, b) => a - b);
  } else if (form.cadence === "MONTHLY") {
    days_of_week = parseMonthlyDays(form.monthlyDays);
    if (!days_of_week || days_of_week.length === 0) {
      throw new Error("Enter at least one monthly day number");
    }
  } else {
    days_of_week = null;
  }

  if (!form.requiresApproval && form.autoPublish && form.publishConnectionIds.length === 0) {
    throw new Error("Choose at least one publish connection for auto-publish");
  }

  return {
    product_url: form.product_url.trim(),
    platform_targets: form.platform_targets,
    cadence: form.cadence,
    days_of_week,
    time_of_day: form.time_of_day,
    timezone: form.timezone,
    num_variations: numVariations,
    brand_kit_id: form.brand_kit_id === "none" ? null : Number(form.brand_kit_id),
    asset_types: form.assetTypes,
    requires_approval: form.requiresApproval,
    auto_publish: !form.requiresApproval && form.autoPublish,
    publish_connection_ids:
      !form.requiresApproval && form.autoPublish
        ? form.publishConnectionIds
        : [],
  };
}

function formFromRule(rule: AutopilotRule): AutopilotFormState {
  return {
    product_url: rule.product_url,
    cadence: (rule.cadence as AutopilotCadence) || "DAILY",
    weeklyDays:
      rule.cadence === "WEEKLY" && rule.days_of_week ? rule.days_of_week : [],
    monthlyDays:
      rule.cadence === "MONTHLY" && rule.days_of_week
        ? rule.days_of_week.join(", ")
        : "",
    time_of_day: rule.time_of_day,
    timezone: rule.timezone,
    num_variations: String(rule.num_variations),
    platform_targets: rule.platform_targets,
    assetTypes: rule.asset_types?.length ? rule.asset_types : ["image"],
    brand_kit_id:
      rule.brand_kit_id === null ? "none" : String(rule.brand_kit_id),
    requiresApproval: rule.requires_approval,
    autoPublish: rule.auto_publish,
    publishConnectionIds: rule.publish_connection_ids ?? [],
  };
}

function aggregateRulePerformance(
  rules: AutopilotRule[],
  historyMap: Map<number, AutopilotRunLog[]>
) {
  const rows: RulePerformanceRow[] = rules.map((rule) => {
    const logs = historyMap.get(rule.id) ?? [];
    const completedRuns = logs.filter((log) => log.status === "COMPLETED").length;
    const failedRuns = logs.filter((log) => log.status === "FAILED").length;
    const awaitingRuns = logs.filter(
      (log) => log.status === "AWAITING_APPROVAL"
    ).length;
    const creditsUsed = logs.reduce((sum, log) => sum + log.credits_used, 0);
    const publishCount = logs.filter(
      (log) => normalizePublishStatus(log.publish_status) === "published"
    ).length;

    return {
      ruleId: rule.id,
      productUrl: rule.product_url,
      totalRuns: logs.length,
      successCount: completedRuns,
      failCount: failedRuns,
      awaitingCount: awaitingRuns,
      creditsUsed,
      avgCreditsPerRun: logs.length ? creditsUsed / logs.length : 0,
      publishCount,
    };
  });

  const totals = rows.reduce(
    (summary, row) => ({
      totalRuns: summary.totalRuns + row.successCount,
      allRunAttempts: summary.allRunAttempts + row.totalRuns,
      failCount: summary.failCount + row.failCount,
      creditsUsed: summary.creditsUsed + row.creditsUsed,
    }),
    {
      totalRuns: 0,
      allRunAttempts: 0,
      failCount: 0,
      creditsUsed: 0,
    }
  );

  return {
    rows,
    totalCompletedRuns: totals.totalRuns,
    totalCreditsUsed: totals.creditsUsed,
    successRate:
      totals.allRunAttempts > 0
        ? (totals.totalRuns / totals.allRunAttempts) * 100
        : 0,
    avgCreditsPerRun:
      totals.allRunAttempts > 0
        ? totals.creditsUsed / totals.allRunAttempts
        : 0,
  };
}

function buildCalendarCells(
  month: Date,
  rules: AutopilotRule[],
  historyMap: Map<number, AutopilotRunLog[]>
) {
  const start = startOfCalendarGrid(month);
  const cells: CalendarDayCell[] = [];

  for (let index = 0; index < 42; index += 1) {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    const items: CalendarEventItem[] = [];

    rules.forEach((rule) => {
      const scheduledDates = computeRuleOccurrences(
        rule,
        new Date(month.getFullYear(), month.getMonth(), 1),
        12
      ).filter((scheduledDate) => isSameDay(scheduledDate, date));

      scheduledDates.forEach((scheduledDate, scheduledIndex) => {
        items.push({
          key: `scheduled-${rule.id}-${scheduledDate.toISOString()}-${scheduledIndex}`,
          type: "scheduled",
          title: truncateUrl(rule.product_url, 32),
          description: `Scheduled ${rule.time_of_day} · ${CADENCE_LABELS[(rule.cadence as AutopilotCadence) || "DAILY"]}`,
          timestamp: scheduledDate.toISOString(),
          ruleId: rule.id,
        });
      });

      const history = historyMap.get(rule.id) ?? [];
      history.forEach((log) => {
        const referenceDate = log.completed_at ?? log.started_at;
        if (!referenceDate) {
          return;
        }

        const logDate = new Date(referenceDate);
        if (!isSameDay(logDate, date)) {
          return;
        }

        items.push({
          key: `history-${log.id}`,
          type:
            log.status === "COMPLETED"
              ? "completed"
              : log.status === "FAILED"
                ? "failed"
                : "awaiting",
          title: truncateUrl(rule.product_url, 32),
          description: `${log.status} · ${log.credits_used} credits used`,
          timestamp: referenceDate,
          ruleId: rule.id,
        });
      });
    });

    items.sort(
      (left, right) =>
        new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime()
    );

    cells.push({
      key: date.toISOString(),
      date,
      isCurrentMonth: date.getMonth() === month.getMonth(),
      items,
    });
  }

  return cells;
}

function EventDots({ items }: { items: CalendarEventItem[] }) {
  const visibleItems = items.slice(0, 4);

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {visibleItems.map((item) => (
        <span
          key={item.key}
          className={cn(
            "size-2 rounded-full",
            item.type === "scheduled" && "bg-primary/60",
            item.type === "completed" && "bg-emerald-500",
            item.type === "failed" && "bg-destructive",
            item.type === "awaiting" && "bg-amber-500"
          )}
          title={`${item.title} · ${item.description}`}
        />
      ))}
      {items.length > visibleItems.length ? (
        <span className="text-[10px] text-muted-foreground">+{items.length - visibleItems.length}</span>
      ) : null}
    </div>
  );
}

function RuleFormFields({
  form,
  onChange,
  brandKitOptions,
  publishConnections,
}: {
  form: AutopilotFormState;
  onChange: (updater: (current: AutopilotFormState) => AutopilotFormState) => void;
  brandKitOptions: { id: number; name: string }[];
  publishConnections: {
    id: number;
    label: string;
    platform: string;
    isActive: boolean;
  }[];
}) {
  const togglePlatform = (platform: string) => {
    onChange((current) => {
      const platform_targets = current.platform_targets.includes(platform)
        ? current.platform_targets.filter((value) => value !== platform)
        : [...current.platform_targets, platform];

      return { ...current, platform_targets };
    });
  };

  const toggleWeekday = (day: number) => {
    onChange((current) => {
      const weeklyDays = current.weeklyDays.includes(day)
        ? current.weeklyDays.filter((value) => value !== day)
        : [...current.weeklyDays, day].sort((a, b) => a - b);

      return { ...current, weeklyDays };
    });
  };

  const toggleAssetType = (assetType: string, locked: boolean) => {
    if (locked) {
      return;
    }

    onChange((current) => {
      const assetTypes = current.assetTypes.includes(assetType)
        ? current.assetTypes.filter((value) => value !== assetType)
        : [...current.assetTypes, assetType];

      return {
        ...current,
        assetTypes: Array.from(new Set(["image", ...assetTypes])),
      };
    });
  };

  const togglePublishConnection = (connectionId: number) => {
    onChange((current) => {
      const publishConnectionIds = current.publishConnectionIds.includes(connectionId)
        ? current.publishConnectionIds.filter((value) => value !== connectionId)
        : [...current.publishConnectionIds, connectionId];

      return { ...current, publishConnectionIds };
    });
  };

  return (
    <div className="grid gap-5">
      <div className="grid gap-2">
        <Label htmlFor="product-url">Product URL</Label>
        <Input
          id="product-url"
          placeholder="https://example.com/product"
          value={form.product_url}
          onChange={(event) =>
            onChange((current) => ({
              ...current,
              product_url: event.target.value,
            }))
          }
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-2">
          <Label>Cadence</Label>
          <Select
            value={form.cadence}
            onValueChange={(value) =>
              onChange((current) => ({
                ...current,
                cadence: value as AutopilotCadence,
              }))
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="DAILY">Daily</SelectItem>
              <SelectItem value="WEEKLY">Weekly</SelectItem>
              <SelectItem value="MONTHLY">Monthly</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="variations">Variations</Label>
          <Input
            id="variations"
            type="number"
            min={1}
            max={10}
            value={form.num_variations}
            onChange={(event) =>
              onChange((current) => ({
                ...current,
                num_variations: event.target.value,
              }))
            }
          />
        </div>
      </div>

      {form.cadence === "WEEKLY" && (
        <div className="grid gap-2">
          <Label>Days of week</Label>
          <div className="flex flex-wrap gap-2">
            {WEEKDAY_OPTIONS.map((day) => {
              const isSelected = form.weeklyDays.includes(day.value);
              return (
                <Button
                  key={day.value}
                  type="button"
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  onClick={() => toggleWeekday(day.value)}
                >
                  {day.label}
                </Button>
              );
            })}
          </div>
        </div>
      )}

      {form.cadence === "MONTHLY" && (
        <div className="grid gap-2">
          <Label htmlFor="monthly-days">Day numbers</Label>
          <Input
            id="monthly-days"
            placeholder="1, 15, 28"
            value={form.monthlyDays}
            onChange={(event) =>
              onChange((current) => ({
                ...current,
                monthlyDays: event.target.value,
              }))
            }
          />
          <p className="text-sm text-muted-foreground">
            Enter one or more day numbers between 1 and 31.
          </p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-2">
          <Label htmlFor="time-of-day">Time of day</Label>
          <Input
            id="time-of-day"
            type="time"
            value={form.time_of_day}
            onChange={(event) =>
              onChange((current) => ({
                ...current,
                time_of_day: event.target.value,
              }))
            }
          />
        </div>

        <div className="grid gap-2">
          <Label>Timezone</Label>
          <Select
            value={form.timezone}
            onValueChange={(value) =>
              onChange((current) => ({ ...current, timezone: value }))
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIMEZONE_OPTIONS.map((timezone) => (
                <SelectItem key={timezone} value={timezone}>
                  {timezone}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-2">
        <Label>Platform targets</Label>
        <div className="flex flex-wrap gap-2">
          {PLATFORM_OPTIONS.map((platform) => {
            const isSelected = form.platform_targets.includes(platform.value);
            return (
              <Button
                key={platform.value}
                type="button"
                variant={isSelected ? "default" : "outline"}
                size="sm"
                onClick={() => togglePlatform(platform.value)}
              >
                {platform.label}
              </Button>
            );
          })}
        </div>
      </div>

      <div className="grid gap-2">
        <Label>Asset types</Label>
        <div className="grid gap-2 rounded-xl border bg-muted/20 p-4">
          {ASSET_TYPE_OPTIONS.map((assetType) => {
            const isChecked = form.assetTypes.includes(assetType.value);
            return (
              <label
                key={assetType.value}
                className={cn(
                  "flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm",
                  isChecked ? "border-primary/40 bg-primary/5" : "border-border bg-background",
                  assetType.locked && "opacity-80"
                )}
              >
                <span className="font-medium">{assetType.label}</span>
                <input
                  type="checkbox"
                  checked={isChecked}
                  disabled={assetType.locked}
                  onChange={() => toggleAssetType(assetType.value, assetType.locked)}
                  className="size-4 accent-primary"
                />
              </label>
            );
          })}
        </div>
      </div>

      <div className="grid gap-2">
        <Label>Brand kit</Label>
        <Select
          value={form.brand_kit_id}
          onValueChange={(value) =>
            onChange((current) => ({ ...current, brand_kit_id: value }))
          }
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Optional" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No brand kit</SelectItem>
            {brandKitOptions.map((brandKit) => (
              <SelectItem key={brandKit.id} value={String(brandKit.id)}>
                {brandKit.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-3 rounded-xl border bg-muted/20 p-4">
        <label className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-sm font-medium">Require approval before publishing</p>
            <p className="text-sm text-muted-foreground">
              Hold each run for review before anything goes live.
            </p>
          </div>
          <input
            type="checkbox"
            checked={form.requiresApproval}
            onChange={(event) =>
              onChange((current) => ({
                ...current,
                requiresApproval: event.target.checked,
                autoPublish: event.target.checked ? false : current.autoPublish,
                publishConnectionIds: event.target.checked
                  ? []
                  : current.publishConnectionIds,
              }))
            }
            className="mt-1 size-4 accent-primary"
          />
        </label>

        {!form.requiresApproval && (
          <div className="grid gap-3 rounded-lg border bg-background p-4">
            <label className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <p className="text-sm font-medium">Auto-publish to connected platforms</p>
                <p className="text-sm text-muted-foreground">
                  Push approved assets directly into your connected channels.
                </p>
              </div>
              <input
                type="checkbox"
                checked={form.autoPublish}
                onChange={(event) =>
                  onChange((current) => ({
                    ...current,
                    autoPublish: event.target.checked,
                    publishConnectionIds: event.target.checked
                      ? current.publishConnectionIds
                      : [],
                  }))
                }
                className="mt-1 size-4 accent-primary"
              />
            </label>

            {form.autoPublish && (
              <div className="grid gap-2">
                <Label>Publish connections</Label>
                {publishConnections.length ? (
                  <div className="grid gap-2">
                    {publishConnections.map((connection) => {
                      const isSelected = form.publishConnectionIds.includes(connection.id);
                      return (
                        <label
                          key={connection.id}
                          className={cn(
                            "flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm",
                            isSelected
                              ? "border-primary/40 bg-primary/5"
                              : "border-border bg-background",
                            !connection.isActive && "opacity-60"
                          )}
                        >
                          <div>
                            <p className="font-medium">{connection.label}</p>
                            <p className="text-xs text-muted-foreground">
                              {connection.platform}
                              {!connection.isActive ? " · Inactive" : ""}
                            </p>
                          </div>
                          <input
                            type="checkbox"
                            checked={isSelected}
                            disabled={!connection.isActive}
                            onChange={() => togglePublishConnection(connection.id)}
                            className="size-4 accent-primary"
                          />
                        </label>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Connect a publishing destination in Settings to enable auto-publish.
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function HistoryContent({
  logs,
  isLoading,
}: {
  logs: AutopilotRunLog[] | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((index) => (
          <Skeleton key={index} className="h-24 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (!logs?.length) {
    return (
      <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
        No run history yet for this schedule.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {logs.map((log) => {
        const publishStatusClassName = getPublishStatusClassName(log.publish_status);
        return (
          <div key={log.id} className="rounded-xl border p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={getStatusVariant(log.status)}>{log.status}</Badge>
                  {publishStatusClassName ? (
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize",
                        publishStatusClassName
                      )}
                    >
                      {normalizePublishStatus(log.publish_status)}
                    </span>
                  ) : null}
                  <span className="text-sm text-muted-foreground">
                    Started {formatDateTime(log.started_at)}
                  </span>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                  <span>Completed: {formatDateTime(log.completed_at)}</span>
                  <span>Estimated: {log.credits_estimated} credits</span>
                  <span>Used: {log.credits_used} credits</span>
                  {log.retry_count > 0 ? <span>Retries: {log.retry_count}</span> : null}
                </div>
                {log.error ? (
                  <p className="text-sm text-destructive">{log.error}</p>
                ) : null}
              </div>

              {log.campaign_id ? (
                <Button asChild variant="outline" size="sm">
                  <Link href={`/campaigns/view?id=${log.campaign_id}`}>
                    View Campaign
                  </Link>
                </Button>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SchedulesTab({
  rules,
  isLoading,
  onEdit,
  onDelete,
  onToggle,
  onRunNow,
  onHistory,
  onCreate,
  isMutating,
}: {
  rules: AutopilotRule[] | undefined;
  isLoading: boolean;
  onEdit: (rule: AutopilotRule) => void;
  onDelete: (ruleId: number) => void;
  onToggle: (ruleId: number) => void;
  onRunNow: (ruleId: number) => void;
  onHistory: (rule: AutopilotRule) => void;
  onCreate: () => void;
  isMutating: boolean;
}) {
  return (
    <div className="grid gap-4">
      {isLoading ? (
        [0, 1, 2].map((index) => (
          <Card key={index}>
            <CardHeader>
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-4 w-1/3" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-10 w-full rounded-xl" />
            </CardContent>
          </Card>
        ))
      ) : rules?.length ? (
        rules.map((rule) => (
          <Card key={rule.id}>
            <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <CardTitle className="text-xl">
                    {truncateUrl(rule.product_url)}
                  </CardTitle>
                  <Badge variant="secondary">{rule.cadence}</Badge>
                  <Badge variant={rule.enabled ? "default" : "outline"}>
                    {rule.enabled ? "Enabled" : "Disabled"}
                  </Badge>
                  {!rule.requires_approval && rule.auto_publish ? (
                    <Badge variant="outline">Auto-publish</Badge>
                  ) : null}
                </div>
                <CardDescription className="max-w-3xl break-all">
                  {rule.product_url}
                </CardDescription>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant={rule.enabled ? "outline" : "default"}
                  size="sm"
                  onClick={() => onToggle(rule.id)}
                  disabled={isMutating}
                >
                  {rule.enabled ? "Disable" : "Enable"}
                </Button>
                <Button variant="outline" size="sm" onClick={() => onEdit(rule)}>
                  <Pencil className="size-4" />
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRunNow(rule.id)}
                  disabled={isMutating}
                >
                  <Play className="size-4" />
                  Run Now
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onHistory(rule)}
                >
                  <History className="size-4" />
                  View History
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => onDelete(rule.id)}
                  disabled={isMutating}
                >
                  <Trash2 className="size-4" />
                  Delete
                </Button>
              </div>
            </CardHeader>

            <CardContent className="grid gap-4">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-xl border bg-muted/30 p-4">
                  <p className="text-sm text-muted-foreground">Next run</p>
                  <p className="mt-1 font-medium">{formatDateTime(rule.next_run_at)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {CADENCE_LABELS[(rule.cadence as AutopilotCadence) || "DAILY"]} at {rule.time_of_day} · {rule.timezone}
                  </p>
                </div>
                <div className="rounded-xl border bg-muted/30 p-4">
                  <p className="text-sm text-muted-foreground">Variations</p>
                  <p className="mt-1 font-medium">{rule.num_variations}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Requires approval: {rule.requires_approval ? "Yes" : "No"}
                  </p>
                </div>
                <div className="rounded-xl border bg-muted/30 p-4">
                  <p className="text-sm text-muted-foreground">Run stats</p>
                  <p className="mt-1 font-medium">{rule.run_count} total runs</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Last run: {formatDateTime(rule.last_run_at)}
                  </p>
                </div>
                <div className="rounded-xl border bg-muted/30 p-4">
                  <p className="text-sm text-muted-foreground">Failures</p>
                  <p className="mt-1 font-medium">
                    {rule.consecutive_failures} consecutive
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Timeout: {rule.approval_timeout_hours}h
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {rule.platform_targets.map((platform) => (
                  <Badge key={platform} variant="outline">
                    {platform}
                  </Badge>
                ))}
                {rule.asset_types.map((assetType) => (
                  <Badge key={`${rule.id}-${assetType}`} variant="secondary">
                    {assetType.toUpperCase()}
                  </Badge>
                ))}
                {!rule.requires_approval && rule.publish_connection_ids?.length ? (
                  <Badge variant="outline">
                    {rule.publish_connection_ids.length} publish connection
                    {rule.publish_connection_ids.length > 1 ? "s" : ""}
                  </Badge>
                ) : null}
              </div>

              {rule.days_of_week?.length ? (
                <div className="flex items-start gap-2 text-sm text-muted-foreground">
                  <Clock3 className="mt-0.5 size-4" />
                  <span>
                    {rule.cadence === "WEEKLY"
                      ? `Runs on ${rule.days_of_week
                          .map(
                            (day) =>
                              WEEKDAY_OPTIONS.find((option) => option.value === day)
                                ?.label ?? String(day)
                          )
                          .join(", ")}`
                      : `Runs on day ${rule.days_of_week.join(", ")} of the month`}
                  </span>
                </div>
              ) : null}

              {rule.last_failure_reason ? (
                <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                  {rule.last_failure_reason}
                </div>
              ) : null}
            </CardContent>
          </Card>
        ))
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <span className="flex size-14 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
              <Bot className="size-7" />
            </span>
            <div className="space-y-1">
              <h2 className="text-xl font-semibold">No autopilot schedules yet</h2>
              <p className="text-sm text-muted-foreground">
                Create one to get started.
              </p>
            </div>
            <Button onClick={onCreate}>
              <Plus className="size-4" />
              Create Schedule
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CalendarTab({
  rules,
  historyMap,
}: {
  rules: AutopilotRule[];
  historyMap: Map<number, AutopilotRunLog[]>;
}) {
  const [visibleMonth, setVisibleMonth] = useState(
    () => new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  );
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const calendarCells = useMemo(
    () => buildCalendarCells(visibleMonth, rules, historyMap),
    [historyMap, rules, visibleMonth]
  );

  const selectedCell =
    calendarCells.find((cell) => isSameDay(cell.date, selectedDate)) ??
    calendarCells[0];

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.9fr)]">
      <Card>
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-xl">Monthly schedule map</CardTitle>
            <CardDescription>
              Scheduled runs appear in primary dots, while completed, failed, and awaiting runs are color-coded from history.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() =>
                setVisibleMonth(
                  (current) => new Date(current.getFullYear(), current.getMonth() - 1, 1)
                )
              }
            >
              <ChevronLeft className="size-4" />
            </Button>
            <div className="min-w-36 text-center text-sm font-medium">
              {monthLabel(visibleMonth)}
            </div>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() =>
                setVisibleMonth(
                  (current) => new Date(current.getFullYear(), current.getMonth() + 1, 1)
                )
              }
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-7 gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {CALENDAR_WEEKDAYS.map((day) => (
              <div key={day} className="px-2 py-1 text-center">
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-2">
            {calendarCells.map((cell) => {
              const isSelected = isSameDay(cell.date, selectedDate);
              const isToday = isSameDay(cell.date, new Date());
              return (
                <button
                  key={cell.key}
                  type="button"
                  onClick={() => setSelectedDate(cell.date)}
                  className={cn(
                    "min-h-24 rounded-xl border p-2 text-left transition-colors",
                    cell.isCurrentMonth
                      ? "bg-card hover:bg-accent/40"
                      : "bg-muted/20 text-muted-foreground hover:bg-muted/40",
                    isSelected && "border-primary bg-primary/5",
                    isToday && "shadow-[inset_0_0_0_1px_theme(colors.primary.DEFAULT)]"
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">{cell.date.getDate()}</span>
                    {cell.items.length ? (
                      <span className="text-[10px] text-muted-foreground">
                        {cell.items.length}
                      </span>
                    ) : null}
                  </div>
                  <EventDots items={cell.items} />
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">
            {selectedCell ? selectedCell.date.toLocaleDateString([], { dateStyle: "full" }) : "Selected day"}
          </CardTitle>
          <CardDescription>
            Click a calendar day to inspect scheduled and completed autopilot activity.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {selectedCell?.items.length ? (
            selectedCell.items.map((item) => (
              <div key={item.key} className="rounded-xl border p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{item.title}</p>
                  <Badge
                    variant={
                      item.type === "completed"
                        ? "default"
                        : item.type === "failed"
                          ? "destructive"
                          : "outline"
                    }
                  >
                    {item.type}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {formatDateTime(item.timestamp)}
                </p>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
              No scheduled or historical autopilot activity on this day.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PerformanceTab({
  rules,
  rows,
  totalCompletedRuns,
  totalCreditsUsed,
  successRate,
  avgCreditsPerRun,
}: {
  rules: AutopilotRule[];
  rows: RulePerformanceRow[];
  totalCompletedRuns: number;
  totalCreditsUsed: number;
  successRate: number;
  avgCreditsPerRun: number;
}) {
  const maxCredits = Math.max(...rows.map((row) => row.creditsUsed), 1);

  return (
    <div className="grid gap-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="gap-1 pb-3">
            <CardDescription>Total runs completed</CardDescription>
            <CardTitle className="text-2xl">{totalCompletedRuns}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="gap-1 pb-3">
            <CardDescription>Total credits used</CardDescription>
            <CardTitle className="text-2xl">{totalCreditsUsed}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="gap-1 pb-3">
            <CardDescription>Success rate</CardDescription>
            <CardTitle className="text-2xl">{successRate.toFixed(1)}%</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="gap-1 pb-3">
            <CardDescription>Avg credits per run</CardDescription>
            <CardTitle className="text-2xl">{avgCreditsPerRun.toFixed(1)}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Per-rule performance</CardTitle>
          <CardDescription>
            Compare run reliability and credit burn across your {rules.length} autopilot schedules.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {rows.length ? (
            rows.map((row) => (
              <div key={row.ruleId} className="rounded-xl border p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-1">
                    <p className="font-medium">{truncateUrl(row.productUrl, 80)}</p>
                    <p className="text-sm text-muted-foreground break-all">
                      {row.productUrl}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">{row.totalRuns} runs</Badge>
                    <Badge variant="secondary">{row.successCount} success</Badge>
                    <Badge variant="outline">{row.failCount} failed</Badge>
                    <Badge variant="outline">{row.publishCount} published</Badge>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Credits used</span>
                      <span>{row.creditsUsed}</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div
                        className="h-2 rounded-full bg-primary"
                        style={{
                          width: `${Math.max((row.creditsUsed / maxCredits) * 100, row.creditsUsed ? 8 : 0)}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div className="grid gap-1 text-sm text-muted-foreground md:text-right">
                    <span>Awaiting approval: {row.awaitingCount}</span>
                    <span>Avg credits/run: {row.avgCreditsPerRun.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
              Performance data will appear after your schedules have started running.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AutopilotPage() {
  const { data: rules, isLoading } = useAutopilotRules();
  const { data: brandKits } = useBrandKits();
  const { data: publishConnections } = usePublishConnections();
  const { data: billingOverview } = useBillingOverview();
  const createRule = useCreateAutopilotRule();
  const updateRule = useUpdateAutopilotRule();
  const deleteRule = useDeleteAutopilotRule();
  const toggleRule = useToggleAutopilotRule();
  const runNow = useRunAutopilotNow();
  const { isConnected, lastEvent } = useAutopilotWebSocket();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<AutopilotRule | null>(null);
  const [selectedRule, setSelectedRule] = useState<AutopilotRule | null>(null);
  const [form, setForm] = useState<AutopilotFormState>(EMPTY_FORM);
  const [activeTab, setActiveTab] = useState<
    "schedules" | "calendar" | "performance"
  >("schedules");

  const brandKitOptions = useMemo(
    () => (brandKits ?? []).map((kit) => ({ id: kit.id, name: kit.name })),
    [brandKits]
  );

  const publishConnectionOptions = useMemo(
    () =>
      (publishConnections ?? []).map((connection) => ({
        id: connection.id,
        label:
          connection.page_name || connection.account_name || `${connection.platform} connection`,
        platform: connection.platform,
        isActive: connection.is_active,
      })),
    [publishConnections]
  );

  const historyRuleId = selectedRule?.id ?? 0;
  const { data: history, isLoading: historyLoading } =
    useAutopilotHistory(historyRuleId);

  const ruleIds = useMemo(() => (rules ?? []).map((rule) => rule.id), [rules]);
  const historyQueries = useAutopilotHistories(ruleIds);

  const historyMap = useMemo(() => {
    const map = new Map<number, AutopilotRunLog[]>();
    ruleIds.forEach((ruleId, index) => {
      map.set(ruleId, historyQueries[index]?.data ?? []);
    });
    return map;
  }, [historyQueries, ruleIds]);

  const performance = useMemo(
    () => aggregateRulePerformance(rules ?? [], historyMap),
    [historyMap, rules]
  );

  const creditsRemaining =
    (billingOverview?.usage.credits_limit ?? 0) +
    (billingOverview?.usage.bonus_credits ?? 0) -
    (billingOverview?.usage.credits_used ?? 0);

  const isSubmitting = createRule.isPending || updateRule.isPending;
  const isMutating =
    isSubmitting || deleteRule.isPending || toggleRule.isPending || runNow.isPending;

  const openCreateDialog = () => {
    setEditingRule(null);
    setForm(EMPTY_FORM);
    setDialogOpen(true);
  };

  const openEditDialog = (rule: AutopilotRule) => {
    setEditingRule(rule);
    setForm(formFromRule(rule));
    setDialogOpen(true);
  };

  const openHistoryDialog = (rule: AutopilotRule) => {
    setSelectedRule(rule);
    setHistoryOpen(true);
  };

  const handleSubmit = async () => {
    let payload: AutopilotRuleCreate;

    try {
      payload = buildPayload(form);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Invalid schedule details"
      );
      return;
    }

    try {
      if (editingRule) {
        await updateRule.mutateAsync({ ruleId: editingRule.id, data: payload });
        toast.success("Autopilot schedule updated");
      } else {
        await createRule.mutateAsync(payload);
        toast.success("Autopilot schedule created");
      }
      setDialogOpen(false);
      setEditingRule(null);
      setForm(EMPTY_FORM);
    } catch {
      toast.error(
        editingRule
          ? "Failed to update autopilot schedule"
          : "Failed to create autopilot schedule"
      );
    }
  };

  const handleDelete = async (ruleId: number) => {
    try {
      await deleteRule.mutateAsync(ruleId);
      toast.success("Autopilot schedule deleted");
      if (selectedRule?.id === ruleId) {
        setHistoryOpen(false);
        setSelectedRule(null);
      }
    } catch {
      toast.error("Failed to delete autopilot schedule");
    }
  };

  const handleToggle = async (ruleId: number) => {
    try {
      await toggleRule.mutateAsync(ruleId);
      toast.success("Autopilot schedule updated");
    } catch {
      toast.error("Failed to toggle autopilot schedule");
    }
  };

  const handleRunNow = async (ruleId: number) => {
    try {
      await runNow.mutateAsync(ruleId);
      toast.success("Autopilot run started");
    } catch {
      toast.error("Failed to run autopilot now");
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
              <Bot className="size-5" />
            </span>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">Autopilot</h1>
              <p className="text-sm text-muted-foreground md:text-base">
                Automatically generate ad creatives on a schedule.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2 py-1",
                isConnected
                  ? "border-emerald-200 bg-emerald-500/10 text-emerald-700 dark:border-emerald-500/30 dark:text-emerald-300"
                  : "border-border bg-muted text-muted-foreground"
              )}
            >
              <span
                className={cn(
                  "size-2 rounded-full",
                  isConnected ? "bg-emerald-500" : "bg-muted-foreground"
                )}
              />
              {isConnected ? "Live autopilot events connected" : "Waiting for live autopilot events"}
            </span>
            {lastEvent ? (
              <span>Last event: {lastEvent.event.replaceAll("_", " ")}</span>
            ) : null}
          </div>
        </div>

        <Dialog
          open={dialogOpen}
          onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) {
              setEditingRule(null);
              setForm(EMPTY_FORM);
            }
          }}
        >
          <DialogTrigger asChild>
            <Button onClick={openCreateDialog}>
              <Plus className="size-4" />
              Create Schedule
            </Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                {editingRule ? "Edit autopilot schedule" : "Create autopilot schedule"}
              </DialogTitle>
              <DialogDescription>
                Set the cadence, output mix, approval flow, and publish targets for recurring creative generation.
              </DialogDescription>
            </DialogHeader>

            <RuleFormFields
              form={form}
              onChange={(updater) => setForm((current) => updater(current))}
              brandKitOptions={brandKitOptions}
              publishConnections={publishConnectionOptions}
            />

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Saving...
                  </>
                ) : editingRule ? (
                  "Save Changes"
                ) : (
                  "Create Schedule"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {creditsRemaining < 50 ? (
        <Card className="border-amber-200 bg-amber-500/10 dark:border-amber-500/30">
          <CardContent className="flex flex-col gap-3 px-6 py-5 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 rounded-full bg-amber-500/20 p-2 text-amber-700 dark:text-amber-300">
                <TriangleAlert className="size-4" />
              </span>
              <div>
                <p className="font-medium text-amber-900 dark:text-amber-100">
                  Running low on credits! Get 50 credits for $4.99.
                </p>
                <p className="text-sm text-amber-800/80 dark:text-amber-200/80">
                  You have {Math.max(creditsRemaining, 0)} credits remaining across subscription and bonus balance.
                </p>
              </div>
            </div>
            <Button asChild variant="outline" className="border-amber-300 bg-background/80">
              <Link href="/settings/billing">Top up credits</Link>
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="gap-1 pb-3">
            <CardDescription>Total schedules</CardDescription>
            <CardTitle className="text-2xl">
              {isLoading ? <Skeleton className="h-8 w-16" /> : rules?.length ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="gap-1 pb-3">
            <CardDescription>Enabled</CardDescription>
            <CardTitle className="text-2xl">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                rules?.filter((rule) => rule.enabled).length ?? 0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="gap-1 pb-3">
            <CardDescription>Total runs</CardDescription>
            <CardTitle className="text-2xl">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                rules?.reduce((total, rule) => total + rule.run_count, 0) ?? 0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2 rounded-xl border bg-muted/20 p-2">
        {TAB_OPTIONS.map((tab) => {
          const isActive = activeTab === tab.value;
          return (
            <button
              key={tab.value}
              type="button"
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-background/70 hover:text-foreground"
              )}
            >
              {tab.value === "schedules" ? <Sparkles className="size-4" /> : null}
              {tab.value === "calendar" ? <CalendarDays className="size-4" /> : null}
              {tab.value === "performance" ? <CheckCircle2 className="size-4" /> : null}
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === "schedules" ? (
        <SchedulesTab
          rules={rules}
          isLoading={isLoading}
          onEdit={openEditDialog}
          onDelete={handleDelete}
          onToggle={handleToggle}
          onRunNow={handleRunNow}
          onHistory={openHistoryDialog}
          onCreate={openCreateDialog}
          isMutating={isMutating}
        />
      ) : null}

      {activeTab === "calendar" ? (
        <CalendarTab rules={rules ?? []} historyMap={historyMap} />
      ) : null}

      {activeTab === "performance" ? (
        <PerformanceTab
          rules={rules ?? []}
          rows={performance.rows}
          totalCompletedRuns={performance.totalCompletedRuns}
          totalCreditsUsed={performance.totalCreditsUsed}
          successRate={performance.successRate}
          avgCreditsPerRun={performance.avgCreditsPerRun}
        />
      ) : null}

      <Dialog
        open={historyOpen}
        onOpenChange={(open) => {
          setHistoryOpen(open);
          if (!open) {
            setSelectedRule(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>Autopilot run history</DialogTitle>
            <DialogDescription>
              {selectedRule
                ? `Recent runs for ${truncateUrl(selectedRule.product_url, 80)}`
                : "Recent autopilot activity"}
            </DialogDescription>
          </DialogHeader>

          <HistoryContent logs={history} isLoading={historyLoading} />

          <DialogFooter>
            <Button variant="outline" onClick={() => setHistoryOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
