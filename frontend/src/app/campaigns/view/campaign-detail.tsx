"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { 
  ArrowLeft, 
  ImageIcon, 
  Video as VideoIcon, 
  FileText, 
  Play, 
  ExternalLink, 
  Copy, 
  Check,
  RefreshCw,
  Loader2,
  Download,
  Archive
} from "lucide-react";
import { toast } from "sonner";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useCampaign } from "@/hooks/use-campaigns";
import { useAssets } from "@/hooks/use-assets";
import { useWebSocket } from "@/hooks/use-websocket";
import type { Asset, AgentLog, Campaign } from "@/types";

const downloadAsset = async (url: string, filename: string) => {
  try {
    const response = await fetch(url);
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    toast.success("Download started", {
      description: filename,
    });
  } catch {
    toast.error("Download failed", {
      description: "Could not download the file. Try opening it directly.",
    });
  }
};

const ProgressIndicator = ({ logs, status }: { logs: AgentLog[]; status: string }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (status !== "RESEARCHING" && status !== "GENERATING") return null;

  return (
    <Card className="border-amber-200/50 bg-amber-50/30 dark:bg-amber-950/10 backdrop-blur-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin text-amber-500" />
            Agent Activity
          </CardTitle>
          <Badge variant="outline" className="animate-pulse bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400">
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div 
          ref={scrollRef}
          className="h-48 overflow-y-auto rounded-md bg-zinc-950 p-4 font-mono text-xs text-zinc-300 space-y-2 scroll-smooth"
        >
          {logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-zinc-500">
              Waiting for agent activity...
            </div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex gap-2">
                <span className="text-amber-500 font-bold">[{log.agent_name}]</span>
                <span className={log.level === "ERROR" ? "text-red-400" : ""}>{log.message}</span>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const AssetGrid = ({ type, assets }: { type: Asset["type"]; assets: Asset[] }) => {
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const copyToClipboard = async (text: string, id: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error("Failed to copy", err);
      toast.error("Failed to copy");
    }
  };

  if (assets.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
        No {type.toLowerCase()}s found for this campaign.
      </div>
    );
  }

  if (type === "IMAGE") {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {assets.map((asset) => {
          const meta = JSON.parse(asset.asset_metadata || "{}");
          const filename = `${meta.platform || "image"}_${meta.angle || asset.id}.png`;
          return (
            <Card key={asset.id} className="overflow-hidden group hover:shadow-lg transition-all duration-300">
              <div className="aspect-square relative overflow-hidden">
                <img
                  src={asset.content}
                  alt={meta.angle || "Generated Image"}
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    onClick={() => downloadAsset(asset.content, filename)}
                    className="translate-y-4 group-hover:translate-y-0 transition-transform duration-300"
                  >
                    <Download className="mr-2 h-4 w-4" /> Download
                  </Button>
                  <Button variant="secondary" size="sm" asChild className="translate-y-4 group-hover:translate-y-0 transition-transform duration-300 delay-75">
                    <a href={asset.content} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="mr-2 h-4 w-4" /> View
                    </a>
                  </Button>
                </div>
              </div>
              <CardHeader className="p-4">
                <div className="flex items-center justify-between">
                  <Badge variant="outline">{meta.platform}</Badge>
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">{meta.aspect_ratio}</span>
                </div>
                <CardTitle className="text-sm mt-2 line-clamp-1">{meta.angle}</CardTitle>
              </CardHeader>
            </Card>
          );
        })}
      </div>
    );
  }

  if (type === "VIDEO") {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {assets.map((asset) => {
          const meta = JSON.parse(asset.asset_metadata || "{}");
          const filename = `${meta.platform || "video"}_${meta.angle || asset.id}.mp4`;
          return (
            <Card key={asset.id} className="overflow-hidden group hover:shadow-lg transition-all duration-300">
              <div className="aspect-video relative bg-zinc-100 dark:bg-zinc-900 flex items-center justify-center overflow-hidden">
                <video src={asset.content} className="h-full w-full object-cover" />
                <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="secondary" 
                      size="sm"
                      onClick={() => downloadAsset(asset.content, filename)}
                    >
                      <Download className="mr-2 h-4 w-4" /> Download
                    </Button>
                    <div className="h-14 w-14 rounded-full bg-white/90 flex items-center justify-center shadow-xl cursor-pointer hover:scale-110 transition-transform">
                      <Play className="h-7 w-7 text-black fill-black" />
                    </div>
                  </div>
                </div>
                {meta.duration && (
                  <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-black/60 text-white text-[10px] font-bold">
                    {meta.duration}
                  </div>
                )}
              </div>
              <CardHeader className="p-4">
                <div className="flex items-center justify-between">
                  <Badge variant="outline">{meta.platform}</Badge>
                </div>
                <CardTitle className="text-sm mt-2">{meta.angle}</CardTitle>
              </CardHeader>
            </Card>
          );
        })}
      </div>
    );
  }

  if (type === "COPY") {
    return (
      <div className="grid grid-cols-1 gap-6">
        {assets.map((asset) => {
          const meta = JSON.parse(asset.asset_metadata || "{}");
          return (
            <Card key={asset.id} className="relative overflow-hidden group hover:border-amber-200 transition-colors duration-300">
              <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => copyToClipboard(asset.content, asset.id)}
                  className="bg-background/80 backdrop-blur-sm"
                >
                  {copiedId === asset.id ? (
                    <><Check className="mr-2 h-4 w-4 text-green-500" /> Copied</>
                  ) : (
                    <><Copy className="mr-2 h-4 w-4" /> Copy</>
                  )}
                </Button>
              </div>
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline" className="bg-zinc-50 dark:bg-zinc-900">{meta.platform}</Badge>
                  <Badge variant="secondary" className="font-normal">{meta.angle}</Badge>
                </div>
                <CardTitle className="text-xl font-bold tracking-tight text-amber-600 dark:text-amber-500">{meta.headline}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-base leading-relaxed whitespace-pre-wrap">{asset.content}</p>
              </CardContent>
              {meta.cta && (
                <CardFooter className="bg-zinc-50/50 dark:bg-zinc-900/50 border-t px-6 py-3">
                  <div className="text-sm font-semibold flex items-center gap-2 text-zinc-500">
                    CALL TO ACTION: 
                    <span className="text-zinc-900 dark:text-zinc-100 font-bold">{meta.cta}</span>
                  </div>
                </CardFooter>
              )}
            </Card>
          );
        })}
      </div>
    );
  }

  return null;
};

