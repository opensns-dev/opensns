"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, Shield } from "lucide-react";
import { toast } from "sonner";
import { useSettings, useUpdateSettings } from "@/hooks/use-settings";
import type { AILabelPosition } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AILabelBadge } from "@/components/ai-label-badge";

const POSITION_OPTIONS: { value: AILabelPosition; label: string }[] = [
  { value: "TOP_LEFT", label: "Top Left" },
  { value: "TOP_RIGHT", label: "Top Right" },
  { value: "BOTTOM_LEFT", label: "Bottom Left" },
  { value: "BOTTOM_RIGHT", label: "Bottom Right" },
  { value: "NONE", label: "None (metadata only)" },
];

export default function AILabelingSettingsPage() {
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateSettings();

  const [enabled, setEnabled] = useState(true);
  const [labelText, setLabelText] = useState("AI Generated");
  const [position, setPosition] = useState<AILabelPosition>("BOTTOM_RIGHT");

  useEffect(() => {
    if (settings) {
      setEnabled(settings.ai_disclosure_enabled);
      setLabelText(settings.ai_label_text);
      setPosition(settings.ai_label_position as AILabelPosition);
    }
  }, [settings]);

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync({
        ai_disclosure_enabled: enabled,
        ai_label_text: labelText,
        ai_label_position: position,
      });
      toast.success("AI labeling settings saved");
    } catch {
      toast.error("Failed to save settings");
    }
  };

  if (isLoading) {
    return (
      <div className="container max-w-3xl py-8 space-y-6">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    );
  }

  return (
    <div className="container max-w-3xl py-8 space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Button variant="ghost" size="sm" asChild className="h-8 w-8 p-0">
            <a href="/settings">
              <ArrowLeft className="h-4 w-4" />
            </a>
          </Button>
          <h1 className="text-2xl font-bold">AI Content Labeling</h1>
        </div>
        <p className="text-zinc-600 dark:text-zinc-400 ml-10">
          Configure AI disclosure labels for regulatory compliance (EU AI Act, IAB
          transparency)
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Disclosure Settings
          </CardTitle>
          <CardDescription>
            When enabled, generated assets will be labeled as AI-created content
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="ai-enabled" className="text-sm font-medium">
                Enable AI Disclosure Labels
              </Label>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                Automatically label generated content as AI-created
              </p>
            </div>
            <input
              id="ai-enabled"
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-300"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ai-label-text">Label Text</Label>
            <Input
              id="ai-label-text"
              placeholder="AI Generated"
              value={labelText}
              onChange={(e) => setLabelText(e.target.value)}
              disabled={!enabled}
            />
            <p className="text-xs text-zinc-500">
              Text displayed on the label badge (e.g. &quot;AI Generated&quot;,
              &quot;Made with AI&quot;)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="ai-label-position">Label Position</Label>
            <Select
              value={position}
              onValueChange={(val) => setPosition(val as AILabelPosition)}
              disabled={!enabled}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select position" />
              </SelectTrigger>
              <SelectContent>
                {POSITION_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Preview</Label>
            <div className="relative h-40 w-full rounded-lg border border-dashed border-zinc-300 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900">
              <div className="flex h-full items-center justify-center text-sm text-zinc-400">
                Asset Preview Area
              </div>
              <AILabelBadge
                disclosure={
                  enabled
                    ? { labeled: true, label_text: labelText, position }
                    : null
                }
              />
            </div>
          </div>

          <Button
            onClick={handleSave}
            disabled={updateSettings.isPending}
            className="w-full"
          >
            {updateSettings.isPending ? "Saving..." : "Save Settings"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
