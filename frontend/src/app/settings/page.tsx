"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor, CreditCard, AlertCircle, User, Mic, Video, Key, Link2, Check, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useSettings, useUpdateSettings, useTestConnection } from "@/hooks/use-settings";
import { useTTSVoices } from "@/hooks/use-audio";
import { useUGCEngines, useAvatars, useVoices } from "@/hooks/use-ugc";
import {
  useSaveProviderCredential,
  useRemoveProviderCredential,
  useTestProviderCredential,
  useTestProviderCompatibility,
  useGroupedProviders,
} from "@/hooks/use-providers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  ProviderRegistryItem,
  ProviderCredentialSummary,
  ProviderCredentialTestResult,
  ProviderType,
} from "@/types";

type ProviderTestStatus = "idle" | "success" | "error";

interface ProviderTestState {
  status: ProviderTestStatus;
  message: string;
  testedAt?: string;
  source: "persisted" | "manual";
}

function buildPersistedConnectionState(
  credential?: ProviderCredentialSummary
): ProviderTestState | null {
  if (!credential?.last_tested_at || credential.last_test_success === undefined) {
    return null;
  }

  return {
    status: credential.last_test_success ? "success" : "error",
    message: credential.last_test_success
      ? "Last saved connection check passed."
      : "Last saved connection check failed.",
    testedAt: credential.last_tested_at,
    source: "persisted",
  };
}

function buildManualTestState(result: ProviderCredentialTestResult): ProviderTestState {
  return {
    status: result.success ? "success" : "error",
    message: result.message,
    testedAt: new Date().toISOString(),
    source: "manual",
  };
}

function getStatusBadgeVariant(status: ProviderTestStatus): "secondary" | "destructive" | "outline" {
  if (status === "success") {
    return "secondary";
  }

  if (status === "error") {
    return "destructive";
  }

  return "outline";
}

function formatTestTimestamp(value?: string): string | null {
  if (!value) {
    return null;
  }

  const parsedDate = new Date(value);

  if (Number.isNaN(parsedDate.getTime())) {
    return null;
  }

  return parsedDate.toLocaleString();
}

interface ProviderTestStatusRowProps {
  label: string;
  pendingLabel: string;
  pending: boolean;
  result: ProviderTestState | null;
  emptyMessage: string;
}

