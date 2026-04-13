"use client";

import { useState, useMemo } from "react";
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useCampaigns } from "@/hooks/use-campaigns";
import {
  useCalendarView,
  useCreateScheduledPost,
  useCancelScheduledPost,
  useReschedulePost,
} from "@/hooks/use-scheduling";
import type {
  ScheduledPost,
  ScheduleStatus,
  ScheduleRecurrence,
} from "@/types";

const STATUS_COLOR: Record<ScheduleStatus, string> = {
  PENDING: "bg-yellow-400",
  SCHEDULED: "bg-blue-500",
  PUBLISHING: "bg-blue-400",
  PUBLISHED: "bg-green-500",
  FAILED: "bg-red-500",
  CANCELLED: "bg-gray-400",
};

const STATUS_VARIANT: Record<
  ScheduleStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  PENDING: "outline",
  SCHEDULED: "secondary",
  PUBLISHING: "secondary",
  PUBLISHED: "default",
  FAILED: "destructive",
  CANCELLED: "outline",
};

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const PLATFORMS = ["FACEBOOK", "INSTAGRAM", "GOOGLE_ADS", "TIKTOK", "NAVER"];

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function SchedulingPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<ScheduleStatus | "ALL">(
    "ALL"
  );
  const [platformFilter, setPlatformFilter] = useState<string>("ALL");
  const [dialogOpen, setDialogOpen] = useState(false);

  const [formCampaignId, setFormCampaignId] = useState("");
  const [formPlatform, setFormPlatform] = useState("FACEBOOK");
  const [formDatetime, setFormDatetime] = useState("");
  const [formRecurrence, setFormRecurrence] = useState<ScheduleRecurrence>("NONE");
  const [formCopyText, setFormCopyText] = useState("");

  const { data: calendar, isLoading: calendarLoading } = useCalendarView(
    month,
    year
  );
  const { data: campaigns } = useCampaigns();
  const createPost = useCreateScheduledPost();
  const cancelPost = useCancelScheduledPost();
  const reschedulePost = useReschedulePost();

  const filteredPosts = useMemo(() => {
    if (!calendar) return [];
    return calendar.posts.filter((p) => {
      if (statusFilter !== "ALL" && p.status !== statusFilter) return false;
      if (platformFilter !== "ALL" && p.platform !== platformFilter)
        return false;
      return true;
    });
  }, [calendar, statusFilter, platformFilter]);

  const postsByDay = useMemo(() => {
    const map: Record<number, ScheduledPost[]> = {};
    for (const post of filteredPosts) {
      const day = new Date(post.scheduled_at).getDate();
      if (!map[day]) map[day] = [];
      map[day].push(post);
    }
    return map;
  }, [filteredPosts]);

  const calendarDays = useMemo(() => {
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const cells: (number | null)[] = [];
    for (let i = 0; i < firstDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    return cells;
  }, [month, year]);

  const selectedDayPosts = useMemo(() => {
    if (selectedDay === null) return [];
    return postsByDay[selectedDay] || [];
  }, [selectedDay, postsByDay]);

  const handlePrevMonth = () => {
    if (month === 1) {
      setMonth(12);
      setYear(year - 1);
    } else {
      setMonth(month - 1);
    }
    setSelectedDay(null);
  };

  const handleNextMonth = () => {
    if (month === 12) {
      setMonth(1);
      setYear(year + 1);
    } else {
      setMonth(month + 1);
    }
    setSelectedDay(null);
  };

  const monthLabel = new Date(year, month - 1).toLocaleString("default", {
    month: "long",
    year: "numeric",
  });

  const handleCreate = async () => {
    if (!formCampaignId || !formDatetime) {
      toast.error("Campaign and date/time are required");
      return;
    }
    try {
      await createPost.mutateAsync({
        campaign_id: Number(formCampaignId),
        platform: formPlatform,
        scheduled_at: new Date(formDatetime).toISOString(),
        recurrence: formRecurrence,
        copy_text: formCopyText || undefined,
      });
      toast.success("Post scheduled");
      setDialogOpen(false);
      setFormCampaignId("");
      setFormPlatform("FACEBOOK");
      setFormDatetime("");
      setFormRecurrence("NONE");
      setFormCopyText("");
    } catch {
      toast.error("Failed to schedule post");
    }
  };

  const handleCancel = async (postId: number) => {
    try {
      await cancelPost.mutateAsync(postId);
      toast.success("Post cancelled");
    } catch {
      toast.error("Failed to cancel post");
    }
  };

  const handleReschedule = async (postId: number) => {
    const input = prompt("Enter new date/time (YYYY-MM-DDTHH:mm):");
    if (!input) return;
    try {
      await reschedulePost.mutateAsync({
        postId,
        scheduled_at: new Date(input).toISOString(),
      });
      toast.success("Post rescheduled");
    } catch {
      toast.error("Failed to reschedule");
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Scheduling</h1>
          <p className="text-muted-foreground">
            Schedule and manage your campaign posts
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>Schedule Post</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Schedule a Post</DialogTitle>
              <DialogDescription>
                Choose a campaign and set the publish date
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Campaign</Label>
                <Select
                  value={formCampaignId}
                  onValueChange={setFormCampaignId}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select campaign" />
                  </SelectTrigger>
                  <SelectContent>
                    {campaigns?.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        {c.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Platform</Label>
                <Select value={formPlatform} onValueChange={setFormPlatform}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PLATFORMS.map((p) => (
                      <SelectItem key={p} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Date &amp; Time</Label>
                <Input
                  type="datetime-local"
                  value={formDatetime}
                  onChange={(e) => setFormDatetime(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Recurrence</Label>
                <Select
                  value={formRecurrence}
                  onValueChange={(v) =>
                    setFormRecurrence(v as ScheduleRecurrence)
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NONE">None</SelectItem>
                    <SelectItem value="DAILY">Daily</SelectItem>
                    <SelectItem value="WEEKLY">Weekly</SelectItem>
                    <SelectItem value="MONTHLY">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Copy Text</Label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  placeholder="Enter copy text for the post..."
                  value={formCopyText}
                  onChange={(e) => setFormCopyText(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleCreate}
                disabled={createPost.isPending}
                className="w-full"
              >
                {createPost.isPending ? "Scheduling..." : "Schedule"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Scheduled</CardDescription>
            <CardTitle className="text-2xl">
              {calendarLoading ? (
                <Skeleton className="h-8 w-12" />
              ) : (
                calendar?.total_scheduled ?? 0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Published</CardDescription>
            <CardTitle className="text-2xl">
              {calendarLoading ? (
                <Skeleton className="h-8 w-12" />
              ) : (
                calendar?.total_published ?? 0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Failed</CardDescription>
            <CardTitle className="text-2xl text-destructive">
              {calendarLoading ? (
                <Skeleton className="h-8 w-12" />
              ) : (
                calendar?.total_failed ?? 0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={handlePrevMonth}>
                &larr;
              </Button>
              <CardTitle>{monthLabel}</CardTitle>
              <Button variant="outline" size="sm" onClick={handleNextMonth}>
                &rarr;
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value={statusFilter}
                onValueChange={(v) =>
                  setStatusFilter(v as ScheduleStatus | "ALL")
                }
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Statuses</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="SCHEDULED">Scheduled</SelectItem>
                  <SelectItem value="PUBLISHED">Published</SelectItem>
                  <SelectItem value="FAILED">Failed</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={platformFilter}
                onValueChange={setPlatformFilter}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Platform" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Platforms</SelectItem>
                  {PLATFORMS.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {calendarLoading ? (
            <Skeleton className="h-[400px] w-full rounded-xl" />
          ) : (
            <div className="grid grid-cols-7 gap-px bg-muted rounded-lg overflow-hidden">
              {DAYS.map((day) => (
                <div
                  key={day}
                  className="bg-background p-2 text-center text-sm font-medium text-muted-foreground"
                >
                  {day}
                </div>
              ))}
              {calendarDays.map((day, i) => (
                <button
                  key={i}
                  type="button"
                  disabled={day === null}
                  onClick={() => day !== null && setSelectedDay(day)}
                  className={`bg-background p-2 min-h-[80px] text-left transition-colors ${
                    day !== null ? "hover:bg-muted/50 cursor-pointer" : ""
                  } ${
                    selectedDay === day
                      ? "ring-2 ring-primary ring-inset"
                      : ""
                  }`}
                >
                  {day !== null && (
                    <>
                      <span className="text-sm font-medium">{day}</span>
                      {postsByDay[day] && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {postsByDay[day].map((post) => (
                            <span
                              key={post.id}
                              className={`inline-block h-2 w-2 rounded-full ${STATUS_COLOR[post.status]}`}
                              title={`${post.platform} - ${post.status}`}
                            />
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedDay !== null && (
        <Card>
          <CardHeader>
            <CardTitle>
              {new Date(year, month - 1, selectedDay).toLocaleDateString(
                "default",
                { weekday: "long", month: "long", day: "numeric", year: "numeric" }
              )}
            </CardTitle>
            <CardDescription>
              {selectedDayPosts.length} post
              {selectedDayPosts.length !== 1 ? "s" : ""}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedDayPosts.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No posts scheduled for this day
              </p>
            ) : (
              <div className="space-y-3">
                {selectedDayPosts.map((post) => {
                  const campaign = campaigns?.find(
                    (c) => c.id === post.campaign_id
                  );
                  return (
                    <div
                      key={post.id}
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {campaign?.title ?? `Campaign #${post.campaign_id}`}
                          </span>
                          <Badge variant="secondary">{post.platform}</Badge>
                          <Badge variant={STATUS_VARIANT[post.status]}>
                            {post.status}
                          </Badge>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {formatTime(post.scheduled_at)}
                          {post.recurrence !== "NONE" &&
                            ` · Repeats ${post.recurrence.toLowerCase()}`}
                        </span>
                        {post.copy_text && (
                          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                            {post.copy_text}
                          </p>
                        )}
                        {post.error && (
                          <p className="text-sm text-destructive mt-1">
                            {post.error}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {(post.status === "PENDING" ||
                          post.status === "SCHEDULED" ||
                          post.status === "FAILED") && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleReschedule(post.id)}
                            disabled={reschedulePost.isPending}
                          >
                            Reschedule
                          </Button>
                        )}
                        {post.status !== "CANCELLED" &&
                          post.status !== "PUBLISHED" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCancel(post.id)}
                              disabled={cancelPost.isPending}
                            >
                              Cancel
                            </Button>
                          )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
