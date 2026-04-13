"use client";

import { useState } from "react";
import { Search, LayoutGrid, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTemplates } from "@/hooks/use-templates";
import type { Template, TemplateIndustry, TemplatePlatform } from "@/types";

const INDUSTRY_LABELS: Record<TemplateIndustry, string> = {
  BEAUTY: "Beauty",
  HEALTH: "Health",
  FOOD: "Food",
  IT_SAAS: "IT / SaaS",
  FASHION: "Fashion",
  EDUCATION: "Education",
  REAL_ESTATE: "Real Estate",
  FINANCE: "Finance",
  TRAVEL: "Travel",
  PET: "Pet",
};

const PLATFORM_LABELS: Record<TemplatePlatform, string> = {
  INSTAGRAM: "Instagram",
  FACEBOOK: "Facebook",
  GOOGLE_ADS: "Google Ads",
  NAVER: "Naver",
  TIKTOK: "TikTok",
};

const LAYOUT_LABELS: Record<string, string> = {
  SINGLE_IMAGE: "Single Image",
  CAROUSEL: "Carousel",
  VIDEO_COVER: "Video Cover",
  TEXT_OVERLAY: "Text Overlay",
  SPLIT_VIEW: "Split View",
  PRODUCT_HERO: "Product Hero",
};

const PLATFORM_COLORS: Record<TemplatePlatform, string> = {
  INSTAGRAM: "bg-pink-100 text-pink-700 dark:bg-pink-950/40 dark:text-pink-400",
  FACEBOOK: "bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400",
  GOOGLE_ADS: "bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400",
  NAVER: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400",
  TIKTOK: "bg-violet-100 text-violet-700 dark:bg-violet-950/40 dark:text-violet-400",
};

const ALL_VALUE = "__all__";

export default function TemplatesPage() {
  const [industryFilter, setIndustryFilter] = useState<TemplateIndustry | undefined>();
  const [platformFilter, setPlatformFilter] = useState<TemplatePlatform | undefined>();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: templates, isLoading, error } = useTemplates({
    industry: industryFilter,
    platform: platformFilter,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-9 w-56" />
          <div className="flex gap-3">
            <Skeleton className="h-9 w-36" />
            <Skeleton className="h-9 w-36" />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-3">
                <Skeleton className="h-5 w-40" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <div className="flex gap-2">
                  <Skeleton className="h-5 w-16" />
                  <Skeleton className="h-5 w-20" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">Failed to load templates</h2>
          <p className="text-muted-foreground">Something went wrong while fetching templates.</p>
        </div>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Templates</h1>
          <p className="text-muted-foreground">Browse ad templates by industry and platform</p>
        </div>
        <div className="flex gap-3">
          <Select
            value={industryFilter ?? ALL_VALUE}
            onValueChange={(v) => setIndustryFilter(v === ALL_VALUE ? undefined : v as TemplateIndustry)}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="All Industries" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_VALUE}>All Industries</SelectItem>
              {(Object.keys(INDUSTRY_LABELS) as TemplateIndustry[]).map((key) => (
                <SelectItem key={key} value={key}>
                  {INDUSTRY_LABELS[key]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={platformFilter ?? ALL_VALUE}
            onValueChange={(v) => setPlatformFilter(v === ALL_VALUE ? undefined : v as TemplatePlatform)}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="All Platforms" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_VALUE}>All Platforms</SelectItem>
              {(Object.keys(PLATFORM_LABELS) as TemplatePlatform[]).map((key) => (
                <SelectItem key={key} value={key}>
                  {PLATFORM_LABELS[key]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {templates && templates.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Search className="h-10 w-10 text-muted-foreground mb-4" />
          <h3 className="font-medium mb-1">No templates found</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Try changing your filter criteria
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setIndustryFilter(undefined);
              setPlatformFilter(undefined);
            }}
          >
            Clear Filters
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {templates?.map((template: Template) => (
            <Card
              key={template.id}
              className={`cursor-pointer transition-all hover:shadow-md ${
                selectedId === template.id
                  ? "ring-2 ring-amber-500 shadow-md"
                  : ""
              }`}
              onClick={() => setSelectedId(selectedId === template.id ? null : template.id)}
            >
              <CardHeader className="pb-3">
                <CardTitle className="text-base leading-snug">
                  {template.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {template.description}
                </p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">
                    {INDUSTRY_LABELS[template.industry]}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={PLATFORM_COLORS[template.platform]}
                  >
                    {PLATFORM_LABELS[template.platform]}
                  </Badge>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <LayoutGrid className="h-3.5 w-3.5" />
                  {LAYOUT_LABELS[template.layout] ?? template.layout}
                </div>
                {selectedId === template.id && template.copy_template && (
                  <div className="mt-3 rounded-lg border bg-zinc-50 p-3 text-xs dark:bg-zinc-900 space-y-1.5">
                    {template.copy_template.headline && (
                      <p><span className="font-medium">Headline:</span> {template.copy_template.headline}</p>
                    )}
                    {template.copy_template.body && (
                      <p><span className="font-medium">Body:</span> {template.copy_template.body}</p>
                    )}
                    {template.copy_template.cta && (
                      <p><span className="font-medium">CTA:</span> {template.copy_template.cta}</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
