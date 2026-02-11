"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Copy, ChevronDown, ChevronUp, Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useRepurposeJob, useRepurposeContents } from "@/hooks/use-repurpose";
import type { RepurposeStatus, ContentPlatform } from "@/types";

const STATUS_CONFIG: Record<
  RepurposeStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  PENDING: { label: "대기 중", variant: "secondary" },
  EXTRACTING: { label: "오디오 추출 중", variant: "default" },
  TRANSCRIBING: { label: "음성 변환 중", variant: "default" },
  GENERATING: { label: "콘텐츠 생성 중", variant: "outline" },
  COMPLETED: { label: "완료", variant: "default" },
  FAILED: { label: "실패", variant: "destructive" },
};

const PLATFORM_LABELS: Record<ContentPlatform, string> = {
  NAVER_BLOG: "네이버 블로그",
  X_THREAD: "X 스레드",
  INSTAGRAM: "인스타그램",
  BRUNCH: "브런치 스토리",
  NAVER_POST: "네이버 포스트",
  SHORT_CLIP: "숏폼 클립 추천",
};

const PROGRESS_STEPS: RepurposeStatus[] = ["EXTRACTING", "TRANSCRIBING", "GENERATING"];

function getProgressPercent(status: RepurposeStatus): number {
  const idx = PROGRESS_STEPS.indexOf(status);
  if (status === "COMPLETED") return 100;
  if (status === "FAILED") return 0;
  if (idx === -1) return 0;
  return ((idx + 1) / (PROGRESS_STEPS.length + 1)) * 100;
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}시간 ${m}분`;
  if (m > 0) return `${m}분 ${s}초`;
  return `${s}초`;
}

export default function RepurposeDetailPage() {
  const params = useParams();
  const jobId = Number(params.id);
  const [showTranscript, setShowTranscript] = useState(false);

  const { data: job, isLoading: jobLoading } = useRepurposeJob(jobId);
  const { data: contents, isLoading: contentsLoading } = useRepurposeContents(
    job?.status === "COMPLETED" ? jobId : 0
  );

  const copyToClipboard = async (text: string, platform: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${platform} 콘텐츠가 복사되었습니다`);
    } catch {
      toast.error("복사 실패");
    }
  };

  if (jobLoading) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <p className="text-muted-foreground">작업을 찾을 수 없습니다.</p>
        <Button variant="outline" asChild>
          <Link href="/repurpose">
            <ArrowLeft className="mr-2 h-4 w-4" />
            돌아가기
          </Link>
        </Button>
      </div>
    );
  }

  const config = STATUS_CONFIG[job.status];
  const isProcessing = ["EXTRACTING", "TRANSCRIBING", "GENERATING"].includes(job.status);

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/repurpose">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="text-2xl font-bold truncate">
          {job.video_title || "리퍼포징 결과"}
        </h1>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <Badge variant={config.variant}>{config.label}</Badge>
            <a
              href={job.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline flex items-center gap-1"
            >
              원본 영상 <ExternalLink className="h-3 w-3" />
            </a>
            {job.video_duration && (
              <span className="text-sm text-muted-foreground">
                {formatDuration(job.video_duration)}
              </span>
            )}
            <span className="text-sm text-muted-foreground">
              {new Date(job.created_at).toLocaleDateString("ko-KR")}
            </span>
          </div>

          {isProcessing && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                {config.label}...
              </div>
              <Progress value={getProgressPercent(job.status)} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>오디오 추출</span>
                <span>음성 변환</span>
                <span>콘텐츠 생성</span>
                <span>완료</span>
              </div>
            </div>
          )}

          {job.status === "FAILED" && job.error && (
            <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
              {job.error}
            </div>
          )}
        </CardContent>
      </Card>

      {job.summary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">요약</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm whitespace-pre-wrap">{job.summary}</p>
            {job.key_points && job.key_points.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-1">핵심 포인트</p>
                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                  {job.key_points.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {job.transcript && (
        <Card>
          <CardHeader>
            <button
              onClick={() => setShowTranscript(!showTranscript)}
              className="flex items-center justify-between w-full text-left"
            >
              <CardTitle className="text-lg">스크립트</CardTitle>
              {showTranscript ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
          </CardHeader>
          {showTranscript && (
            <CardContent>
              <div className="relative">
                <Button
                  variant="outline"
                  size="sm"
                  className="absolute top-0 right-0"
                  onClick={() => copyToClipboard(job.transcript!, "스크립트")}
                >
                  <Copy className="h-3 w-3 mr-1" />
                  복사
                </Button>
                <p className="text-sm whitespace-pre-wrap max-h-96 overflow-y-auto pr-20">
                  {job.transcript}
                </p>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {job.status === "COMPLETED" && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">생성된 콘텐츠</h2>
          {contentsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-40 w-full" />
              ))}
            </div>
          ) : contents && contents.length > 0 ? (
            contents.map((content) => {
              const platformLabel =
                PLATFORM_LABELS[content.platform] || content.platform;
              const metadata = content.content_metadata || {};
              const hashtags = metadata.hashtags as string[] | undefined;
              const tags = metadata.tags as string[] | undefined;
              const clips = metadata.clips as Array<Record<string, unknown>> | undefined;

              return (
                <Card key={content.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{platformLabel}</CardTitle>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          copyToClipboard(content.content, platformLabel)
                        }
                      >
                        <Copy className="h-3 w-3 mr-1" />
                        복사
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="whitespace-pre-wrap text-sm bg-muted/50 rounded-md p-4 max-h-96 overflow-y-auto">
                      {content.content}
                    </div>

                    {hashtags && hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {hashtags.map((tag, i) => (
                          <span
                            key={i}
                            className="text-xs text-blue-600 bg-blue-50 dark:bg-blue-900/20 rounded-full px-2 py-0.5"
                          >
                            #{tag.replace(/^#/, "")}
                          </span>
                        ))}
                      </div>
                    )}

                    {tags && tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {tags.map((tag, i) => (
                          <span
                            key={i}
                            className="text-xs bg-gray-100 dark:bg-gray-800 rounded-full px-2 py-0.5"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {clips && clips.length > 0 && (
                      <div className="text-xs text-muted-foreground">
                        {clips.length}개 클립 추천
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })
          ) : (
            <p className="text-muted-foreground text-sm">
              생성된 콘텐츠가 없습니다.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
