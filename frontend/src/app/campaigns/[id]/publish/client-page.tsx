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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { useCampaign } from "@/hooks/use-campaigns";
import { useAssets } from "@/hooks/use-assets";
import {
  usePublishConnections,
  useDeleteConnection,
  useConnectMeta,
  usePublishCampaign,
  usePublishLogs,
} from "@/hooks/use-publishing";
import type { PublishPlatformType, PublishStatus } from "@/types";

const STATUS_VARIANT: Record<
  PublishStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  PENDING: "outline",
  PUBLISHING: "secondary",
  PUBLISHED: "default",
  FAILED: "destructive",
};

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString();
}

export default function PublishPage() {
  const params = useParams<{ id: string }>();
  const campaignId = Number(params.id);

  const [selectedPlatform, setSelectedPlatform] =
    useState<PublishPlatformType>("FACEBOOK");
  const [caption, setCaption] = useState("");
  const [selectedAssetIds, setSelectedAssetIds] = useState<number[]>([]);

  const { data: campaign, isLoading: campaignLoading } =
    useCampaign(campaignId);
  const { data: assets, isLoading: assetsLoading } = useAssets(campaignId);
  const { data: connections, isLoading: connectionsLoading } =
    usePublishConnections();
  const { data: logs, isLoading: logsLoading } = usePublishLogs(campaignId);

  const connectMeta = useConnectMeta();
  const deleteConnection = useDeleteConnection();
  const publishCampaign = usePublishCampaign();

  const handleConnectMeta = async () => {
    try {
      const data = await connectMeta.mutateAsync();
      window.location.href = data.auth_url;
    } catch {
      toast.error("Failed to initiate connection");
    }
  };

  const handleDisconnect = async (connectionId: number) => {
    try {
      await deleteConnection.mutateAsync(connectionId);
      toast.success("Platform disconnected");
    } catch {
      toast.error("Failed to disconnect");
    }
  };

  const toggleAsset = (assetId: number) => {
    setSelectedAssetIds((prev) =>
      prev.includes(assetId)
        ? prev.filter((id) => id !== assetId)
        : [...prev, assetId]
    );
  };

  const handlePublish = async () => {
    try {
      await publishCampaign.mutateAsync({
        campaignId,
        data: {
          platform: selectedPlatform,
          asset_ids: selectedAssetIds.length > 0 ? selectedAssetIds : undefined,
          caption: caption || undefined,
        },
      });
      toast.success("Published successfully");
      setCaption("");
      setSelectedAssetIds([]);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Publishing failed";
      toast.error(message);
    }
  };

  if (campaignLoading) {
    return (
      <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
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

  const activeConnection = connections?.find(
    (c) => c.platform === selectedPlatform && c.is_active
  );

  return (
    <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{campaign.title}</h1>
          <p className="text-muted-foreground">Publish to social platforms</p>
        </div>
        <Link href="/campaigns">
          <Button variant="outline">Back</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connected Platforms</CardTitle>
          <CardDescription>
            Connect your social media accounts to publish directly
          </CardDescription>
        </CardHeader>
        <CardContent>
          {connectionsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : connections && connections.length > 0 ? (
            <div className="space-y-3">
              {connections.map((conn) => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary">{conn.platform}</Badge>
                    <span className="font-medium">
                      {conn.page_name || conn.account_name || "Unknown"}
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDisconnect(conn.id)}
                    disabled={deleteConnection.isPending}
                  >
                    Disconnect
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No platforms connected yet
            </p>
          )}
          <div className="mt-4">
            <Button
              onClick={handleConnectMeta}
              disabled={connectMeta.isPending}
            >
              {connectMeta.isPending
                ? "Connecting..."
                : "Connect Facebook / Instagram"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Publish Campaign</CardTitle>
          <CardDescription>
            Select a platform and assets to publish
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Platform</Label>
            <Select
              value={selectedPlatform}
              onValueChange={(v) =>
                setSelectedPlatform(v as PublishPlatformType)
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FACEBOOK">Facebook</SelectItem>
                <SelectItem value="INSTAGRAM">Instagram</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Caption</Label>
            <Input
              placeholder="Enter a caption for your post..."
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>
              Assets{" "}
              <span className="text-muted-foreground font-normal">
                (select specific assets or leave empty to include all)
              </span>
            </Label>
            {assetsLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : assets && assets.length > 0 ? (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {assets.map((asset) => (
                  <button
                    key={asset.id}
                    type="button"
                    onClick={() => toggleAsset(asset.id)}
                    className={`rounded-lg border p-3 text-left text-sm transition-colors ${
                      selectedAssetIds.includes(asset.id)
                        ? "border-primary bg-primary/5"
                        : "hover:bg-muted/50"
                    }`}
                  >
                    <Badge variant="outline" className="mb-1">
                      {asset.type}
                    </Badge>
                    <p className="truncate text-xs text-muted-foreground">
                      {asset.type === "COPY"
                        ? asset.content.slice(0, 60)
                        : `Asset #${asset.id}`}
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No assets in this campaign
              </p>
            )}
          </div>

          <Button
            className="w-full"
            onClick={handlePublish}
            disabled={publishCampaign.isPending || !activeConnection}
          >
            {publishCampaign.isPending
              ? "Publishing..."
              : !activeConnection
                ? `Connect ${selectedPlatform} first`
                : `Publish to ${selectedPlatform}`}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Publish History</CardTitle>
        </CardHeader>
        <CardContent>
          {logsLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : logs && logs.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Platform</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Post ID</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      <Badge variant="secondary">{log.platform}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[log.status]}>
                        {log.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {log.external_url ? (
                        <a
                          href={log.external_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          {log.external_post_id || "View"}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDate(log.created_at)}
                    </TableCell>
                    <TableCell>
                      {log.error_message ? (
                        <span className="text-destructive text-sm">
                          {log.error_message}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground">
              No publish history yet
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
