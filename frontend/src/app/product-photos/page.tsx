"use client";

import { useEffect, useState } from "react";
import {
  Camera,
  Trash2,
  RefreshCw,
  Plus,
  Image as ImageIcon,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import {
  useProductPhotos,
  useCreateProductPhoto,
  useDeleteProductPhoto,
  useRetryProductPhoto,
} from "@/hooks/use-product-photos";
import type {
  ProductPhoto,
  ProductPhotoCreate,
  ProductPhotoAngle,
  ProductPhotoStatus,
} from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const ALL_ANGLES: { value: ProductPhotoAngle; label: string }[] = [
  { value: "FRONT", label: "Front" },
  { value: "SIDE", label: "Side" },
  { value: "TOP_DOWN", label: "Top Down" },
  { value: "LIFESTYLE", label: "Lifestyle" },
  { value: "MODEL_HOLDING", label: "Model Holding" },
  { value: "STUDIO", label: "Studio" },
];

function statusVariant(
  status: ProductPhotoStatus
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "COMPLETED":
      return "default";
    case "FAILED":
      return "destructive";
    case "PENDING":
    case "REMOVING_BG":
    case "GENERATING":
      return "secondary";
    default:
      return "outline";
  }
}

function statusLabel(status: ProductPhotoStatus): string {
  switch (status) {
    case "PENDING":
      return "Pending";
    case "REMOVING_BG":
      return "Removing Background";
    case "GENERATING":
      return "Generating";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
    default:
      return status;
  }
}

function isProcessing(status: ProductPhotoStatus): boolean {
  return status === "PENDING" || status === "REMOVING_BG" || status === "GENERATING";
}

