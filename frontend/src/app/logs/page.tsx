"use client";

import { useState } from "react";
import Link from "next/link";
import { ScrollText, Search, Sparkles, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useCampaigns } from "@/hooks/use-campaigns";

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function LogsPage() {
  const { data: campaigns, isLoading } = useCampaigns();
  const [searchQuery, setSearchQuery] = useState("");

  const filteredCampaigns = campaigns?.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Logs</h1>
        <p className="text-muted-foreground">
          View agent activity logs for your campaigns
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search campaigns..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {isLoading ? (
        <div className="rounded-md border bg-white dark:bg-zinc-950">
          <div className="p-8 text-center text-muted-foreground animate-pulse">
            Loading campaigns...
          </div>
        </div>
      ) : filteredCampaigns && filteredCampaigns.length > 0 ? (
        <div className="rounded-md border bg-white dark:bg-zinc-950">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Campaign</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCampaigns.map((campaign) => (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium">
                    <p className="truncate max-w-[300px]">{campaign.title}</p>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        campaign.status === "COMPLETED"
                          ? "default"
                          : campaign.status === "FAILED"
                            ? "destructive"
                            : "secondary"
                      }
                    >
                      {campaign.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDate(campaign.created_at)}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/campaigns/view?id=${campaign.id}`}>
                        <ExternalLink className="mr-2 h-4 w-4" />
                        View Logs
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="p-4 rounded-full bg-amber-50 dark:bg-amber-950/30 mb-4">
            <ScrollText className="h-10 w-10 text-amber-500" />
          </div>
          <h3 className="text-lg font-medium mb-2">No logs yet</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm">
            Campaign logs will appear here once you create and run a campaign.
          </p>
          <Button asChild>
            <Link href="/campaigns/">Create a Campaign</Link>
          </Button>
        </div>
      )}
    </div>
  );
}
