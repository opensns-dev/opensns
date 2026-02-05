"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import CampaignDetail from "./campaign-detail";
import { Skeleton } from "@/components/ui/skeleton";

function CampaignViewContent() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id");
  
  if (!id) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <h2 className="text-2xl font-bold">No campaign selected</h2>
        <p className="text-muted-foreground">Please select a campaign from the list.</p>
      </div>
    );
  }
  
  return <CampaignDetail id={Number(id)} />;
}

function LoadingFallback() {
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
    </div>
  );
}

export default function CampaignViewPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <CampaignViewContent />
    </Suspense>
  );
}
