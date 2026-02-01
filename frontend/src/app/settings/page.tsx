"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor } from "lucide-react";
import { toast } from "sonner";
import { useSettings, useUpdateSettings, useTestConnection } from "@/hooks/use-settings";
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

const LLM_ENGINES = [
  { value: "openai", label: "OpenAI" },
  { value: "ollama", label: "Ollama (Local)" },
  { value: "mock", label: "Mock (Testing)" },
];

const IMAGE_ENGINES = [
  { value: "fal", label: "Fal.ai" },
  { value: "flux-pro", label: "Flux Pro" },
  { value: "comfyui", label: "ComfyUI (Local)" },
];

const VIDEO_ENGINES = [
  { value: "fal-video", label: "Fal.ai Video" },
  { value: "runway", label: "Runway" },
  { value: "comfyui-video", label: "ComfyUI Video (Local)" },
];

export default function SettingsPage() {
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateSettings();
  const testConnection = useTestConnection();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  const [formData, setFormData] = useState({
    openai_api_key: "",
    fal_api_key: "",
    firecrawl_api_key: "",
    default_llm_engine: "openai",
    default_image_engine: "fal",
    default_video_engine: "fal-video",
    ollama_url: "",
    comfyui_url: "",
  });

  const [showOpenAIKey, setShowOpenAIKey] = useState(false);
  const [showFalKey, setShowFalKey] = useState(false);
  const [showFirecrawlKey, setShowFirecrawlKey] = useState(false);

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
        ollama_url: settings.ollama_url || "",
        comfyui_url: settings.comfyui_url || "",
      }));
    }
  }, [settings]);

  const handleSave = async () => {
    try {
      const dataToSend: Record<string, string> = {
        default_llm_engine: formData.default_llm_engine,
        default_image_engine: formData.default_image_engine,
        default_video_engine: formData.default_video_engine,
        ollama_url: formData.ollama_url,
        comfyui_url: formData.comfyui_url,
      };

      if (formData.openai_api_key) {
        dataToSend.openai_api_key = formData.openai_api_key;
      }
      if (formData.fal_api_key) {
        dataToSend.fal_api_key = formData.fal_api_key;
      }
      if (formData.firecrawl_api_key) {
        dataToSend.firecrawl_api_key = formData.firecrawl_api_key;
      }

      await updateSettings.mutateAsync(dataToSend);
      setFormData((prev) => ({ ...prev, openai_api_key: "", fal_api_key: "", firecrawl_api_key: "" }));
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-zinc-500">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="container max-w-3xl py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Configure your API keys and engine preferences
        </p>
      </div>

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

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Your API keys are encrypted and stored securely
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="openai_key">OpenAI API Key</Label>
              {settings?.has_openai_key && (
                <Badge variant="secondary">Configured</Badge>
              )}
            </div>
            <div className="flex gap-2">
              <Input
                id="openai_key"
                type={showOpenAIKey ? "text" : "password"}
                placeholder={settings?.has_openai_key ? "••••••••••••••••" : "sk-..."}
                value={formData.openai_api_key}
                onChange={(e) =>
                  setFormData({ ...formData, openai_api_key: e.target.value })
                }
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowOpenAIKey(!showOpenAIKey)}
              >
                {showOpenAIKey ? "Hide" : "Show"}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="fal_key">Fal.ai API Key</Label>
              {settings?.has_fal_key && (
                <Badge variant="secondary">Configured</Badge>
              )}
            </div>
            <div className="flex gap-2">
              <Input
                id="fal_key"
                type={showFalKey ? "text" : "password"}
                placeholder={settings?.has_fal_key ? "••••••••••••••••" : "Enter your Fal.ai key"}
                value={formData.fal_api_key}
                onChange={(e) =>
                  setFormData({ ...formData, fal_api_key: e.target.value })
                }
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowFalKey(!showFalKey)}
              >
                {showFalKey ? "Hide" : "Show"}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="firecrawl_key">Firecrawl API Key (Optional)</Label>
              {settings?.has_firecrawl_key && (
                <Badge variant="secondary">Configured</Badge>
              )}
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Optional. Used as fallback if Playwright scraping fails.
            </p>
            <div className="flex gap-2">
              <Input
                id="firecrawl_key"
                type={showFirecrawlKey ? "text" : "password"}
                placeholder={settings?.has_firecrawl_key ? "••••••••••••••••" : "fc-..."}
                value={formData.firecrawl_api_key}
                onChange={(e) =>
                  setFormData({ ...formData, firecrawl_api_key: e.target.value })
                }
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowFirecrawlKey(!showFirecrawlKey)}
              >
                {showFirecrawlKey ? "Hide" : "Show"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Default Engines</CardTitle>
          <CardDescription>
            Select which AI engines to use for generation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="llm_engine">LLM Engine</Label>
            <select
              id="llm_engine"
              className="flex h-10 w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-800 dark:bg-zinc-950"
              value={formData.default_llm_engine}
              onChange={(e) =>
                setFormData({ ...formData, default_llm_engine: e.target.value })
              }
            >
              {LLM_ENGINES.map((engine) => (
                <option key={engine.value} value={engine.value}>
                  {engine.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="image_engine">Image Engine</Label>
            <select
              id="image_engine"
              className="flex h-10 w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-800 dark:bg-zinc-950"
              value={formData.default_image_engine}
              onChange={(e) =>
                setFormData({ ...formData, default_image_engine: e.target.value })
              }
            >
              {IMAGE_ENGINES.map((engine) => (
                <option key={engine.value} value={engine.value}>
                  {engine.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="video_engine">Video Engine</Label>
            <select
              id="video_engine"
              className="flex h-10 w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-800 dark:bg-zinc-950"
              value={formData.default_video_engine}
              onChange={(e) =>
                setFormData({ ...formData, default_video_engine: e.target.value })
              }
            >
              {VIDEO_ENGINES.map((engine) => (
                <option key={engine.value} value={engine.value}>
                  {engine.label}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Local Engines</CardTitle>
          <CardDescription>
            Configure URLs for self-hosted engines
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ollama_url">Ollama URL</Label>
            <Input
              id="ollama_url"
              type="url"
              placeholder="http://localhost:11434"
              value={formData.ollama_url}
              onChange={(e) =>
                setFormData({ ...formData, ollama_url: e.target.value })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="comfyui_url">ComfyUI URL</Label>
            <Input
              id="comfyui_url"
              type="url"
              placeholder="http://localhost:8188"
              value={formData.comfyui_url}
              onChange={(e) =>
                setFormData({ ...formData, comfyui_url: e.target.value })
              }
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-4">
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
