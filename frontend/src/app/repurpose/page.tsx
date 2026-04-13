"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Trash2, ExternalLink, Repeat } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useRepurposeJobs,
  useCreateRepurposeJob,
  useDeleteRepurposeJob,
} from "@/hooks/use-repurpose";
import type { ContentPlatform, ToneStyle, RepurposeStatus } from "@/types";

const PLATFORM_KEYS: Record<ContentPlatform, string> = {
  NAVER_BLOG: "naverBlog",
  X_THREAD: "xThread",
  INSTAGRAM: "instagram",
  BRUNCH: "brunch",
  NAVER_POST: "naverPost",
  SHORT_CLIP: "shortClip",
};

const ALL_PLATFORMS: ContentPlatform[] = [
  "NAVER_BLOG",
  "X_THREAD",
  "INSTAGRAM",
  "BRUNCH",
  "NAVER_POST",
  "SHORT_CLIP",
];

const TONE_KEYS: Record<ToneStyle, string> = {
  FRIENDLY: "friendly",
  FORMAL: "formal",
  CASUAL: "casual",
};

const TONE_OPTIONS: ToneStyle[] = ["FRIENDLY", "FORMAL", "CASUAL"];

const STATUS_VARIANTS: Record<RepurposeStatus, "default" | "secondary" | "destructive" | "outline"> = {
  PENDING: "secondary",
  EXTRACTING: "default",
  TRANSCRIBING: "default",
  GENERATING: "outline",
  COMPLETED: "default",
  FAILED: "destructive",
};

const STATUS_KEYS: Record<RepurposeStatus, string> = {
  PENDING: "pending",
  EXTRACTING: "extracting",
  TRANSCRIBING: "transcribing",
  GENERATING: "generating",
  COMPLETED: "completed",
  FAILED: "failed",
};

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function RepurposePage() {
  const router = useRouter();
  const t = useTranslations("repurpose");
  const tc = useTranslations("common");
  const [url, setUrl] = useState("");
  const [tone, setTone] = useState<ToneStyle>("FRIENDLY");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Set<ContentPlatform>>(
    new Set(ALL_PLATFORMS)
  );

  const { data: jobs, isLoading } = useRepurposeJobs();
  const createJob = useCreateRepurposeJob();
  const deleteJob = useDeleteRepurposeJob();

  const togglePlatform = (platform: ContentPlatform) => {
    setSelectedPlatforms((prev) => {
      const next = new Set(prev);
      if (next.has(platform)) {
        next.delete(platform);
      } else {
        next.add(platform);
      }
      return next;
    });
  };

  const handleCreate = async () => {
    if (!url.trim() || selectedPlatforms.size === 0) return;

    try {
      const job = await createJob.mutateAsync({
        youtube_url: url.trim(),
        tone_style: tone,
        target_platforms: Array.from(selectedPlatforms),
      });
      setUrl("");
      toast.success(t("toast.startSuccess"), { description: t("toast.startSuccessDesc") });
      router.push(`/repurpose/${job.id}`);
    } catch {
      toast.error(t("toast.startError"), { description: t("toast.startErrorDesc") });
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteJob.mutateAsync(id);
      toast.success(t("toast.deleteSuccess"));
    } catch {
      toast.error(t("toast.deleteError"));
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-muted-foreground mt-1">
          {t("subtitle")}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("newRepurpose")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="youtube-url">{t("youtubeUrl")}</Label>
            <Input
              id="youtube-url"
              placeholder="https://youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>{t("toneAndManner")}</Label>
            <Select value={tone} onValueChange={(v) => setTone(v as ToneStyle)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TONE_OPTIONS.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {t(`tones.${TONE_KEYS[opt]}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>{t("outputPlatforms")}</Label>
            <div className="flex flex-wrap gap-2">
              {ALL_PLATFORMS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => togglePlatform(p)}
                  className={`rounded-full px-3 py-1 text-sm border transition-colors ${
                    selectedPlatforms.has(p)
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-muted-foreground border-border hover:border-primary/50"
                  }`}
                >
                  {t(`platforms.${PLATFORM_KEYS[p]}`)}
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleCreate}
            disabled={createJob.isPending || !url.trim() || selectedPlatforms.size === 0}
          >
            {createJob.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {tc("processing")}
              </>
            ) : (
              <>
                <Repeat className="mr-2 h-4 w-4" />
                {t("startRepurpose")}
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-xl font-semibold mb-3">{t("previousJobs")}</h2>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : jobs && jobs.length > 0 ? (
          <div className="space-y-2">
            {jobs.map((job) => {
              const variant = STATUS_VARIANTS[job.status];
              const statusKey = STATUS_KEYS[job.status];
              return (
                <div
                  key={job.id}
                  className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/50 transition-colors"
                >
                  <Link
                    href={`/repurpose/${job.id}`}
                    className="flex-1 min-w-0"
                  >
                    <p className="font-medium truncate">
                      {job.video_title || job.youtube_url}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant={variant}>{t(`status.${statusKey}`)}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(job.created_at)}
                      </span>
                    </div>
                  </Link>
                  <div className="flex items-center gap-2 ml-4">
                    <Button variant="ghost" size="sm" asChild>
                      <a
                        href={job.youtube_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:text-red-600"
                      onClick={() => handleDelete(job.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Repeat className="h-8 w-8 text-muted-foreground mb-3" />
            <p className="text-muted-foreground">
              {t("noJobs")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
