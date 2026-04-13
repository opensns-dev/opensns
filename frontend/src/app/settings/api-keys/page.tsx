"use client";

import { useState } from "react";
import { Plus, Copy, Check, Key, ArrowLeft, ArrowUpRight } from "lucide-react";
import { toast } from "sonner";
import {
  useApiKeys,
  useCreateApiKey,
  useRevokeApiKey,
} from "@/hooks/use-api-keys";
import { useBillingOverview } from "@/hooks/use-billing";
import type { ApiKeyCreate, ApiKeyCreated } from "@/types";
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

const SCOPES = ["read", "write"] as const;

const EXPIRY_OPTIONS = [
  { value: "30", label: "30 days" },
  { value: "60", label: "60 days" },
  { value: "90", label: "90 days" },
  { value: "365", label: "365 days" },
  { value: "never", label: "Never" },
];

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function maskKey(prefix: string) {
  return `${prefix}...`;
}

export default function ApiKeysPage() {
  const { data: apiKeys, isLoading } = useApiKeys();
  const { data: billing } = useBillingOverview();
  const createApiKey = useCreateApiKey();
  const revokeApiKey = useRevokeApiKey();

  const [createOpen, setCreateOpen] = useState(false);
  const [revokeConfirmId, setRevokeConfirmId] = useState<number | null>(null);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);

  const [formName, setFormName] = useState("");
  const [formScopes, setFormScopes] = useState<Set<string>>(
    new Set(["read", "write"])
  );
  const [formExpiry, setFormExpiry] = useState("never");

  const hasApiAccess = billing?.subscription?.tier === "PRO" || billing?.subscription?.tier === "ULTRA";

  const openCreateDialog = () => {
    setFormName("");
    setFormScopes(new Set(["read", "write"]));
    setFormExpiry("never");
    setCreateOpen(true);
  };

  const handleCreate = async () => {
    if (!formName.trim()) {
      toast.error("Name is required");
      return;
    }

    const payload: ApiKeyCreate = {
      name: formName.trim(),
      scopes: Array.from(formScopes).join(","),
      expires_in_days:
        formExpiry === "never" ? null : parseInt(formExpiry, 10),
    };

    try {
      const result = await createApiKey.mutateAsync(payload);
      setCreateOpen(false);
      setCreatedKey(result);
    } catch {
      toast.error("Failed to create API key");
    }
  };

  const handleRevoke = async (id: number) => {
    try {
      await revokeApiKey.mutateAsync(id);
      setRevokeConfirmId(null);
      toast.success("API key revoked");
    } catch {
      toast.error("Failed to revoke API key");
    }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleScope = (scope: string) => {
    setFormScopes((prev) => {
      const next = new Set(prev);
      if (next.has(scope)) {
        next.delete(scope);
      } else {
        next.add(scope);
      }
      return next;
    });
  };

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
            <h1 className="text-2xl font-bold">API Keys</h1>
          </div>
          <p className="text-zinc-600 dark:text-zinc-400 ml-10">
            Manage API keys for programmatic access to OpenSNS
          </p>
        </div>
        {hasApiAccess ? (
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Create API Key
          </Button>
        ) : (
          <Button asChild>
            <a href="/settings/billing">
              <ArrowUpRight className="h-4 w-4 mr-2" />
              Upgrade to PRO
            </a>
          </Button>
        )}
      </div>

      {!hasApiAccess && (
        <Card className="border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30">
          <CardContent className="flex items-center gap-3 py-4">
            <Key className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0" />
            <p className="text-sm text-amber-800 dark:text-amber-200">
              API access is available on PRO and ULTRA plans. Upgrade your plan
              to create and manage API keys.
            </p>
          </CardContent>
        </Card>
      )}

      {!apiKeys?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Key className="h-12 w-12 text-zinc-400 mb-4" />
            <h3 className="text-lg font-semibold mb-1">No API keys yet</h3>
            <p className="text-zinc-500 dark:text-zinc-400 mb-4">
              Create an API key to access the OpenSNS API programmatically.
            </p>
            {hasApiAccess && (
              <Button onClick={openCreateDialog}>
                <Plus className="h-4 w-4 mr-2" />
                Create API Key
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Your API Keys</CardTitle>
            <CardDescription>
              Keys are used to authenticate API requests. Revoked keys cannot be
              reactivated.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Scopes</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs dark:bg-zinc-800">
                        {maskKey(key.key_prefix)}
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {key.scopes.split(",").map((scope) => (
                          <Badge key={scope} variant="secondary" className="text-xs">
                            {scope}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      {key.is_active ? (
                        <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-zinc-500">
                          Revoked
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-zinc-500 text-sm">
                      {formatDate(key.last_used_at)}
                    </TableCell>
                    <TableCell className="text-zinc-500 text-sm">
                      {formatDate(key.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      {key.is_active && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-600"
                          onClick={() => setRevokeConfirmId(key.id)}
                        >
                          Revoke
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create API Key</DialogTitle>
            <DialogDescription>
              Generate a new API key for programmatic access.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="key-name">Name *</Label>
              <Input
                id="key-name"
                placeholder="e.g. Production Server"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Scopes</Label>
              <div className="flex gap-3">
                {SCOPES.map((scope) => (
                  <label key={scope} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formScopes.has(scope)}
                      onChange={() => toggleScope(scope)}
                      className="rounded border-zinc-300"
                    />
                    <span className="text-sm capitalize">{scope}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Expiration</Label>
              <Select value={formExpiry} onValueChange={setFormExpiry}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EXPIRY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={createApiKey.isPending}>
              {createApiKey.isPending ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={createdKey !== null}
        onOpenChange={() => setCreatedKey(null)}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>API Key Created</DialogTitle>
            <DialogDescription>
              Copy your API key now. This key won&apos;t be shown again.
            </DialogDescription>
          </DialogHeader>

          {createdKey && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>API Key</Label>
                <div className="flex gap-2">
                  <Input
                    readOnly
                    value={createdKey.key}
                    className="font-mono text-sm"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleCopy(createdKey.key)}
                  >
                    {copied ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
                Make sure to copy your API key now. You won&apos;t be able to
                see it again.
              </div>
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setCreatedKey(null)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={revokeConfirmId !== null}
        onOpenChange={() => setRevokeConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Revoke API Key</DialogTitle>
            <DialogDescription>
              This action cannot be undone. Any applications using this key will
              lose access immediately.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRevokeConfirmId(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => revokeConfirmId && handleRevoke(revokeConfirmId)}
              disabled={revokeApiKey.isPending}
            >
              {revokeApiKey.isPending ? "Revoking..." : "Revoke Key"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
