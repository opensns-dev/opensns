"use client";

import { useState } from "react";
import { Plus, Pencil, Trash2, Star, Palette, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import {
  useBrandKits,
  useCreateBrandKit,
  useUpdateBrandKit,
  useDeleteBrandKit,
} from "@/hooks/use-brand-kits";
import type { BrandKit, BrandKitCreate } from "@/types";
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

const EMPTY_FORM: BrandKitCreate = {
  name: "",
  is_default: false,
  logo_url: "",
  primary_color: "",
  secondary_color: "",
  accent_color: "",
  font_heading: "",
  font_body: "",
  tone_of_voice: "",
  brand_values: [],
  target_audience: "",
  guidelines: "",
};

function ColorSwatch({ color }: { color: string | null }) {
  if (!color) return null;
  return (
    <span
      className="inline-block h-4 w-4 rounded-full border border-zinc-300 dark:border-zinc-600"
      style={{ backgroundColor: color }}
    />
  );
}

export default function BrandKitsPage() {
  const { data: brandKits, isLoading } = useBrandKits();
  const createBrandKit = useCreateBrandKit();
  const updateBrandKit = useUpdateBrandKit();
  const deleteBrandKit = useDeleteBrandKit();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingKit, setEditingKit] = useState<BrandKit | null>(null);
  const [formData, setFormData] = useState<BrandKitCreate>(EMPTY_FORM);
  const [valuesInput, setValuesInput] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const openCreateDialog = () => {
    setEditingKit(null);
    setFormData(EMPTY_FORM);
    setValuesInput("");
    setDialogOpen(true);
  };

  const openEditDialog = (kit: BrandKit) => {
    setEditingKit(kit);
    setFormData({
      name: kit.name,
      is_default: kit.is_default,
      logo_url: kit.logo_url || "",
      primary_color: kit.primary_color || "",
      secondary_color: kit.secondary_color || "",
      accent_color: kit.accent_color || "",
      font_heading: kit.font_heading || "",
      font_body: kit.font_body || "",
      tone_of_voice: kit.tone_of_voice || "",
      brand_values: kit.brand_values,
      target_audience: kit.target_audience || "",
      guidelines: kit.guidelines || "",
    });
    setValuesInput(kit.brand_values.join(", "));
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast.error("Name is required");
      return;
    }
    const payload: BrandKitCreate = {
      ...formData,
      brand_values: valuesInput
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean),
    };

    try {
      if (editingKit) {
        await updateBrandKit.mutateAsync({ id: editingKit.id, data: payload });
        toast.success("Brand kit updated");
      } else {
        await createBrandKit.mutateAsync(payload);
        toast.success("Brand kit created");
      }
      setDialogOpen(false);
    } catch {
      toast.error(editingKit ? "Failed to update brand kit" : "Failed to create brand kit");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteBrandKit.mutateAsync(id);
      setDeleteConfirmId(null);
      toast.success("Brand kit deleted");
    } catch {
      toast.error("Failed to delete brand kit");
    }
  };

  const isPending = createBrandKit.isPending || updateBrandKit.isPending;

  if (isLoading) {
    return (
      <div className="container max-w-3xl py-8 space-y-6">
        <Skeleton className="h-9 w-48" />
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-3xl py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Button variant="ghost" size="sm" asChild className="h-8 w-8 p-0">
              <a href="/settings">
                <ArrowLeft className="h-4 w-4" />
              </a>
            </Button>
            <h1 className="text-2xl font-bold">Brand Kits</h1>
          </div>
          <p className="text-zinc-600 dark:text-zinc-400 ml-10">
            Manage your brand identity for consistent ad generation
          </p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-2" />
          Create Brand Kit
        </Button>
      </div>

      {!brandKits?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Palette className="h-12 w-12 text-zinc-400 mb-4" />
            <h3 className="text-lg font-semibold mb-1">No brand kits yet</h3>
            <p className="text-zinc-500 dark:text-zinc-400 mb-4">
              Create your first brand kit to maintain consistent branding across campaigns.
            </p>
            <Button onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Create Brand Kit
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {brandKits.map((kit) => (
            <Card key={kit.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">{kit.name}</CardTitle>
                    {kit.is_default && (
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        Default
                      </Badge>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openEditDialog(kit)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteConfirmId(kit.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
                {kit.tone_of_voice && (
                  <CardDescription>{kit.tone_of_voice}</CardDescription>
                )}
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex flex-wrap gap-4 text-sm">
                  {(kit.primary_color || kit.secondary_color || kit.accent_color) && (
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-500">Colors:</span>
                      <div className="flex gap-1">
                        <ColorSwatch color={kit.primary_color} />
                        <ColorSwatch color={kit.secondary_color} />
                        <ColorSwatch color={kit.accent_color} />
                      </div>
                    </div>
                  )}
                  {kit.font_heading && (
                    <div className="text-zinc-500">
                      Heading: <span className="text-foreground">{kit.font_heading}</span>
                    </div>
                  )}
                  {kit.target_audience && (
                    <div className="text-zinc-500">
                      Audience: <span className="text-foreground">{kit.target_audience}</span>
                    </div>
                  )}
                </div>
                {kit.brand_values.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {kit.brand_values.map((value) => (
                      <Badge key={value} variant="secondary">
                        {value}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingKit ? "Edit Brand Kit" : "Create Brand Kit"}
            </DialogTitle>
            <DialogDescription>
              {editingKit
                ? "Update your brand identity settings."
                : "Define your brand identity for consistent ad generation."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="bk-name">Name *</Label>
              <Input
                id="bk-name"
                placeholder="e.g. Main Brand"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="bk-default"
                checked={formData.is_default}
                onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                className="rounded border-zinc-300"
              />
              <Label htmlFor="bk-default">Set as default brand kit</Label>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-2">
                <Label htmlFor="bk-primary">Primary Color</Label>
                <Input
                  id="bk-primary"
                  placeholder="#FF5733"
                  value={formData.primary_color || ""}
                  onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bk-secondary">Secondary</Label>
                <Input
                  id="bk-secondary"
                  placeholder="#3498DB"
                  value={formData.secondary_color || ""}
                  onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bk-accent">Accent</Label>
                <Input
                  id="bk-accent"
                  placeholder="#2ECC71"
                  value={formData.accent_color || ""}
                  onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="bk-font-heading">Heading Font</Label>
                <Input
                  id="bk-font-heading"
                  placeholder="e.g. Inter"
                  value={formData.font_heading || ""}
                  onChange={(e) => setFormData({ ...formData, font_heading: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bk-font-body">Body Font</Label>
                <Input
                  id="bk-font-body"
                  placeholder="e.g. Roboto"
                  value={formData.font_body || ""}
                  onChange={(e) => setFormData({ ...formData, font_body: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bk-tone">Tone of Voice</Label>
              <Input
                id="bk-tone"
                placeholder="e.g. Professional yet friendly, confident"
                value={formData.tone_of_voice || ""}
                onChange={(e) => setFormData({ ...formData, tone_of_voice: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="bk-values">Brand Values (comma-separated)</Label>
              <Input
                id="bk-values"
                placeholder="e.g. Innovation, Trust, Quality"
                value={valuesInput}
                onChange={(e) => setValuesInput(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="bk-audience">Target Audience</Label>
              <Input
                id="bk-audience"
                placeholder="e.g. Tech-savvy millennials aged 25-40"
                value={formData.target_audience || ""}
                onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="bk-guidelines">Brand Guidelines</Label>
              <Input
                id="bk-guidelines"
                placeholder="e.g. Always use active voice, avoid jargon"
                value={formData.guidelines || ""}
                onChange={(e) => setFormData({ ...formData, guidelines: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="bk-logo">Logo URL</Label>
              <Input
                id="bk-logo"
                type="url"
                placeholder="https://example.com/logo.png"
                value={formData.logo_url || ""}
                onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isPending}>
              {isPending ? "Saving..." : editingKit ? "Update" : "Create"}
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
            <DialogTitle>Delete Brand Kit</DialogTitle>
            <DialogDescription>
              This action cannot be undone. Are you sure you want to delete this brand kit?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
              disabled={deleteBrandKit.isPending}
            >
              {deleteBrandKit.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
