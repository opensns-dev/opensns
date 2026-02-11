"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Trash2, ExternalLink, Repeat } from "lucide-react";
import { toast } from "sonner";
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

const ALL_PLATFORMS: { value: ContentPlatform; label: string }[] = [
  { value: "NAVER_BLOG", label: "네이버 블로그" },
  { value: "X_THREAD", label: "X 스레드" },
  { value: "INSTAGRAM", label: "인스타그램" },
  { value: "BRUNCH", label: "브런치 스토리" },
  { value: "NAVER_POST", label: "네이버 포스트" },
  { value: "SHORT_CLIP", label: "숏폼 클립" },
];

const TONE_OPTIONS: { value: ToneStyle; label: string }[] = [
  { value: "FRIENDLY", label: "존댓말/친근" },
  { value: "FORMAL", label: "존댓말/전문적" },
  { value: "CASUAL", label: "반말/캐주얼" },
];

const STATUS_CONFIG: Record<RepurposeStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  PENDING: { label: "대기 중", variant: "secondary" },
  EXTRACTING: { label: "오디오 추출 중", variant: "default" },
  TRANSCRIBING: { label: "음성 변환 중", variant: "default" },
  GENERATING: { label: "콘텐츠 생성 중", variant: "outline" },
  COMPLETED: { label: "완료", variant: "default" },
  FAILED: { label: "실패", variant: "destructive" },
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
  const [url, setUrl] = useState("");
  const [tone, setTone] = useState<ToneStyle>("FRIENDLY");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Set<ContentPlatform>>(
    new Set(ALL_PLATFORMS.map((p) => p.value))
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
      toast.success("리퍼포징 시작", { description: "콘텐츠 생성이 시작되었습니다." });
      router.push(`/repurpose/${job.id}`);
    } catch {
      toast.error("리퍼포징 실패", { description: "YouTube URL을 확인해주세요." });
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteJob.mutateAsync(id);
      toast.success("삭제 완료");
    } catch {
      toast.error("삭제 실패");
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">콘텐츠 리퍼포징</h1>
        <p className="text-muted-foreground mt-1">
          유튜브 영상을 다양한 플랫폼 콘텐츠로 자동 변환
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">새 리퍼포징</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="youtube-url">YouTube URL</Label>
            <Input
              id="youtube-url"
              placeholder="https://youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>톤앤매너</Label>
            <Select value={tone} onValueChange={(v) => setTone(v as ToneStyle)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TONE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>출력 플랫폼</Label>
            <div className="flex flex-wrap gap-2">
              {ALL_PLATFORMS.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => togglePlatform(p.value)}
                  className={`rounded-full px-3 py-1 text-sm border transition-colors ${
                    selectedPlatforms.has(p.value)
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-muted-foreground border-border hover:border-primary/50"
                  }`}
                >
                  {p.label}
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
                처리 중...
              </>
            ) : (
              <>
                <Repeat className="mr-2 h-4 w-4" />
                리퍼포징 시작
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-xl font-semibold mb-3">이전 작업</h2>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : jobs && jobs.length > 0 ? (
          <div className="space-y-2">
            {jobs.map((job) => {
              const config = STATUS_CONFIG[job.status];
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
                      <Badge variant={config.variant}>{config.label}</Badge>
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
              아직 리퍼포징 작업이 없습니다
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
