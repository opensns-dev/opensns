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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import {
  useVariants,
  useCreateVariant,
  useAutoGenerateVariants,
  useUpdateVariant,
  useDeleteVariant,
} from "@/hooks/use-variants";
import type { AdVariant, AdVariantCreate } from "@/types";

const LABEL_COLORS: Record<string, string> = {
  A: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  B: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  C: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  D: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  E: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
};

function VariantFormFields({
  form,
  onChange,
}: {
  form: AdVariantCreate;
  onChange: (field: keyof AdVariantCreate, value: string | boolean) => void;
}) {
  return (
    <div className="grid gap-4 py-4">
      <div className="grid gap-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={form.name}
          onChange={(e) => onChange("name", e.target.value)}
          placeholder="e.g. Emotional hook variant"
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="variant_label">Label (A-E)</Label>
        <Input
          id="variant_label"
          value={form.variant_label ?? ""}
          onChange={(e) => onChange("variant_label", e.target.value)}
          placeholder="A"
          maxLength={1}
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="copy_headline">Headline</Label>
        <Input
          id="copy_headline"
          value={form.copy_headline ?? ""}
          onChange={(e) => onChange("copy_headline", e.target.value)}
          placeholder="Ad headline"
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="copy_body">Body</Label>
        <Input
          id="copy_body"
          value={form.copy_body ?? ""}
          onChange={(e) => onChange("copy_body", e.target.value)}
          placeholder="Ad body copy"
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="copy_cta">CTA</Label>
        <Input
          id="copy_cta"
          value={form.copy_cta ?? ""}
          onChange={(e) => onChange("copy_cta", e.target.value)}
          placeholder="Shop Now"
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="platform">Platform</Label>
        <Input
          id="platform"
          value={form.platform ?? ""}
          onChange={(e) => onChange("platform", e.target.value)}
          placeholder="instagram, facebook, etc."
        />
      </div>
    </div>
  );
}

const EMPTY_FORM: AdVariantCreate = {
  name: "",
  variant_label: "A",
  copy_headline: "",
  copy_body: "",
  copy_cta: "",
  platform: "",
  is_control: false,
};

