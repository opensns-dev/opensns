"use client";

import { useState } from "react";
import { ArrowLeft, ArrowUpRight, Crown, Eye, Trash2 } from "lucide-react";
import { toast } from "sonner";
import {
  useWhiteLabelConfig,
  useCreateWhiteLabel,
  useUpdateWhiteLabel,
  useDeleteWhiteLabel,
  useActivateWhiteLabel,
  useDeactivateWhiteLabel,
} from "@/hooks/use-white-label";
import { useBillingOverview } from "@/hooks/use-billing";
import type { WhiteLabelConfigCreate, WhiteLabelConfigUpdate } from "@/types";
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

const DEFAULT_FORM: WhiteLabelConfigCreate = {
  brand_name: "",
  logo_url: null,
  favicon_url: null,
  primary_color: "#6366f1",
  secondary_color: "#8b5cf6",
  custom_domain: null,
  custom_css: null,
  email_from_name: null,
  email_from_address: null,
  hide_powered_by: false,
};

export default function WhiteLabelPage() {
  const { data: config, isLoading, error } = useWhiteLabelConfig();
  const { data: billing } = useBillingOverview();
  const createWhiteLabel = useCreateWhiteLabel();
  const updateWhiteLabel = useUpdateWhiteLabel();
  const deleteWhiteLabel = useDeleteWhiteLabel();
  const activateWhiteLabel = useActivateWhiteLabel();
  const deactivateWhiteLabel = useDeactivateWhiteLabel();

  const [formData, setFormData] = useState<WhiteLabelConfigCreate>(DEFAULT_FORM);
  const [hasEdited, setHasEdited] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const hasWhiteLabel = billing?.subscription?.tier === "ULTRA";
  const is404 = (error as { response?: { status?: number } })?.response?.status === 404;
  const configExists = !!config && !is404;

  const populateForm = (cfg: typeof config) => {
    if (!cfg) return;
    setFormData({
      brand_name: cfg.brand_name,
      logo_url: cfg.logo_url,
      favicon_url: cfg.favicon_url,
      primary_color: cfg.primary_color ?? "#6366f1",
      secondary_color: cfg.secondary_color ?? "#8b5cf6",
      custom_domain: cfg.custom_domain,
      custom_css: cfg.custom_css,
      email_from_name: cfg.email_from_name,
      email_from_address: cfg.email_from_address,
      hide_powered_by: cfg.hide_powered_by,
    });
  };

  const prevConfigRef = useState<string | null>(null);
  if (config && JSON.stringify(config) !== prevConfigRef[0]) {
    prevConfigRef[1](JSON.stringify(config));
    if (!hasEdited) {
      populateForm(config);
    }
  }

  const updateField = <K extends keyof WhiteLabelConfigCreate>(
    key: K,
    value: WhiteLabelConfigCreate[K],
  ) => {
    setHasEdited(true);
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    if (!formData.brand_name.trim()) {
      toast.error("Brand name is required");
      return;
    }

    try {
      if (configExists) {
        const update: WhiteLabelConfigUpdate = { ...formData };
        await updateWhiteLabel.mutateAsync(update);
        toast.success("White-label config updated");
      } else {
        await createWhiteLabel.mutateAsync(formData);
        toast.success("White-label config created");
      }
      setHasEdited(false);
    } catch {
      toast.error("Failed to save white-label config");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteWhiteLabel.mutateAsync();
      setDeleteOpen(false);
      setFormData(DEFAULT_FORM);
      setHasEdited(false);
      toast.success("White-label config deleted");
    } catch {
      toast.error("Failed to delete white-label config");
    }
  };

  const handleToggleActive = async () => {
    try {
      if (config?.is_active) {
        await deactivateWhiteLabel.mutateAsync();
        toast.success("White-label deactivated");
      } else {
        await activateWhiteLabel.mutateAsync();
        toast.success("White-label activated");
      }
    } catch {
      toast.error("Failed to toggle white-label status");
    }
  };

  const isSaving = createWhiteLabel.isPending || updateWhiteLabel.isPending;

  if (isLoading) {
    return (
      <div className="container max-w-4xl py-8 space-y-6">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Button variant="ghost" size="sm" asChild className="h-8 w-8 p-0">
              <a href="/settings">
                <ArrowLeft className="h-4 w-4" />
              </a>
            </Button>
            <h1 className="text-2xl font-bold">White Label</h1>
          </div>
          <p className="text-zinc-600 dark:text-zinc-400 ml-10">
            Customize branding for your white-label deployment
          </p>
        </div>
        {configExists && (
          <div className="flex items-center gap-2">
            <Badge variant={config.is_active ? "default" : "secondary"}>
              {config.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
        )}
      </div>

      {!hasWhiteLabel && (
        <Card className="border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30">
          <CardHeader>
            <div className="flex items-center gap-3">
              <Crown className="h-6 w-6 text-amber-600 dark:text-amber-400" />
              <div>
                <CardTitle className="text-lg">ULTRA Plan Required</CardTitle>
                <CardDescription className="text-amber-800 dark:text-amber-200">
                  White-label customization is available exclusively on the ULTRA plan.
                  Upgrade to remove OpenSNS branding and use your own domain.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <a href="/settings/billing">
                <ArrowUpRight className="h-4 w-4 mr-2" />
                Upgrade to ULTRA
              </a>
            </Button>
          </CardContent>
        </Card>
      )}

      {hasWhiteLabel && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Brand Settings</CardTitle>
              <CardDescription>
                Configure how your platform appears to your users
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="wl-brand-name">Brand Name *</Label>
                <Input
                  id="wl-brand-name"
                  placeholder="Your Brand"
                  value={formData.brand_name}
                  onChange={(e) => updateField("brand_name", e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="wl-logo">Logo URL</Label>
                  <Input
                    id="wl-logo"
                    type="url"
                    placeholder="https://example.com/logo.png"
                    value={formData.logo_url ?? ""}
                    onChange={(e) => updateField("logo_url", e.target.value || null)}
                  />
                  {formData.logo_url && (
                    <img
                      src={formData.logo_url}
                      alt="Logo preview"
                      className="h-10 w-10 rounded object-contain border border-zinc-200 dark:border-zinc-700"
                    />
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="wl-favicon">Favicon URL</Label>
                  <Input
                    id="wl-favicon"
                    type="url"
                    placeholder="https://example.com/favicon.ico"
                    value={formData.favicon_url ?? ""}
                    onChange={(e) => updateField("favicon_url", e.target.value || null)}
                  />
                  {formData.favicon_url && (
                    <img
                      src={formData.favicon_url}
                      alt="Favicon preview"
                      className="h-6 w-6 rounded object-contain border border-zinc-200 dark:border-zinc-700"
                    />
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="wl-primary">Primary Color</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      id="wl-primary"
                      value={formData.primary_color ?? "#6366f1"}
                      onChange={(e) => updateField("primary_color", e.target.value)}
                      className="h-10 w-10 rounded border border-zinc-300 dark:border-zinc-600 cursor-pointer bg-transparent p-0.5"
                    />
                    <Input
                      value={formData.primary_color ?? ""}
                      onChange={(e) => updateField("primary_color", e.target.value)}
                      placeholder="#6366f1"
                      className="flex-1"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="wl-secondary">Secondary Color</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      id="wl-secondary"
                      value={formData.secondary_color ?? "#8b5cf6"}
                      onChange={(e) => updateField("secondary_color", e.target.value)}
                      className="h-10 w-10 rounded border border-zinc-300 dark:border-zinc-600 cursor-pointer bg-transparent p-0.5"
                    />
                    <Input
                      value={formData.secondary_color ?? ""}
                      onChange={(e) => updateField("secondary_color", e.target.value)}
                      placeholder="#8b5cf6"
                      className="flex-1"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="wl-domain">Custom Domain</Label>
                <Input
                  id="wl-domain"
                  placeholder="app.yourbrand.com"
                  value={formData.custom_domain ?? ""}
                  onChange={(e) => updateField("custom_domain", e.target.value || null)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="wl-css">Custom CSS</Label>
                <textarea
                  id="wl-css"
                  placeholder=".header { background: #000; }"
                  value={formData.custom_css ?? ""}
                  onChange={(e) => updateField("custom_css", e.target.value || null)}
                  rows={4}
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="wl-email-name">Email From Name</Label>
                  <Input
                    id="wl-email-name"
                    placeholder="Your Brand"
                    value={formData.email_from_name ?? ""}
                    onChange={(e) => updateField("email_from_name", e.target.value || null)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="wl-email-address">Email From Address</Label>
                  <Input
                    id="wl-email-address"
                    type="email"
                    placeholder="noreply@yourbrand.com"
                    value={formData.email_from_address ?? ""}
                    onChange={(e) => updateField("email_from_address", e.target.value || null)}
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="wl-hide-powered"
                  checked={formData.hide_powered_by ?? false}
                  onChange={(e) => updateField("hide_powered_by", e.target.checked)}
                  className="rounded border-zinc-300"
                />
                <Label htmlFor="wl-hide-powered">
                  Hide &quot;Powered by OpenSNS&quot; branding
                </Label>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <Button onClick={handleSave} disabled={isSaving}>
                  {isSaving ? "Saving..." : configExists ? "Update Config" : "Create Config"}
                </Button>
                {configExists && (
                  <>
                    <Button
                      variant={config.is_active ? "outline" : "default"}
                      onClick={handleToggleActive}
                      disabled={activateWhiteLabel.isPending || deactivateWhiteLabel.isPending}
                    >
                      {config.is_active ? "Deactivate" : "Activate"}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setDeleteOpen(true)}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {configExists && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  <CardTitle className="text-lg">Preview</CardTitle>
                </div>
                <CardDescription>
                  A preview of how your branding will appear
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="rounded-lg border border-zinc-200 dark:border-zinc-700 overflow-hidden"
                  style={{ borderTopColor: formData.primary_color ?? "#6366f1", borderTopWidth: 4 }}
                >
                  <div className="p-4 flex items-center gap-3" style={{ backgroundColor: `${formData.primary_color ?? "#6366f1"}10` }}>
                    {formData.logo_url ? (
                      <img
                        src={formData.logo_url}
                        alt="Logo"
                        className="h-8 w-8 rounded object-contain"
                      />
                    ) : (
                      <div
                        className="h-8 w-8 rounded flex items-center justify-center text-white text-xs font-bold"
                        style={{ backgroundColor: formData.primary_color ?? "#6366f1" }}
                      >
                        {formData.brand_name?.charAt(0)?.toUpperCase() || "B"}
                      </div>
                    )}
                    <span className="font-semibold text-lg">
                      {formData.brand_name || "Your Brand"}
                    </span>
                  </div>
                  <div className="p-4 space-y-2">
                    <div className="flex gap-2">
                      <div
                        className="rounded px-3 py-1.5 text-white text-sm font-medium"
                        style={{ backgroundColor: formData.primary_color ?? "#6366f1" }}
                      >
                        Primary Action
                      </div>
                      <div
                        className="rounded px-3 py-1.5 text-white text-sm font-medium"
                        style={{ backgroundColor: formData.secondary_color ?? "#8b5cf6" }}
                      >
                        Secondary Action
                      </div>
                    </div>
                    {!formData.hide_powered_by && (
                      <p className="text-xs text-zinc-400 pt-2">Powered by OpenSNS</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete White-Label Config</DialogTitle>
            <DialogDescription>
              This will permanently delete your white-label configuration. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteWhiteLabel.isPending}
            >
              {deleteWhiteLabel.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
