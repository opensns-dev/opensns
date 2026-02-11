"use client";

import { useState } from "react";
import Link from "next/link";
import { Images, Download, Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useCampaigns } from "@/hooks/use-campaigns";
import { Badge } from "@/components/ui/badge";

export default function AssetsPage() {
  const { data: campaigns, isLoading } = useCampaigns();
  const [searchQuery, setSearchQuery] = useState("");

  const completedCampaigns = campaigns?.filter(
    (c) => c.status === "COMPLETED"
  );

  const filteredCampaigns = completedCampaigns?.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Assets</h1>
          <p className="text-muted-foreground">
            Browse and download generated marketing assets
          </p>
        </div>
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
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 w-32 rounded bg-zinc-200 dark:bg-zinc-800" />
              </CardHeader>
              <CardContent>
                <div className="h-32 w-full rounded bg-zinc-200 dark:bg-zinc-800" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredCampaigns && filteredCampaigns.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredCampaigns.map((campaign) => (
            <Card
              key={campaign.id}
              className="hover:shadow-md transition-shadow"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base truncate">
                    {campaign.title}
                  </CardTitle>
                  <Badge variant="default">Completed</Badge>
                </div>
                <CardDescription className="truncate text-xs">
                  {campaign.product_url}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/campaigns/view?id=${campaign.id}`}>
                      <Images className="mr-2 h-4 w-4" />
                      View Assets
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="p-4 rounded-full bg-amber-50 dark:bg-amber-950/30 mb-4">
            <Sparkles className="h-10 w-10 text-amber-500" />
          </div>
          <h3 className="text-lg font-medium mb-2">No assets yet</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm">
            Complete a campaign to generate marketing assets like images, videos,
            and ad copy.
          </p>
          <Button asChild>
            <Link href="/campaigns/">Create a Campaign</Link>
          </Button>
        </div>
      )}
    </div>
  );
}