export default function CampaignDetail({ id }: { id: number }) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<Asset["type"]>("IMAGE");
  const [isExporting, setIsExporting] = useState(false);
  const exportAbortController = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      exportAbortController.current?.abort();
    };
  }, []);

  const { data: campaign, isLoading: isLoadingCampaign, error: campaignError } = useCampaign(id);
  const { data: assets = [], isLoading: isLoadingAssets } = useAssets(id);
  const { logs, isConnected } = useWebSocket(id);

  const approveMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<Campaign>(`/campaigns/${id}/approve`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns", id] });
      toast.success("Campaign approved", {
        description: "Your assets are now being finalized.",
      });
    },
    onError: () => {
      toast.error("Failed to approve campaign", {
        description: "Please try again.",
      });
    },
  });

  if (isLoadingCampaign) {
    return (
      <div className="flex flex-col gap-6 p-6 max-w-6xl mx-auto">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-md" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <Skeleton className="h-[200px] w-full rounded-xl" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
        </div>
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (campaignError || !campaign) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <h2 className="text-2xl font-bold">Failed to load campaign</h2>
        <p className="text-muted-foreground">The campaign you are looking for might not exist or you do not have access.</p>
        <Button variant="default" asChild>
          <Link href="/campaigns/">Go back to Campaigns</Link>
        </Button>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PENDING": return "bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-900 dark:text-zinc-400";
      case "RESEARCHING": return "bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400";
      case "GENERATING": return "bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400";
      case "AWAITING_APPROVAL": return "bg-purple-50 text-purple-600 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400";
      case "COMPLETED": return "bg-green-50 text-green-600 border-green-200 dark:bg-green-900/30 dark:text-green-400";
      case "FAILED": return "bg-red-50 text-red-600 border-red-200 dark:bg-red-900/30 dark:text-red-400";
      default: return "bg-zinc-100 text-zinc-600";
    }
  };

  const filteredAssets = assets.filter((a) => a.type === activeTab);

  return (
    <div className="flex flex-col gap-8 p-6 lg:p-10 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" asChild className="shrink-0">
            <Link href="/campaigns/">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-extrabold tracking-tight lg:text-4xl">{campaign.title}</h1>
              <Badge className={`px-2.5 py-0.5 font-bold ${getStatusColor(campaign.status)}`}>
                {campaign.status}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground font-medium">
              <ExternalLink className="h-3 w-3" />
              <a href={campaign.product_url} target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors truncate max-w-xs sm:max-w-md">
                {campaign.product_url}
              </a>
              <span className="text-zinc-300 dark:text-zinc-700">•</span>
              <span>{new Date(campaign.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</span>
            </div>
          </div>
        </div>

        {campaign.status === "AWAITING_APPROVAL" && (
          <Button 
            onClick={() => approveMutation.mutate()} 
            disabled={approveMutation.isPending}
            className="bg-purple-600 hover:bg-purple-700 text-white font-bold px-8 h-12 rounded-full shadow-lg shadow-purple-500/20 transition-all active:scale-95"
          >
            {approveMutation.isPending ? (
              <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Approving...</>
            ) : (
              "Approve & Launch Assets"
            )}
          </Button>
        )}

        {assets.length > 0 && (
          <Button
            variant="outline"
            onClick={async () => {
              exportAbortController.current?.abort();
              exportAbortController.current = new AbortController();
              
              setIsExporting(true);
              toast.info("Preparing ZIP archive...");
              try {
                const response = await api.get(`/campaigns/${id}/export`, {
                  responseType: "blob",
                  signal: exportAbortController.current.signal,
                  timeout: 120000,
                });
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement("a");
                link.href = url;
                link.download = `campaign_${id}_assets.zip`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
                toast.success("Download started", {
                  description: `campaign_${id}_assets.zip`,
                });
              } catch (error) {
                if (error instanceof Error && error.name === "CanceledError") {
                  return;
                }
                toast.error("Export failed", {
                  description: "Could not create ZIP archive. Try again.",
                });
              } finally {
                setIsExporting(false);
              }
            }}
            disabled={isExporting}
            className="gap-2"
          >
            {isExporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Archive className="h-4 w-4" />
            )}
            Export All
          </Button>
        )}
      </div>

      <ProgressIndicator logs={logs} status={campaign.status} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden">
            <CardHeader className="bg-zinc-50/50 dark:bg-zinc-900/50 border-b">
              <CardTitle className="text-lg">Campaign Info</CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Description</h4>
                <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                  {campaign.description || "No description provided."}
                </p>
              </div>
              
              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Created At</h4>
                  <p className="text-sm font-medium">{new Date(campaign.created_at).toLocaleTimeString()}</p>
                </div>
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Real-time</h4>
                  <p className="text-sm font-medium flex items-center gap-1.5">
                    <span className={`h-2 w-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-zinc-300"}`} />
                    {isConnected ? "Connected" : "Disconnected"}
                  </p>
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Assets Summary</h4>
                <div className="flex gap-3">
                  <Badge variant="secondary" className="gap-1">
                    <ImageIcon className="h-3 w-3" />
                    {assets.filter(a => a.type === "IMAGE").length} Images
                  </Badge>
                  <Badge variant="secondary" className="gap-1">
                    <VideoIcon className="h-3 w-3" />
                    {assets.filter(a => a.type === "VIDEO").length} Videos
                  </Badge>
                  <Badge variant="secondary" className="gap-1">
                    <FileText className="h-3 w-3" />
                    {assets.filter(a => a.type === "COPY").length} Copies
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center gap-2 p-1.5 bg-zinc-100 dark:bg-zinc-900 rounded-xl w-fit border border-zinc-200 dark:border-zinc-800">
            <Button
              variant={activeTab === "IMAGE" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("IMAGE")}
              className={`flex items-center gap-2 px-4 rounded-lg transition-all ${activeTab === "IMAGE" ? "bg-white dark:bg-zinc-800 shadow-sm font-bold text-amber-600" : ""}`}
            >
              <ImageIcon className="h-4 w-4" /> Images
            </Button>
            <Button
              variant={activeTab === "VIDEO" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("VIDEO")}
              className={`flex items-center gap-2 px-4 rounded-lg transition-all ${activeTab === "VIDEO" ? "bg-white dark:bg-zinc-800 shadow-sm font-bold text-amber-600" : ""}`}
            >
              <VideoIcon className="h-4 w-4" /> Videos
            </Button>
            <Button
              variant={activeTab === "COPY" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("COPY")}
              className={`flex items-center gap-2 px-4 rounded-lg transition-all ${activeTab === "COPY" ? "bg-white dark:bg-zinc-800 shadow-sm font-bold text-amber-600" : ""}`}
            >
              <FileText className="h-4 w-4" /> Ad Copies
            </Button>
          </div>

          <div className="min-h-[400px]">
            {isLoadingAssets ? (
              <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-64" />
                <Skeleton className="h-64" />
              </div>
            ) : (
              <AssetGrid type={activeTab} assets={filteredAssets} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