function ComparisonView({ variants }: { variants: AdVariant[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Side-by-Side Comparison</CardTitle>
        <CardDescription>Compare variant copy across all variants</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-32">Field</TableHead>
                {variants.map((v) => (
                  <TableHead key={v.id}>
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium ${LABEL_COLORS[v.variant_label] ?? "bg-gray-100 text-gray-800"}`}
                      >
                        {v.variant_label}
                      </span>
                      {v.name}
                      {v.is_control && (
                        <Badge variant="outline" className="text-xs">
                          Control
                        </Badge>
                      )}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium">Headline</TableCell>
                {variants.map((v) => (
                  <TableCell key={v.id}>
                    {v.copy_headline || (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Body</TableCell>
                {variants.map((v) => (
                  <TableCell key={v.id} className="max-w-xs">
                    <p className="line-clamp-3">
                      {v.copy_body || (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </p>
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">CTA</TableCell>
                {variants.map((v) => (
                  <TableCell key={v.id}>
                    {v.copy_cta || (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Platform</TableCell>
                {variants.map((v) => (
                  <TableCell key={v.id}>
                    {v.platform ? (
                      <Badge variant="secondary">{v.platform}</Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

export default function VariantsPage() {
  const params = useParams<{ id: string }>();
  const campaignId = Number(params.id);

  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingVariant, setEditingVariant] = useState<AdVariant | null>(null);
  const [form, setForm] = useState<AdVariantCreate>({ ...EMPTY_FORM });

  const { data: campaign, isLoading: campaignLoading } =
    useCampaign(campaignId);
  const { data: variants, isLoading: variantsLoading } =
    useVariants(campaignId);

  const createVariant = useCreateVariant(campaignId);
  const autoGenerate = useAutoGenerateVariants(campaignId);
  const updateVariant = useUpdateVariant(campaignId);
  const deleteVariant = useDeleteVariant(campaignId);

  const handleFormChange = (
    field: keyof AdVariantCreate,
    value: string | boolean
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreate = async () => {
    if (!form.name.trim()) {
      toast.error("Name is required");
      return;
    }
    try {
      await createVariant.mutateAsync(form);
      toast.success("Variant created");
      setForm({ ...EMPTY_FORM });
      setAddOpen(false);
    } catch {
      toast.error("Failed to create variant");
    }
  };

  const handleAutoGenerate = async () => {
    try {
      const result = await autoGenerate.mutateAsync();
      toast.success(`Generated ${result.length} variants`);
    } catch {
      toast.error("Failed to auto-generate variants");
    }
  };

  const handleEditOpen = (variant: AdVariant) => {
    setEditingVariant(variant);
    setForm({
      name: variant.name,
      variant_label: variant.variant_label,
      copy_headline: variant.copy_headline ?? "",
      copy_body: variant.copy_body ?? "",
      copy_cta: variant.copy_cta ?? "",
      platform: variant.platform ?? "",
      is_control: variant.is_control,
    });
    setEditOpen(true);
  };

  const handleUpdate = async () => {
    if (!editingVariant || !form.name.trim()) {
      toast.error("Name is required");
      return;
    }
    try {
      await updateVariant.mutateAsync({
        variantId: editingVariant.id,
        data: form,
      });
      toast.success("Variant updated");
      setEditOpen(false);
      setEditingVariant(null);
    } catch {
      toast.error("Failed to update variant");
    }
  };

  const handleDelete = async (variantId: number) => {
    try {
      await deleteVariant.mutateAsync(variantId);
      toast.success("Variant deleted");
    } catch {
      toast.error("Failed to delete variant");
    }
  };

  if (campaignLoading) {
    return (
      <div className="flex flex-col gap-6 p-6 max-w-5xl mx-auto">
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

  return (
    <div className="flex flex-col gap-6 p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{campaign.title}</h1>
          <p className="text-muted-foreground">A/B Test Variants</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleAutoGenerate}
            disabled={autoGenerate.isPending}
          >
            {autoGenerate.isPending ? "Generating..." : "Auto-Generate Variants"}
          </Button>
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogTrigger asChild>
              <Button>Add Variant</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Variant</DialogTitle>
                <DialogDescription>
                  Create a new ad variant for A/B testing
                </DialogDescription>
              </DialogHeader>
              <VariantFormFields form={form} onChange={handleFormChange} />
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setAddOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreate}
                  disabled={createVariant.isPending}
                >
                  {createVariant.isPending ? "Creating..." : "Create"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Link href="/campaigns">
            <Button variant="outline">Back</Button>
          </Link>
        </div>
      </div>

      {variantsLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-[200px] rounded-xl" />
          <Skeleton className="h-[200px] rounded-xl" />
        </div>
      ) : variants && variants.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {variants.map((variant) => (
              <Card key={variant.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-bold ${LABEL_COLORS[variant.variant_label] ?? "bg-gray-100 text-gray-800"}`}
                      >
                        {variant.variant_label}
                      </span>
                      <CardTitle className="text-base">
                        {variant.name}
                      </CardTitle>
                    </div>
                    <div className="flex items-center gap-1">
                      {variant.is_control && (
                        <Badge variant="outline">Control</Badge>
                      )}
                      {variant.platform && (
                        <Badge variant="secondary">{variant.platform}</Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {variant.copy_headline && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Headline
                      </p>
                      <p className="text-sm font-semibold">
                        {variant.copy_headline}
                      </p>
                    </div>
                  )}
                  {variant.copy_body && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Body
                      </p>
                      <p className="text-sm line-clamp-3">
                        {variant.copy_body}
                      </p>
                    </div>
                  )}
                  {variant.copy_cta && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        CTA
                      </p>
                      <Badge>{variant.copy_cta}</Badge>
                    </div>
                  )}
                  <div className="flex items-center gap-2 pt-2 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditOpen(variant)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(variant.id)}
                      disabled={deleteVariant.isPending}
                      className="text-destructive hover:text-destructive"
                    >
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {variants.length >= 2 && <ComparisonView variants={variants} />}
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 gap-4">
            <p className="text-muted-foreground">
              No variants yet. Auto-generate from campaign assets or add
              manually.
            </p>
            <Button onClick={handleAutoGenerate} disabled={autoGenerate.isPending}>
              {autoGenerate.isPending
                ? "Generating..."
                : "Auto-Generate Variants"}
            </Button>
          </CardContent>
        </Card>
      )}

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Variant</DialogTitle>
            <DialogDescription>
              Update this ad variant
            </DialogDescription>
          </DialogHeader>
          <VariantFormFields form={form} onChange={handleFormChange} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={updateVariant.isPending}
            >
              {updateVariant.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
