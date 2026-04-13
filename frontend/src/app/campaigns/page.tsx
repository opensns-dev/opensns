"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, Trash2, Megaphone, ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useCampaigns, useCreateCampaign, useDeleteCampaign } from "@/hooks/use-campaigns";
import { getStatusVariant, formatDate } from "@/lib/utils";

export default function CampaignsPage() {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [productUrl, setProductUrl] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const { data: campaigns, isLoading, error } = useCampaigns();
  const createCampaign = useCreateCampaign();
  const deleteCampaign = useDeleteCampaign();
  const router = useRouter();

  const totalItems = campaigns?.length ?? 0;
  const totalPages = Math.ceil(totalItems / pageSize);
  const paginatedCampaigns = campaigns?.slice((page - 1) * pageSize, page * pageSize);

  const handleCreate = async () => {
    if (!title.trim() || !productUrl.trim()) return;

    try {
      const data = await createCampaign.mutateAsync({
        title: title,
        product_url: productUrl
      });
      setTitle("");
      setProductUrl("");
      setIsOpen(false);
      toast.success("Campaign created", {
        description: "Your campaign is now being processed.",
      });
      router.push(`/campaigns/view?id=${data.id}`);
    } catch (err) {
      console.error("Failed to create campaign:", err);
      toast.error("Failed to create campaign", {
        description: "Please try again.",
      });
    }
  };

  const handleDelete = async (id: number, campaignTitle: string) => {
    try {
      await deleteCampaign.mutateAsync(id);
      toast.success("Campaign deleted", {
        description: `"${campaignTitle}" has been permanently deleted.`,
      });
    } catch (err) {
      console.error("Failed to delete campaign:", err);
      toast.error("Failed to delete campaign", {
        description: "Please try again.",
      });
    }
  };

  if (error) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <div className="rounded-md bg-red-50 p-4 text-red-600 dark:bg-red-900/20 dark:text-red-400">
          Failed to load campaigns. Please try again.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Campaigns</h1>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> Create Campaign
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
                <Label htmlFor="title">Campaign Title</Label>
                <Input
                  id="title"
                  placeholder="Summer Collection 2024"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="url">Product URL</Label>
                <Input
                  id="url"
                  placeholder="https://example.com/product"
                  value={productUrl}
                  onChange={(e) => setProductUrl(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="submit"
                onClick={handleCreate}
                disabled={createCampaign.isPending || !title.trim() || !productUrl.trim()}
              >
                {createCampaign.isPending ? "Creating..." : "Start Analysis"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border bg-white dark:bg-zinc-950">
        <Table>
          <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>

          </TableHeader>
          <TableBody>
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-4 w-48" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-5 w-20" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-24" />
                    </TableCell>
                    <TableCell className="text-right">
                      <Skeleton className="h-8 w-12 ml-auto" />
                    </TableCell>
                  </TableRow>
                ))
              ) : campaigns && campaigns.length > 0 ? (
                paginatedCampaigns?.map((campaign) => (
                  <TableRow key={campaign.id}>
                    <TableCell className="font-medium">
                      <p className="truncate max-w-[300px]" title={campaign.title}>
                        {campaign.title}
                      </p>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(campaign.status)}>
                        {campaign.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(campaign.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/campaigns/view?id=${campaign.id}`}>View</Link>
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Campaign</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to delete &quot;{campaign.title}&quot;? This action cannot be undone and all generated assets will be permanently removed.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDelete(campaign.id, campaign.title)}
                                className="bg-red-500 hover:bg-red-600"
                              >
                                {deleteCampaign.isPending ? "Deleting..." : "Delete"}
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} className="h-48">
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="p-3 rounded-full bg-amber-50 dark:bg-amber-950/30 mb-4">
                        <Megaphone className="h-8 w-8 text-amber-500" />
                      </div>
                      <h3 className="font-medium mb-1">No campaigns yet</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Create your first campaign to generate AI marketing assets.
                      </p>
                      <Button size="sm" onClick={() => setIsOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" /> Create Campaign
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalItems)} of {totalItems}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
