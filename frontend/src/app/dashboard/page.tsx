"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Megaphone, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Loader2, 
  Plus,
  ArrowRight,
  ImageIcon,
  Video,
  FileText,
  Sparkles
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useCampaigns, useCreateCampaign } from "@/hooks/use-campaigns";
import { getStatusVariant } from "@/lib/utils";
import { toast } from "sonner";
import type { Campaign } from "@/types";

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function DashboardPage() {
  const router = useRouter();
  const { data: campaigns, isLoading } = useCampaigns();
  const createCampaign = useCreateCampaign();
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [productUrl, setProductUrl] = useState("");

  const handleCreate = async () => {
    if (!title.trim() || !productUrl.trim()) return;
    try {
      const campaign = await createCampaign.mutateAsync({
        title,
        product_url: productUrl,
      });
      setTitle("");
      setProductUrl("");
      setIsOpen(false);
      toast.success("Campaign created", {
        description: "Your campaign is now being processed.",
      });
      router.push(`/campaigns/view?id=${campaign.id}`);
    } catch {
      toast.error("Failed to create campaign");
    }
  };

  const stats = campaigns ? {
    total: campaigns.length,
    completed: campaigns.filter(c => c.status === "COMPLETED").length,
    inProgress: campaigns.filter(c => ["PENDING", "RESEARCHING", "GENERATING", "AWAITING_APPROVAL"].includes(c.status)).length,
    failed: campaigns.filter(c => c.status === "FAILED").length,
  } : { total: 0, completed: 0, inProgress: 0, failed: 0 };

  const recentCampaigns = campaigns?.slice(0, 5) || [];

  const statCards = [
    {
      title: "Total Campaigns",
      value: stats.total,
      icon: Megaphone,
      description: "Total marketing campaigns",
      color: "text-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-950/30",
    },
    {
      title: "In Progress",
      value: stats.inProgress,
      icon: Clock,
      description: "Currently processing",
      color: "text-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-950/30",
    },
    {
      title: "Completed",
      value: stats.completed,
      icon: CheckCircle,
      description: "Successfully finished",
      color: "text-green-500",
      bgColor: "bg-green-50 dark:bg-green-950/30",
    },
    {
      title: "Failed",
      value: stats.failed,
      icon: AlertCircle,
      description: "Require attention",
      color: "text-red-500",
      bgColor: "bg-red-50 dark:bg-red-950/30",
    },
  ];

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-9 w-40" />
          <Skeleton className="h-10 w-36" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-12 mb-1" />
                <Skeleton className="h-3 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-40 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your marketing campaigns</p>
        </div>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> New Campaign
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create Campaign</DialogTitle>
              <DialogDescription>
                Enter the product URL to analyze and generate marketing assets.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="dash-title">Campaign Title</Label>
                <Input
                  id="dash-title"
                  placeholder="Summer Collection 2024"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dash-url">Product URL</Label>
                <Input
                  id="dash-url"
                  placeholder="https://example.com/product"
                  value={productUrl}
                  onChange={(e) => setProductUrl(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleCreate}
                disabled={createCampaign.isPending || !title.trim() || !productUrl.trim()}
              >
                {createCampaign.isPending ? "Creating..." : "Start Analysis"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.title} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Campaigns</CardTitle>
              <CardDescription>Your latest marketing campaigns</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/campaigns/">
                View all <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {recentCampaigns.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <Sparkles className="h-10 w-10 text-muted-foreground mb-4" />
                <h3 className="font-medium mb-1">No campaigns yet</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Create your first campaign to get started
                </p>
                <Button asChild size="sm">
                  <Link href="/campaigns/">
                    <Plus className="mr-2 h-4 w-4" /> Create Campaign
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {recentCampaigns.map((campaign: Campaign) => (
                  <Link 
                    key={campaign.id} 
                    href={`/campaigns/view?id=${campaign.id}`}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium truncate group-hover:text-amber-600 transition-colors">
                          {campaign.title}
                        </h4>
                        <Badge variant={getStatusVariant(campaign.status)} className="shrink-0">
                          {campaign.status === "RESEARCHING" || campaign.status === "GENERATING" ? (
                            <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> {campaign.status}</>
                          ) : (
                            campaign.status
                          )}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground truncate">
                        {campaign.product_url}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground ml-4 shrink-0">
                      {formatRelativeTime(campaign.created_at)}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Link 
              href="/campaigns/" 
              className="flex items-center gap-4 p-4 rounded-lg border hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors group"
            >
              <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/30">
                <Plus className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <h4 className="font-medium group-hover:text-amber-600 transition-colors">Create New Campaign</h4>
                <p className="text-sm text-muted-foreground">Generate marketing assets from a product URL</p>
              </div>
            </Link>

            <Link 
              href="/settings/" 
              className="flex items-center gap-4 p-4 rounded-lg border hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors group"
            >
              <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950/30">
                <ImageIcon className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <h4 className="font-medium group-hover:text-amber-600 transition-colors">Configure AI Engines</h4>
                <p className="text-sm text-muted-foreground">Set up OpenAI, Fal.ai, and other providers</p>
              </div>
            </Link>

            <div className="flex items-center gap-4 p-4 rounded-lg border bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20">
              <div className="p-2 rounded-lg bg-white dark:bg-zinc-900">
                <Sparkles className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <h4 className="font-medium">Pro Tip</h4>
                <p className="text-sm text-muted-foreground">Add a detailed product URL for better AI-generated creatives</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Asset Types</CardTitle>
            <CardDescription>What OpenSNS generates for your campaigns</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-start gap-3 p-4 rounded-lg bg-zinc-50 dark:bg-zinc-900">
                <div className="p-2 rounded-lg bg-pink-100 dark:bg-pink-950/50">
                  <ImageIcon className="h-5 w-5 text-pink-500" />
                </div>
                <div>
                  <h4 className="font-medium mb-1">Images</h4>
                  <p className="text-sm text-muted-foreground">
                    AI-generated product images optimized for Instagram, Facebook, and Google Ads
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-4 rounded-lg bg-zinc-50 dark:bg-zinc-900">
                <div className="p-2 rounded-lg bg-violet-100 dark:bg-violet-950/50">
                  <Video className="h-5 w-5 text-violet-500" />
                </div>
                <div>
                  <h4 className="font-medium mb-1">Videos</h4>
                  <p className="text-sm text-muted-foreground">
                    Short-form video content for TikTok, Reels, and Stories
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-4 rounded-lg bg-zinc-50 dark:bg-zinc-900">
                <div className="p-2 rounded-lg bg-cyan-100 dark:bg-cyan-950/50">
                  <FileText className="h-5 w-5 text-cyan-500" />
                </div>
                <div>
                  <h4 className="font-medium mb-1">Ad Copy</h4>
                  <p className="text-sm text-muted-foreground">
                    Platform-specific headlines, descriptions, and CTAs
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
