"use client";

import { useState, useEffect } from "react";
import {
  Plus,
  Trash2,
  ArrowLeft,
  Mic,
  User as UserIcon,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import {
  useCustomVoices,
  useCreateVoice,
  useDeleteVoice,
  useCustomAvatars,
  useCreateAvatar,
  useDeleteAvatar,
} from "@/hooks/use-custom-media";
import type {
  CustomVoice,
  CustomVoiceCreate,
  CustomAvatar,
  CustomAvatarCreate,
  VoiceCloneStatus,
} from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
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

const STATUS_STYLES: Record<VoiceCloneStatus, string> = {
  READY: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  PROCESSING:
    "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  PENDING: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  FAILED: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
};

function StatusBadge({ status }: { status: VoiceCloneStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

const EMPTY_VOICE: CustomVoiceCreate = {
  name: "",
  language: "en",
  sample_url: "",
  provider: "heygen",
};

const EMPTY_AVATAR: CustomAvatarCreate = {
  name: "",
  provider: "heygen",
  photo_url: "",
};

type Section = "voices" | "avatars";

export default function CustomMediaPage() {
  const [activeSection, setActiveSection] = useState<Section>("voices");

  const { data: voices, isLoading: voicesLoading, refetch: refetchVoices } = useCustomVoices();
  const createVoice = useCreateVoice();
  const deleteVoice = useDeleteVoice();

  const { data: avatars, isLoading: avatarsLoading, refetch: refetchAvatars } = useCustomAvatars();
  const createAvatar = useCreateAvatar();
  const deleteAvatar = useDeleteAvatar();

  const [voiceDialogOpen, setVoiceDialogOpen] = useState(false);
  const [avatarDialogOpen, setAvatarDialogOpen] = useState(false);
  const [voiceForm, setVoiceForm] = useState<CustomVoiceCreate>(EMPTY_VOICE);
  const [avatarForm, setAvatarForm] = useState<CustomAvatarCreate>(EMPTY_AVATAR);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    type: "voice" | "avatar";
    id: number;
  } | null>(null);

  const hasPendingVoices = voices?.some(
    (v) => v.status === "PENDING" || v.status === "PROCESSING",
  );
  const hasPendingAvatars = avatars?.some(
    (a) => a.status === "PENDING" || a.status === "PROCESSING",
  );

  useEffect(() => {
    if (!hasPendingVoices) return;
    const interval = setInterval(() => refetchVoices(), 10_000);
    return () => clearInterval(interval);
  }, [hasPendingVoices, refetchVoices]);

  useEffect(() => {
    if (!hasPendingAvatars) return;
    const interval = setInterval(() => refetchAvatars(), 10_000);
    return () => clearInterval(interval);
  }, [hasPendingAvatars, refetchAvatars]);

  const handleCreateVoice = async () => {
    if (!voiceForm.name.trim()) {
      toast.error("Name is required");
      return;
    }
    if (!voiceForm.sample_url.trim()) {
      toast.error("Sample URL is required");
      return;
    }
    try {
      await createVoice.mutateAsync(voiceForm);
      toast.success("Voice clone request submitted");
      setVoiceDialogOpen(false);
      setVoiceForm(EMPTY_VOICE);
    } catch {
      toast.error("Failed to create voice");
    }
  };

  const handleCreateAvatar = async () => {
    if (!avatarForm.name.trim()) {
      toast.error("Name is required");
      return;
    }
    if (!avatarForm.photo_url.trim()) {
      toast.error("Photo URL is required");
      return;
    }
    try {
      await createAvatar.mutateAsync(avatarForm);
      toast.success("Avatar creation request submitted");
      setAvatarDialogOpen(false);
      setAvatarForm(EMPTY_AVATAR);
    } catch {
      toast.error("Failed to create avatar");
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    try {
      if (deleteConfirm.type === "voice") {
        await deleteVoice.mutateAsync(deleteConfirm.id);
        toast.success("Voice deleted");
      } else {
        await deleteAvatar.mutateAsync(deleteConfirm.id);
        toast.success("Avatar deleted");
      }
      setDeleteConfirm(null);
    } catch {
      toast.error("Failed to delete");
    }
  };

  const isLoading = voicesLoading || avatarsLoading;

  if (isLoading) {
    return (
      <div className="container max-w-3xl py-8 space-y-6">
        <Skeleton className="h-9 w-48" />
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full rounded-lg" />
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
            <h1 className="text-2xl font-bold">Custom Media</h1>
          </div>
          <p className="text-zinc-600 dark:text-zinc-400 ml-10">
            Manage custom voice clones and avatars for UGC videos
          </p>
        </div>
      </div>

      <div className="flex gap-1 border-b border-zinc-200 dark:border-zinc-800">
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeSection === "voices"
              ? "border-primary text-primary"
              : "border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
          }`}
          onClick={() => setActiveSection("voices")}
        >
          <Mic className="h-4 w-4 inline mr-1.5 -mt-0.5" />
          Voices ({voices?.length ?? 0})
        </button>
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeSection === "avatars"
              ? "border-primary text-primary"
              : "border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
          }`}
          onClick={() => setActiveSection("avatars")}
        >
          <UserIcon className="h-4 w-4 inline mr-1.5 -mt-0.5" />
          Avatars ({avatars?.length ?? 0})
        </button>
      </div>

      {activeSection === "voices" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button
              onClick={() => {
                setVoiceForm(EMPTY_VOICE);
                setVoiceDialogOpen(true);
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Clone Voice
            </Button>
          </div>

          {!voices?.length ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <Mic className="h-12 w-12 text-zinc-400 mb-4" />
                <h3 className="text-lg font-semibold mb-1">
                  No custom voices yet
                </h3>
                <p className="text-zinc-500 dark:text-zinc-400 mb-4">
                  Clone a voice from an audio sample to use in UGC videos.
                </p>
                <Button
                  onClick={() => {
                    setVoiceForm(EMPTY_VOICE);
                    setVoiceDialogOpen(true);
                  }}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Clone Voice
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {voices.map((voice) => (
                <VoiceCard
                  key={voice.id}
                  voice={voice}
                  onDelete={() =>
                    setDeleteConfirm({ type: "voice", id: voice.id })
                  }
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeSection === "avatars" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button
              onClick={() => {
                setAvatarForm(EMPTY_AVATAR);
                setAvatarDialogOpen(true);
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Avatar
            </Button>
          </div>

          {!avatars?.length ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <UserIcon className="h-12 w-12 text-zinc-400 mb-4" />
                <h3 className="text-lg font-semibold mb-1">
                  No custom avatars yet
                </h3>
                <p className="text-zinc-500 dark:text-zinc-400 mb-4">
                  Create an avatar from a photo to use in UGC videos.
                </p>
                <Button
                  onClick={() => {
                    setAvatarForm(EMPTY_AVATAR);
                    setAvatarDialogOpen(true);
                  }}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Avatar
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {avatars.map((avatar) => (
                <AvatarCard
                  key={avatar.id}
                  avatar={avatar}
                  onDelete={() =>
                    setDeleteConfirm({ type: "avatar", id: avatar.id })
                  }
                />
              ))}
            </div>
          )}
        </div>
      )}

      <Dialog open={voiceDialogOpen} onOpenChange={setVoiceDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Clone Voice</DialogTitle>
            <DialogDescription>
              Submit an audio sample to clone a voice for UGC videos.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="voice-name">Name *</Label>
              <Input
                id="voice-name"
                placeholder="e.g. Brand Spokesperson"
                value={voiceForm.name}
                onChange={(e) =>
                  setVoiceForm({ ...voiceForm, name: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="voice-language">Language</Label>
              <Select
                value={voiceForm.language}
                onValueChange={(val) =>
                  setVoiceForm({ ...voiceForm, language: val })
                }
              >
                <SelectTrigger id="voice-language">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="ko">Korean</SelectItem>
                  <SelectItem value="ja">Japanese</SelectItem>
                  <SelectItem value="zh">Chinese</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="voice-provider">Provider</Label>
              <Select
                value={voiceForm.provider}
                onValueChange={(val) =>
                  setVoiceForm({ ...voiceForm, provider: val })
                }
              >
                <SelectTrigger id="voice-provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="heygen">HeyGen</SelectItem>
                  <SelectItem value="did">D-ID</SelectItem>
                  <SelectItem value="elevenlabs">ElevenLabs</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="voice-sample">Sample Audio URL *</Label>
              <Input
                id="voice-sample"
                type="url"
                placeholder="https://example.com/voice-sample.mp3"
                value={voiceForm.sample_url}
                onChange={(e) =>
                  setVoiceForm({ ...voiceForm, sample_url: e.target.value })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setVoiceDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateVoice}
              disabled={createVoice.isPending}
            >
              {createVoice.isPending ? "Submitting..." : "Clone Voice"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={avatarDialogOpen} onOpenChange={setAvatarDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create Avatar</DialogTitle>
            <DialogDescription>
              Upload a reference photo to create a custom avatar.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="avatar-name">Name *</Label>
              <Input
                id="avatar-name"
                placeholder="e.g. Marketing Avatar"
                value={avatarForm.name}
                onChange={(e) =>
                  setAvatarForm({ ...avatarForm, name: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="avatar-provider">Provider</Label>
              <Select
                value={avatarForm.provider}
                onValueChange={(val) =>
                  setAvatarForm({ ...avatarForm, provider: val })
                }
              >
                <SelectTrigger id="avatar-provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="heygen">HeyGen</SelectItem>
                  <SelectItem value="did">D-ID</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="avatar-photo">Photo URL *</Label>
              <Input
                id="avatar-photo"
                type="url"
                placeholder="https://example.com/photo.jpg"
                value={avatarForm.photo_url}
                onChange={(e) =>
                  setAvatarForm({ ...avatarForm, photo_url: e.target.value })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAvatarDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateAvatar}
              disabled={createAvatar.isPending}
            >
              {createAvatar.isPending ? "Submitting..." : "Create Avatar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteConfirm !== null}
        onOpenChange={() => setDeleteConfirm(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Delete {deleteConfirm?.type === "voice" ? "Voice" : "Avatar"}
            </DialogTitle>
            <DialogDescription>
              This action cannot be undone. Are you sure?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteVoice.isPending || deleteAvatar.isPending}
            >
              {deleteVoice.isPending || deleteAvatar.isPending
                ? "Deleting..."
                : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function VoiceCard({
  voice,
  onDelete,
}: {
  voice: CustomVoice;
  onDelete: () => void;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base">{voice.name}</CardTitle>
            <Badge variant="secondary">{voice.language.toUpperCase()}</Badge>
            <Badge variant="outline">{voice.provider}</Badge>
            <StatusBadge status={voice.status} />
          </div>
          <Button variant="ghost" size="sm" onClick={onDelete}>
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center gap-4 text-sm text-zinc-500">
          <a
            href={voice.sample_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 hover:text-zinc-700 dark:hover:text-zinc-300"
          >
            <ExternalLink className="h-3 w-3" />
            Audio Sample
          </a>
          {voice.error && (
            <span className="text-red-500 text-xs">{voice.error}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function AvatarCard({
  avatar,
  onDelete,
}: {
  avatar: CustomAvatar;
  onDelete: () => void;
}) {
  const imageUrl = avatar.preview_url || avatar.photo_url;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={imageUrl}
              alt={avatar.name}
              className="h-10 w-10 rounded-full object-cover border border-zinc-200 dark:border-zinc-700"
            />
            <div className="flex items-center gap-2">
              <CardTitle className="text-base">{avatar.name}</CardTitle>
              <Badge variant="outline">{avatar.provider}</Badge>
              <StatusBadge status={avatar.status} />
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onDelete}>
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </CardHeader>
      {avatar.error && (
        <CardContent className="pt-0">
          <span className="text-red-500 text-xs">{avatar.error}</span>
        </CardContent>
      )}
    </Card>
  );
}
