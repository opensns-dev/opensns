"use client";

import { useState, useEffect } from "react";
import { Video, User, Mic } from "lucide-react";
import { useSettings, useUpdateSettings } from "@/hooks/use-settings";
import { useUGCEngines, useAvatars, useVoices } from "@/hooks/use-ugc";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

const UGC_ENGINES = [
  { value: "heygen", label: "HeyGen" },
  { value: "d-id", label: "D-ID" },
  { value: "sadtalker", label: "SadTalker (Self-hosted)" },
];

export function UGCSettingsCard() {
  const { data: settings, isLoading: settingsLoading } = useSettings();
  const { data: enginesData, isLoading: enginesLoading } = useUGCEngines();
  const updateSettings = useUpdateSettings();

  const [ugcEnabled, setUgcEnabled] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState("heygen");
  const [heygenKey, setHeygenKey] = useState("");
  const [didKey, setDidKey] = useState("");
  const [showHeygenKey, setShowHeygenKey] = useState(false);
  const [showDidKey, setShowDidKey] = useState(false);
  const [avatarId, setAvatarId] = useState("");
  const [voiceId, setVoiceId] = useState("");

  const { data: avatarsData, isLoading: avatarsLoading } = useAvatars(selectedEngine);
  const { data: voicesData, isLoading: voicesLoading } = useVoices(selectedEngine);

  useEffect(() => {
    if (settings) {
      setUgcEnabled(settings.ugc_enabled);
      setSelectedEngine(settings.default_ugc_engine || "heygen");
      setAvatarId(settings.ugc_avatar_id || "");
      setVoiceId(settings.ugc_voice_id || "");
    }
  }, [settings]);

  const handleSaveUGC = async () => {
    try {
      const dataToSend: Record<string, string | boolean> = {
        ugc_enabled: ugcEnabled,
        default_ugc_engine: selectedEngine,
        ugc_avatar_id: avatarId,
        ugc_voice_id: voiceId,
      };

      if (heygenKey) {
        dataToSend.heygen_api_key = heygenKey;
      }
      if (didKey) {
        dataToSend.did_api_key = didKey;
      }

      await updateSettings.mutateAsync(dataToSend);
      setHeygenKey("");
      setDidKey("");
      toast.success("UGC settings saved");
    } catch {
      toast.error("Failed to save UGC settings");
    }
  };

  if (settingsLoading || enginesLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
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
              checked={ugcEnabled}
              onChange={(e) => setUgcEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-700"
            />
            <span className="text-sm font-medium">Enable UGC Video Generation</span>
          </label>
          {ugcEnabled && <Badge variant="secondary">Enabled</Badge>}
        </div>

        {ugcEnabled && (
          <>
            <div className="space-y-2">
              <Label>UGC Engine</Label>
              <Select value={selectedEngine} onValueChange={setSelectedEngine}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select engine" />
                </SelectTrigger>
                <SelectContent>
                  {UGC_ENGINES.map((engine) => {
                    const engineInfo = enginesData?.engines.find(
                      (e) => e.engine === engine.value
                    );
                    return (
                      <SelectItem key={engine.value} value={engine.value}>
                        {engine.label}
                        {engineInfo?.has_api_key ? " ✓" : ""}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {selectedEngine === "heygen" && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="heygen_key">HeyGen API Key</Label>
                  {settings?.has_heygen_key && (
                    <Badge variant="secondary">Configured</Badge>
                  )}
                </div>
                <div className="flex gap-2">
                  <Input
                    id="heygen_key"
                    type={showHeygenKey ? "text" : "password"}
                    placeholder={
                      settings?.has_heygen_key ? "••••••••••••••••" : "Enter HeyGen API key"
                    }
                    value={heygenKey}
                    onChange={(e) => setHeygenKey(e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowHeygenKey(!showHeygenKey)}
                  >
                    {showHeygenKey ? "Hide" : "Show"}
                  </Button>
                </div>
              </div>
            )}

            {selectedEngine === "d-id" && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="did_key">D-ID API Key</Label>
                  {settings?.has_did_key && (
                    <Badge variant="secondary">Configured</Badge>
                  )}
                </div>
                <div className="flex gap-2">
                  <Input
                    id="did_key"
                    type={showDidKey ? "text" : "password"}
                    placeholder={
                      settings?.has_did_key ? "••••••••••••••••" : "Enter D-ID API key"
                    }
                    value={didKey}
                    onChange={(e) => setDidKey(e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowDidKey(!showDidKey)}
                  >
                    {showDidKey ? "Hide" : "Show"}
                  </Button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Avatar
                </Label>
                {avatarsLoading ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <Select value={avatarId} onValueChange={setAvatarId}>
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
                  <Select value={voiceId} onValueChange={setVoiceId}>
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

            <Button onClick={handleSaveUGC} disabled={updateSettings.isPending}>
              {updateSettings.isPending ? "Saving..." : "Save UGC Settings"}
            </Button>
          </>
        )}

        {!ugcEnabled && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Enable UGC video generation to create AI avatar talking-head videos. 
            These videos feature an AI avatar speaking your ad copy, perfect for 
            TikTok, Instagram Reels, and other social media platforms.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