export default function ProductPhotosPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const [scenePrompt, setScenePrompt] = useState("");
  const [selectedAngles, setSelectedAngles] = useState<ProductPhotoAngle[]>([
    "FRONT",
    "LIFESTYLE",
    "STUDIO",
  ]);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [shouldPoll, setShouldPoll] = useState(false);

  const { data: photos, isLoading } = useProductPhotos(shouldPoll ? 3000 : false);
  const createPhoto = useCreateProductPhoto();
  const deletePhoto = useDeleteProductPhoto();
  const retryPhoto = useRetryProductPhoto();

  useEffect(() => {
    setShouldPoll(photos?.some((p) => isProcessing(p.status)) ?? false);
  }, [photos]);

  const toggleAngle = (angle: ProductPhotoAngle) => {
    setSelectedAngles((prev) =>
      prev.includes(angle)
        ? prev.filter((a) => a !== angle)
        : [...prev, angle]
    );
  };

  const handleCreate = async () => {
    if (!imageUrl.trim()) {
      toast.error("Image URL is required");
      return;
    }
    if (selectedAngles.length === 0) {
      toast.error("Select at least one angle");
      return;
    }

    const data: ProductPhotoCreate = {
      original_image_url: imageUrl.trim(),
      angles: selectedAngles,
      scene_prompt: scenePrompt.trim() || undefined,
    };

    try {
      await createPhoto.mutateAsync(data);
      toast.success("Product photo job created");
      setDialogOpen(false);
      setImageUrl("");
      setScenePrompt("");
      setSelectedAngles(["FRONT", "LIFESTYLE", "STUDIO"]);
    } catch {
      toast.error("Failed to create product photo job");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deletePhoto.mutateAsync(id);
      setDeleteConfirmId(null);
      toast.success("Product photo deleted");
    } catch {
      toast.error("Failed to delete product photo");
    }
  };

  const handleRetry = async (id: number) => {
    try {
      await retryPhoto.mutateAsync(id);
      toast.success("Retrying product photo job");
    } catch {
      toast.error("Failed to retry product photo job");
    }
  };

  if (isLoading) {
    return (
      <div className="container max-w-4xl py-8 space-y-6">
        <Skeleton className="h-9 w-56" />
        <div className="grid gap-4 sm:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Product Photography AI</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Generate professional product shots from a single image
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Photo Shoot
        </Button>
      </div>

      {!photos?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Camera className="h-12 w-12 text-zinc-400 mb-4" />
            <h3 className="text-lg font-semibold mb-1">No product photos yet</h3>
            <p className="text-zinc-500 dark:text-zinc-400 mb-4">
              Create your first product photo shoot to generate professional shots.
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Photo Shoot
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {photos.map((photo) => (
            <ProductPhotoCard
              key={photo.id}
              photo={photo}
              onDelete={() => setDeleteConfirmId(photo.id)}
              onRetry={() => handleRetry(photo.id)}
              isRetrying={retryPhoto.isPending}
            />
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>New Product Photo Shoot</DialogTitle>
            <DialogDescription>
              Provide a product image URL and select angles to generate.
              Each angle costs 3 credits.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="pp-image-url">Product Image URL *</Label>
              <Input
                id="pp-image-url"
                type="url"
                placeholder="https://example.com/product.png"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Angles ({selectedAngles.length} selected)</Label>
              <div className="grid grid-cols-2 gap-2">
                {ALL_ANGLES.map((angle) => (
                  <label
                    key={angle.value}
                    className="flex items-center gap-2 rounded-md border border-zinc-200 dark:border-zinc-700 px-3 py-2 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800"
                  >
                    <input
                      type="checkbox"
                      checked={selectedAngles.includes(angle.value)}
                      onChange={() => toggleAngle(angle.value)}
                      className="rounded border-zinc-300"
                    />
                    <span className="text-sm">{angle.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pp-scene">Scene Prompt (optional)</Label>
              <textarea
                id="pp-scene"
                placeholder="e.g. Minimalist white marble surface with soft natural lighting"
                value={scenePrompt}
                onChange={(e) => setScenePrompt(e.target.value)}
                rows={3}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <p className="text-xs text-zinc-500">
              Estimated cost: {selectedAngles.length * 3} credits ({selectedAngles.length} angle{selectedAngles.length !== 1 ? "s" : ""} × 3 credits)
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={createPhoto.isPending}>
              {createPhoto.isPending ? "Creating..." : "Start Photo Shoot"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteConfirmId !== null}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Product Photo</DialogTitle>
            <DialogDescription>
              This action cannot be undone. Are you sure you want to delete this
              product photo job and all generated images?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
              disabled={deletePhoto.isPending}
            >
              {deletePhoto.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ProductPhotoCard({
  photo,
  onDelete,
  onRetry,
  isRetrying,
}: {
  photo: ProductPhoto;
  onDelete: () => void;
  onRetry: () => void;
  isRetrying: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm font-medium truncate max-w-[180px]">
              {photo.original_image_url.split("/").pop() || "Product Photo"}
            </CardTitle>
            <Badge variant={statusVariant(photo.status)}>
              {isProcessing(photo.status) && (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              )}
              {statusLabel(photo.status)}
            </Badge>
          </div>
          <div className="flex gap-1">
            {photo.status === "FAILED" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onRetry}
                disabled={isRetrying}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onDelete}>
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        </div>
        {photo.scene_prompt && (
          <CardDescription className="truncate">
            {photo.scene_prompt}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="pt-0 space-y-3">
        <div className="flex gap-2 items-start">
          <div className="w-16 h-16 rounded border border-zinc-200 dark:border-zinc-700 overflow-hidden flex-shrink-0">
            <img
              src={photo.original_image_url}
              alt="Original product"
              className="w-full h-full object-cover"
            />
          </div>
          <div className="text-xs text-zinc-500 space-y-1">
            <div>Angles: {photo.angles.join(", ")}</div>
            <div>
              Created: {new Date(photo.created_at).toLocaleDateString()}
            </div>
            {photo.error && (
              <div className="text-red-500">Error: {photo.error}</div>
            )}
          </div>
        </div>

        {photo.results.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-zinc-600 dark:text-zinc-400">
              Generated Images
            </p>
            <div className="grid grid-cols-3 gap-2">
              {photo.results.map((result, idx) => (
                <div key={idx} className="space-y-1">
                  <a
                    href={result.image_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded border border-zinc-200 dark:border-zinc-700 overflow-hidden aspect-square hover:ring-2 hover:ring-primary transition-all"
                  >
                    <img
                      src={result.image_url}
                      alt={`${result.angle} view`}
                      className="w-full h-full object-cover"
                    />
                  </a>
                  <p className="text-[10px] text-center text-zinc-500">
                    {result.angle}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {isProcessing(photo.status) && photo.results.length === 0 && (
          <div className="flex items-center justify-center py-4 text-zinc-400">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            <span className="text-sm">{statusLabel(photo.status)}...</span>
          </div>
        )}

        {photo.status === "COMPLETED" && photo.results.length === 0 && (
          <div className="flex flex-col items-center justify-center py-4 text-zinc-400">
            <ImageIcon className="h-8 w-8 mb-1" />
            <span className="text-xs">No images generated</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