function ProviderTestStatusRow({
  label,
  pendingLabel,
  pending,
  result,
  emptyMessage,
}: ProviderTestStatusRowProps) {
  const badgeLabel = pending
    ? pendingLabel
    : result?.status === "success"
      ? "Passed"
      : result?.status === "error"
        ? "Failed"
        : "Not run";
  const badgeVariant = pending ? "outline" : getStatusBadgeVariant(result?.status ?? "idle");
  const timestamp = formatTestTimestamp(result?.testedAt);

  return (
    <div className="flex items-start justify-between gap-3 rounded-md border bg-muted/30 px-3 py-2">
      <div className="min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <Badge variant={badgeVariant} className="gap-1">
            {pending ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
            {badgeLabel}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {pending ? "Running check..." : result?.message ?? emptyMessage}
        </p>
      </div>
      {timestamp ? (
        <span className="shrink-0 text-[11px] text-muted-foreground/80">{timestamp}</span>
      ) : null}
    </div>
  );
}

// Provider Card Component for credential management
interface ProviderCardProps {
  provider: ProviderRegistryItem;
  credential?: ProviderCredentialSummary;
}

function ProviderCard({ provider, credential }: ProviderCardProps) {
  const [apiKey, setApiKey] = useState("");
  const [url, setUrl] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [connectionResult, setConnectionResult] = useState<ProviderTestState | null>(() =>
    buildPersistedConnectionState(credential)
  );
  const [compatibilityResult, setCompatibilityResult] = useState<ProviderTestState | null>(null);

  const saveCredential = useSaveProviderCredential();
  const removeCredential = useRemoveProviderCredential();
  const testCredential = useTestProviderCredential();
  const testCompatibility = useTestProviderCompatibility();

  const isConfigured = credential?.is_configured ?? false;
  const hasSharedCredentials = provider.shared_credentials_with && provider.shared_credentials_with.length > 0;
  const canRunCompatibilityTest = provider.requires_url || provider.is_local;

  useEffect(() => {
    if (!isConfigured) {
      setConnectionResult(null);
      setCompatibilityResult(null);
      return;
    }

    const persistedConnectionState = buildPersistedConnectionState(credential);

    if (!persistedConnectionState) {
      return;
    }

    setConnectionResult((current) => {
      if (current?.source === "manual") {
        return current;
      }

      return persistedConnectionState;
    });
  }, [credential, isConfigured]);

  const handleSave = async () => {
    try {
      await saveCredential.mutateAsync({
        provider_name: provider.name,
        credential_key: apiKey || undefined,
        endpoint_url: url || undefined,
      });
      setApiKey("");
      setUrl("");
      toast.success(`${provider.display_name} credentials saved`);
    } catch {
      toast.error(`Failed to save ${provider.display_name} credentials`);
    }
  };

  const handleRemove = async () => {
    try {
      await removeCredential.mutateAsync(provider.name);
      toast.success(`${provider.display_name} credentials removed`);
    } catch {
      toast.error(`Failed to remove ${provider.display_name} credentials`);
    }
  };

  const handleTestConnection = async () => {
    try {
      const result = await testCredential.mutateAsync(provider.name);
      setConnectionResult(buildManualTestState(result));

      if (result.success) {
        toast.success(`${provider.display_name} connection successful`, {
          description: result.message,
        });
      } else {
        toast.error(`${provider.display_name} connection failed`, {
          description: result.message,
        });
      }
    } catch {
      toast.error(`${provider.display_name} connection test failed`);
    }
  };

  const handleTestCompatibility = async () => {
    try {
      const result = await testCompatibility.mutateAsync(provider.name);
      setCompatibilityResult(buildManualTestState(result));

      if (result.success) {
        toast.success(`${provider.display_name} compatibility successful`, {
          description: result.message,
        });
      } else {
        toast.error(`${provider.display_name} compatibility failed`, {
          description: result.message,
        });
      }
    } catch {
      toast.error(`${provider.display_name} compatibility test failed`);
    }
  };

  // Skip rendering if this provider uses shared credentials and is not the primary
  if (hasSharedCredentials && provider.shared_credentials_note) {
    return (
      <div className="rounded-lg border bg-muted/50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium">{provider.display_name}</h4>
            <p className="text-sm text-muted-foreground">{provider.shared_credentials_note}</p>
          </div>
          {isConfigured ? (
            <Badge variant="secondary" className="flex items-center gap-1">
              <Check className="h-3 w-3" />
              Configured
            </Badge>
          ) : (
            <Badge variant="outline">Not configured</Badge>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-4 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-medium">{provider.display_name}</h4>
          <p className="text-sm text-muted-foreground">{provider.description}</p>
        </div>
        {isConfigured ? (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Check className="h-3 w-3" />
            Configured
          </Badge>
        ) : (
          <Badge variant="outline">Not configured</Badge>
        )}
      </div>

      {/* Input fields for credentials */}
      {(provider.requires_key || provider.requires_url) && !isConfigured && (
        <div className="space-y-3">
          {provider.requires_key && (
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-sm">
                <Key className="h-3 w-3" />
                API Key
              </Label>
              <div className="flex gap-2">
                <Input
                  type={showKey ? "text" : "password"}
                  placeholder={provider.key_placeholder || "Enter API key"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setShowKey(!showKey)}
                >
                  {showKey ? <X className="h-4 w-4" /> : <Key className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          )}

          {provider.requires_url && (
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-sm">
                <Link2 className="h-3 w-3" />
                URL
              </Label>
              <Input
                type="url"
                placeholder={provider.url_placeholder || "http://localhost:..."}
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2">
        {!isConfigured ? (
          <Button
            size="sm"
            onClick={handleSave}
            disabled={saveCredential.isPending || (!apiKey && !url)}
          >
            {saveCredential.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-1" />
            ) : null}
            Save
          </Button>
        ) : (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={handleTestConnection}
              disabled={testCredential.isPending || testCompatibility.isPending}
            >
              {testCredential.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : null}
              Test connection
            </Button>
            {canRunCompatibilityTest ? (
              <Button
                size="sm"
                variant="outline"
                onClick={handleTestCompatibility}
                disabled={testCompatibility.isPending || testCredential.isPending}
              >
                {testCompatibility.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : null}
                Test compatibility
              </Button>
            ) : null}
            <Button
              size="sm"
              variant="destructive"
              onClick={handleRemove}
              disabled={removeCredential.isPending}
            >
              {removeCredential.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : null}
              Remove
            </Button>
          </>
        )}
      </div>

      {isConfigured ? (
        <div className="space-y-2 border-t pt-3">
          <ProviderTestStatusRow
            label="Connection"
            pendingLabel="Testing"
            pending={testCredential.isPending}
            result={connectionResult}
            emptyMessage="No connection check has been run yet."
          />
          {canRunCompatibilityTest ? (
            <ProviderTestStatusRow
              label="Compatibility"
              pendingLabel="Testing"
              pending={testCompatibility.isPending}
              result={compatibilityResult}
              emptyMessage="No compatibility check has been run yet."
            />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default function SettingsPage() {
  const { data: settings, isLoading, error } = useSettings();
  const updateSettings = useUpdateSettings();
  const testConnection = useTestConnection();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Provider registry data
  const { grouped, isLoading: providersLoading } = useGroupedProviders();

  const [formData, setFormData] = useState({
    default_llm_engine: "openai",
    default_image_engine: "fal",
    default_video_engine: "fal-video",
    default_ugc_engine: "",
    ugc_enabled: false,
    ugc_avatar_id: "",
    ugc_voice_id: "",
    tts_enabled: false,
    default_tts_engine: "",
    tts_voice_id: "",
    bgm_enabled: false,
    default_bgm_engine: "",
    bgm_style: "",
    default_stt_engine: "",
    ollama_url: "",
    comfyui_url: "",
    sadtalker_url: "",
    // Legacy fields for backward compatibility
    openai_api_key: "",
    anthropic_api_key: "",
    google_api_key: "",
    groq_api_key: "",
    fal_api_key: "",
    firecrawl_api_key: "",
    heygen_api_key: "",
    did_api_key: "",
  });

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({
    openai_api_key: false,
    anthropic_api_key: false,
    google_api_key: false,
    groq_api_key: false,
    fal_api_key: false,
    firecrawl_api_key: false,
    heygen_api_key: false,
    did_api_key: false,
  });

  const { data: enginesData, isLoading: enginesLoading } = useUGCEngines();
  const { data: avatarsData, isLoading: avatarsLoading } = useAvatars(formData.default_ugc_engine);
  const { data: voicesData, isLoading: voicesLoading } = useVoices(formData.default_ugc_engine);
  const { data: ttsVoicesData, isLoading: ttsVoicesLoading } = useTTSVoices(
    formData.tts_enabled ? formData.default_tts_engine : null
  );

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (settings) {
      setFormData((prev) => ({
        ...prev,
        default_llm_engine: settings.default_llm_engine || "openai",
        default_image_engine: settings.default_image_engine || "fal",
        default_video_engine: settings.default_video_engine || "fal-video",
        default_ugc_engine: settings.default_ugc_engine || "",
        ugc_enabled: settings.ugc_enabled || false,
        ugc_avatar_id: settings.ugc_avatar_id || "",
        ugc_voice_id: settings.ugc_voice_id || "",
        tts_enabled: settings.tts_enabled || false,
        default_tts_engine: settings.default_tts_engine || "",
        tts_voice_id: settings.tts_voice_id || "",
        bgm_enabled: settings.bgm_enabled || false,
        default_bgm_engine: settings.default_bgm_engine || "",
        bgm_style: settings.bgm_style || "",
        default_stt_engine: settings.default_stt_engine || "",
        ollama_url: settings.ollama_url || "",
        comfyui_url: settings.comfyui_url || "",
        sadtalker_url: settings.sadtalker_url || "",
      }));
    }
  }, [settings]);

  const handleSave = async () => {
    try {
      const dataToSend: Record<string, string | boolean> = {
        default_llm_engine: formData.default_llm_engine,
        default_image_engine: formData.default_image_engine,
        default_video_engine: formData.default_video_engine,
        default_ugc_engine: formData.default_ugc_engine,
        ugc_enabled: formData.ugc_enabled,
        ugc_avatar_id: formData.ugc_avatar_id,
        ugc_voice_id: formData.ugc_voice_id,
        tts_enabled: formData.tts_enabled,
        default_tts_engine: formData.default_tts_engine,
        tts_voice_id: formData.tts_voice_id,
        bgm_enabled: formData.bgm_enabled,
        default_bgm_engine: formData.default_bgm_engine,
        bgm_style: formData.bgm_style,
        default_stt_engine: formData.default_stt_engine,
        ollama_url: formData.ollama_url,
        comfyui_url: formData.comfyui_url,
        sadtalker_url: formData.sadtalker_url,
      };

      // Only include non-empty API keys for backward compatibility
      if (formData.openai_api_key) dataToSend.openai_api_key = formData.openai_api_key;
      if (formData.anthropic_api_key) dataToSend.anthropic_api_key = formData.anthropic_api_key;
      if (formData.google_api_key) dataToSend.google_api_key = formData.google_api_key;
      if (formData.groq_api_key) dataToSend.groq_api_key = formData.groq_api_key;
      if (formData.fal_api_key) dataToSend.fal_api_key = formData.fal_api_key;
      if (formData.firecrawl_api_key) dataToSend.firecrawl_api_key = formData.firecrawl_api_key;
      if (formData.heygen_api_key) dataToSend.heygen_api_key = formData.heygen_api_key;
      if (formData.did_api_key) dataToSend.did_api_key = formData.did_api_key;

      await updateSettings.mutateAsync(dataToSend);
      
      setFormData((prev) => ({
        ...prev,
        openai_api_key: "",
        anthropic_api_key: "",
        google_api_key: "",
        groq_api_key: "",
        fal_api_key: "",
        firecrawl_api_key: "",
        heygen_api_key: "",
        did_api_key: "",
      }));
      
      toast.success("Settings saved", {
        description: "Your preferences have been updated.",
      });
    } catch {
      toast.error("Failed to save settings", {
        description: "Please try again.",
      });
    }
  };

  const handleTestConnection = async () => {
    try {
      const result = await testConnection.mutateAsync();
      if (result.openai && result.fal) {
        toast.success("All connections successful", {
          description: "OpenAI and Fal.ai are connected.",
        });
      } else {
        toast.warning("Partial connection", {
          description: `OpenAI: ${result.openai ? "✓" : "✗"} | Fal.ai: ${result.fal ? "✓" : "✗"}`,
        });
      }
    } catch {
      toast.error("Connection test failed", {
        description: "Please check your API keys.",
      });
    }
  };

  const toggleKeyVisibility = (key: string) => {
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Build engine options from provider registry
  const getEngineOptions = (type: ProviderType) => {
    return grouped[type].map(({ provider, credential }) => ({
      value: provider.name,
      label: provider.display_name,
      isConfigured: credential?.is_configured ?? false,
    }));
  };

  const renderEngineCard = (
    title: string,
    description: string,
    type: ProviderType,
    selectedValue: string,
    onValueChange: (value: string) => void
  ) => {
    const engineOptions = getEngineOptions(type);
    const selectedProvider = grouped[type].find(
      ({ provider }) => provider.name === selectedValue
    )?.provider;

    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Engine</Label>
            <Select value={selectedValue} onValueChange={onValueChange}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder={`Select ${title.toLowerCase()} engine`} />
              </SelectTrigger>
              <SelectContent>
                {engineOptions.map((engine) => (
                  <SelectItem key={engine.value} value={engine.value}>
                    <span className="flex items-center gap-2">
                      {engine.label}
                      {engine.isConfigured && (
                        <Check className="h-3 w-3 text-green-500" />
                      )}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Show provider-specific configuration if needed */}
          {selectedProvider?.shared_credentials_note && (
            <p className="text-xs text-muted-foreground">
              {selectedProvider.shared_credentials_note}
            </p>
          )}
        </CardContent>
      </Card>
    );
  };

  if (isLoading || providersLoading) {
    return (
      <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
        <Skeleton className="h-9 w-32" />
        <Skeleton className="h-10 w-full max-w-md" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="rounded-lg border bg-card shadow-sm p-6 space-y-4">
            <div className="space-y-2">
              <Skeleton className="h-6 w-40" />
              <Skeleton className="h-4 w-64" />
            </div>
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">Failed to load settings</h2>
          <p className="text-muted-foreground">Something went wrong while fetching your settings.</p>
        </div>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Configure your API keys, engine preferences, and appearance
        </p>
      </div>

      <Tabs defaultValue="ai-engines" className="w-full">
        <TabsList className="grid w-full max-w-lg grid-cols-4">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="ai-engines">AI Engines</TabsTrigger>
          <TabsTrigger value="audio">Audio</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>
                Customize the look and feel of the application
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label>Theme</Label>
                <div className="flex gap-2">
                  {mounted && (
                    <>
                      <Button
                        variant={theme === "light" ? "default" : "outline"}
                        size="sm"
                        onClick={() => setTheme("light")}
                        className="flex items-center gap-2"
                      >
                        <Sun className="h-4 w-4" />
                        Light
                      </Button>
                      <Button
                        variant={theme === "dark" ? "default" : "outline"}
                        size="sm"
                        onClick={() => setTheme("dark")}
                        className="flex items-center gap-2"
                      >
                        <Moon className="h-4 w-4" />
                        Dark
                      </Button>
                      <Button
                        variant={theme === "system" ? "default" : "outline"}
                        size="sm"
                        onClick={() => setTheme("system")}
                        className="flex items-center gap-2"
                      >
                        <Monitor className="h-4 w-4" />
                        System
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai-engines" className="space-y-6 mt-6">
          {/* Provider Credentials Section */}
          <Card>
            <CardHeader>
              <CardTitle>Provider Credentials</CardTitle>
              <CardDescription>
                Configure API keys and endpoints for AI providers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* LLM Providers */}
              {grouped.llm.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    Language Models
                  </h4>
                  <div className="grid gap-3">
                    {grouped.llm.map(({ provider, credential }) => (
                      <ProviderCard
                        key={provider.name}
                        provider={provider}
                        credential={credential}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Image Providers */}
              {grouped.image.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    Image Generation
                  </h4>
                  <div className="grid gap-3">
                    {grouped.image.map(({ provider, credential }) => (
                      <ProviderCard
                        key={provider.name}
                        provider={provider}
                        credential={credential}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Video Providers */}
              {grouped.video.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    Video Generation
                  </h4>
                  <div className="grid gap-3">
                    {grouped.video.map(({ provider, credential }) => (
                      <ProviderCard
                        key={provider.name}
                        provider={provider}
                        credential={credential}
                      />
                    ))}
                  </div>
                </div>
              )}

              {grouped.scraper.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    Research & Scraping
                  </h4>
                  <div className="grid gap-3">
                    {grouped.scraper.map(({ provider, credential }) => (
                      <ProviderCard
                        key={provider.name}
                        provider={provider}
                        credential={credential}
                      />
                    ))}
                  </div>
                </div>
              )}

              {grouped.tts.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    Text-to-Speech
                  </h4>
                  <div className="grid gap-3">
                    {grouped.tts.map(({ provider, credential }) => (
                      <ProviderCard
                        key={provider.name}
                        provider={provider}
                        credential={credential}
                      />
                    ))}
                  </div>
                </div>
              )}

              {grouped.stt.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    Speech-to-Text
                  </h4>
                  <div className="grid gap-3">
                    {grouped.stt.map(({ provider, credential }) => (
                      <ProviderCard
                        key={provider.name}
                        provider={provider}
                        credential={credential}
                      />
                    ))}
                  </div>
                </div>
              )}

              {grouped.bgm.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    Background Music
                  </h4>
                  <div className="grid gap-3">
                    {grouped.bgm.map(({ provider, credential }) => (
                      <ProviderCard
                        key={provider.name}
                        provider={provider}
                        credential={credential}
                      />
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="border-t pt-6" />

          {/* Engine Preferences Section */}
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Engine Preferences</h3>
            <p className="text-sm text-muted-foreground">
              Select your default engines for different generation tasks
            </p>
          </div>

          {renderEngineCard(
            "LLM Engine",
            "Select your preferred language model engine for copy generation",
            "llm",
            formData.default_llm_engine,
            (value) => setFormData({ ...formData, default_llm_engine: value })
          )}

          {renderEngineCard(
            "Image Engine",
            "Select your preferred image generation engine",
            "image",
            formData.default_image_engine,
            (value) => setFormData({ ...formData, default_image_engine: value })
          )}

          {renderEngineCard(
            "Video Engine",
            "Select your preferred video generation engine",
            "video",
            formData.default_video_engine,
            (value) => setFormData({ ...formData, default_video_engine: value })
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Video className="h-5 w-5" />
                UGC Video Generation
              </CardTitle>
              <CardDescription>
                Generate AI avatar talking-head videos for your ads
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.ugc_enabled}
                    onChange={(e) => setFormData({ ...formData, ugc_enabled: e.target.checked })}
                    className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-700"
                  />
                  <span className="text-sm font-medium">Enable UGC Video Generation</span>
                </label>
                {formData.ugc_enabled && <Badge variant="secondary">Enabled</Badge>}
              </div>

              {formData.ugc_enabled && (
                <>
                  <div className="space-y-2">
                    <Label>UGC Engine</Label>
                    <Select
                      value={formData.default_ugc_engine}
                      onValueChange={(value) =>
                        setFormData({ ...formData, default_ugc_engine: value })
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select UGC engine" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">Disabled</SelectItem>
                        {grouped.ugc.map(({ provider, credential }) => (
                          <SelectItem key={provider.name} value={provider.name}>
                            <span className="flex items-center gap-2">
                              {provider.display_name}
                              {credential?.is_configured && (
                                <Check className="h-3 w-3 text-green-500" />
                              )}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Show UGC provider credentials card for selected engine */}
                  {formData.default_ugc_engine && formData.default_ugc_engine !== "" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <User className="h-4 w-4" />
                          Avatar
                        </Label>
                        {avatarsLoading ? (
                          <Skeleton className="h-10 w-full" />
                        ) : (
                          <Select
                            value={formData.ugc_avatar_id}
                            onValueChange={(value) =>
                              setFormData({ ...formData, ugc_avatar_id: value })
                            }
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Default Avatar" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="">Default Avatar</SelectItem>
                              {avatarsData?.avatars.map((avatar) => (
                                <SelectItem key={avatar.avatar_id} value={avatar.avatar_id}>
                                  {avatar.name} {avatar.gender ? `(${avatar.gender})` : ""}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          <Mic className="h-4 w-4" />
                          Voice
                        </Label>
                        {voicesLoading ? (
                          <Skeleton className="h-10 w-full" />
                        ) : (
                          <Select
                            value={formData.ugc_voice_id}
                            onValueChange={(value) =>
                              setFormData({ ...formData, ugc_voice_id: value })
                            }
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Default Voice" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="">Default Voice</SelectItem>
                              {voicesData?.voices.map((voice) => (
                                <SelectItem key={voice.voice_id} value={voice.voice_id}>
                                  {voice.name} ({voice.language})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {!formData.ugc_enabled && (
                <p className="text-sm text-muted-foreground">
                  Enable UGC video generation to create AI avatar talking-head videos.
                  These videos feature an AI avatar speaking your ad copy, perfect for
                  TikTok, Instagram Reels, and other social media platforms.
                </p>
              )}
            </CardContent>
          </Card>


        </TabsContent>

        <TabsContent value="audio" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>TTS Settings</CardTitle>
              <CardDescription>
                Choose how narration is generated for audio-enabled creatives.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.tts_enabled}
                    onChange={(e) =>
                      setFormData({ ...formData, tts_enabled: e.target.checked })
                    }
                    className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-700"
                  />
                  <span className="text-sm font-medium">Enable TTS narration</span>
                </label>
                {formData.tts_enabled ? <Badge variant="secondary">Enabled</Badge> : null}
              </div>

              <div className="space-y-2">
                <Label>TTS Engine</Label>
                <Select
                  value={formData.default_tts_engine}
                  onValueChange={(value) =>
                    setFormData({
                      ...formData,
                      default_tts_engine: value,
                      tts_voice_id: "",
                    })
                  }
                  disabled={!formData.tts_enabled}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select TTS engine" />
                  </SelectTrigger>
                  <SelectContent>
                    {grouped.tts.length > 0
                      ? grouped.tts.map(({ provider, credential }) => (
                          <SelectItem key={provider.name} value={provider.name}>
                            <span className="flex items-center gap-2">
                              {provider.display_name}
                              {credential?.is_configured && (
                                <Check className="h-3 w-3 text-green-500" />
                              )}
                            </span>
                          </SelectItem>
                        ))
                      : [
                          <SelectItem key="openai-tts" value="openai-tts">OpenAI TTS</SelectItem>,
                          <SelectItem key="edge-tts" value="edge-tts">Edge TTS (Free)</SelectItem>,
                          <SelectItem key="elevenlabs" value="elevenlabs">ElevenLabs</SelectItem>,
                        ]}
                  </SelectContent>
                </Select>
              </div>

              {formData.tts_enabled && formData.default_tts_engine ? (
                <div className="space-y-2">
                  <Label>Voice</Label>
                  {ttsVoicesLoading ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Select
                      value={formData.tts_voice_id}
                      onValueChange={(value) =>
                        setFormData({ ...formData, tts_voice_id: value })
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select voice" />
                      </SelectTrigger>
                      <SelectContent>
                        {ttsVoicesData?.voices.map((voice) => (
                          <SelectItem key={voice.voice_id} value={voice.voice_id}>
                            {voice.name} ({voice.language})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>BGM Settings</CardTitle>
              <CardDescription>
                Control background music defaults for generated video content.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.bgm_enabled}
                    onChange={(e) =>
                      setFormData({ ...formData, bgm_enabled: e.target.checked })
                    }
                    className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-700"
                  />
                  <span className="text-sm font-medium">Enable background music</span>
                </label>
                {formData.bgm_enabled ? <Badge variant="secondary">Enabled</Badge> : null}
              </div>

              <div className="space-y-2">
                <Label>BGM Engine</Label>
                <Select
                  value={formData.default_bgm_engine}
                  onValueChange={(value) =>
                    setFormData({ ...formData, default_bgm_engine: value })
                  }
                  disabled={!formData.bgm_enabled}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select BGM engine" />
                  </SelectTrigger>
                  <SelectContent>
                    {grouped.bgm.length > 0
                      ? grouped.bgm.map(({ provider, credential }) => (
                          <SelectItem key={provider.name} value={provider.name}>
                            <span className="flex items-center gap-2">
                              {provider.display_name}
                              {credential?.is_configured && (
                                <Check className="h-3 w-3 text-green-500" />
                              )}
                            </span>
                          </SelectItem>
                        ))
                      : [
                          <SelectItem key="static-bgm" value="static-bgm">Static BGM</SelectItem>,
                        ]}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>BGM Style</Label>
                <Select
                  value={formData.bgm_style}
                  onValueChange={(value) =>
                    setFormData({ ...formData, bgm_style: value })
                  }
                  disabled={!formData.bgm_enabled}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select background music style" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="upbeat">Upbeat</SelectItem>
                    <SelectItem value="corporate">Corporate</SelectItem>
                    <SelectItem value="emotional">Emotional</SelectItem>
                    <SelectItem value="minimal">Minimal</SelectItem>
                    <SelectItem value="energetic">Energetic</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>STT Settings</CardTitle>
              <CardDescription>
                Select the speech-to-text engine for transcription tasks.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>STT Engine</Label>
                <Select
                  value={formData.default_stt_engine}
                  onValueChange={(value) =>
                    setFormData({ ...formData, default_stt_engine: value })
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select STT engine" />
                  </SelectTrigger>
                  <SelectContent>
                    {grouped.stt.length > 0
                      ? grouped.stt.map(({ provider, credential }) => (
                          <SelectItem key={provider.name} value={provider.name}>
                            <span className="flex items-center gap-2">
                              {provider.display_name}
                              {credential?.is_configured && (
                                <Check className="h-3 w-3 text-green-500" />
                              )}
                            </span>
                          </SelectItem>
                        ))
                      : [
                          <SelectItem key="openai-stt" value="openai-stt">OpenAI Whisper</SelectItem>,
                        ]}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="billing" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Billing & Subscription
              </CardTitle>
              <CardDescription>
                Manage your subscription, view usage, and upgrade your plan
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild>
                <a href="/settings/billing/">Manage Billing</a>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex gap-4 pt-4 border-t">
        <Button onClick={handleSave} disabled={updateSettings.isPending}>
          {updateSettings.isPending ? "Saving..." : "Save Settings"}
        </Button>
        <Button
          variant="outline"
          onClick={handleTestConnection}
          disabled={testConnection.isPending}
        >
          {testConnection.isPending ? "Testing..." : "Test Connection"}
        </Button>
      </div>
    </div>
  );
}
