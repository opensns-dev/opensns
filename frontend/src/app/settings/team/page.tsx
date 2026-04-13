"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  Users,
  UserPlus,
  Trash2,
  Crown,
  Shield,
  Pencil,
  Eye,
  ArrowUpCircle,
} from "lucide-react";
import {
  useTeamMembers,
  useInviteMember,
  useUpdateMemberRole,
  useRemoveMember,
} from "@/hooks/use-team";
import { useBillingOverview } from "@/hooks/use-billing";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import type { TeamRole, TeamMember } from "@/types";

const ROLE_CONFIG: Record<TeamRole, { color: string; icon: typeof Crown; label: string }> = {
  OWNER: { color: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300", icon: Crown, label: "Owner" },
  ADMIN: { color: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300", icon: Shield, label: "Admin" },
  EDITOR: { color: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300", icon: Pencil, label: "Editor" },
  VIEWER: { color: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300", icon: Eye, label: "Viewer" },
};

const STATUS_CONFIG: Record<string, string> = {
  PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  ACCEPTED: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
};

function RoleBadge({ role }: { role: TeamRole }) {
  const config = ROLE_CONFIG[role];
  const Icon = config.icon;
  return (
    <Badge variant="outline" className={config.color}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
    </Badge>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_CONFIG[status] ?? "bg-zinc-100 text-zinc-700";
  return (
    <Badge variant="outline" className={color}>
      {status === "PENDING" ? "Pending" : "Accepted"}
    </Badge>
  );
}

function InviteDialog({
  open,
  onOpenChange,
  onInvite,
  isPending,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInvite: (email: string, role: TeamRole) => void;
  isPending: boolean;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<TeamRole>("EDITOR");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    onInvite(email.trim(), role);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Invite Team Member</DialogTitle>
            <DialogDescription>
              Send an invitation to collaborate on your campaigns.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="colleague@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select value={role} onValueChange={(v) => setRole(v as TeamRole)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ADMIN">Admin — can manage members</SelectItem>
                  <SelectItem value="EDITOR">Editor — can create & edit</SelectItem>
                  <SelectItem value="VIEWER">Viewer — read-only access</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !email.trim()}>
              {isPending ? "Sending..." : "Send Invite"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EditRoleDialog({
  member,
  open,
  onOpenChange,
  onUpdate,
  isPending,
}: {
  member: TeamMember;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate: (memberId: number, role: TeamRole) => void;
  isPending: boolean;
}) {
  const [role, setRole] = useState<TeamRole>(member.role);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Change Role</DialogTitle>
          <DialogDescription>
            Update the role for {member.email}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={role} onValueChange={(v) => setRole(v as TeamRole)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ADMIN">Admin</SelectItem>
                <SelectItem value="EDITOR">Editor</SelectItem>
                <SelectItem value="VIEWER">Viewer</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={() => onUpdate(member.id, role)}
            disabled={isPending || role === member.role}
          >
            {isPending ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function TeamPage() {
  const { data: members, isLoading, error } = useTeamMembers();
  const { data: billing } = useBillingOverview();
  const inviteMember = useInviteMember();
  const updateRole = useUpdateMemberRole();
  const removeMember = useRemoveMember();

  const [inviteOpen, setInviteOpen] = useState(false);
  const [editMember, setEditMember] = useState<TeamMember | null>(null);

  const maxMembers = billing?.subscription.limits.team_members as number | undefined;
  const currentTier = billing?.subscription.tier ?? "FREE";
  const memberCount = members?.filter((m) => m.invite_status !== "DECLINED").length ?? 0;
  const atLimit = maxMembers !== undefined && memberCount >= maxMembers;

  const handleInvite = (email: string, role: TeamRole) => {
    inviteMember.mutate(
      { email, role },
      {
        onSuccess: () => {
          toast.success("Invitation sent!");
          setInviteOpen(false);
        },
        onError: (err) => {
          const message =
            (err as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail ?? "Failed to send invitation.";
          toast.error(message);
        },
      }
    );
  };

  const handleUpdateRole = (memberId: number, role: TeamRole) => {
    updateRole.mutate(
      { memberId, data: { role } },
      {
        onSuccess: () => {
          toast.success("Role updated!");
          setEditMember(null);
        },
        onError: (err) => {
          const message =
            (err as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail ?? "Failed to update role.";
          toast.error(message);
        },
      }
    );
  };

  const handleRemove = (member: TeamMember) => {
    if (!confirm(`Remove ${member.email} from the team?`)) return;
    removeMember.mutate(member.id, {
      onSuccess: () => toast.success("Member removed."),
      onError: (err) => {
        const message =
          (err as { response?: { data?: { detail?: string } } }).response?.data
            ?.detail ?? "Failed to remove member.";
        toast.error(message);
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-zinc-500">Loading team members...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-red-500">Failed to load team members</div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Team Members</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Manage who has access to your campaigns
          </p>
        </div>
        <Button onClick={() => setInviteOpen(true)} disabled={atLimit}>
          <UserPlus className="h-4 w-4 mr-2" />
          Invite Member
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Team
            </CardTitle>
            <div className="text-sm text-zinc-500">
              {maxMembers !== undefined ? (
                <span className={atLimit ? "text-amber-600 font-medium" : ""}>
                  {memberCount}/{maxMembers} members ({currentTier} plan)
                </span>
              ) : (
                `${memberCount} members`
              )}
              {atLimit && (
                <Button variant="link" size="sm" className="ml-2 text-amber-600 p-0 h-auto" asChild>
                  <a href="/settings/billing">
                    <ArrowUpCircle className="h-3 w-3 mr-1" />
                    Upgrade
                  </a>
                </Button>
              )}
            </div>
          </div>
          <CardDescription>
            {atLimit
              ? "You've reached the team member limit. Upgrade to add more."
              : "Invite team members to collaborate on campaigns."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {members && members.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Invited</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => {
                  const isOwner = member.role === "OWNER";
                  return (
                    <TableRow key={member.id}>
                      <TableCell className="font-medium">
                        {member.email}
                      </TableCell>
                      <TableCell>
                        <RoleBadge role={member.role} />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={member.invite_status} />
                      </TableCell>
                      <TableCell className="text-zinc-500 text-sm">
                        {new Date(member.invited_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditMember(member)}
                          disabled={isOwner}
                          title={isOwner ? "Cannot change owner role" : "Edit role"}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemove(member)}
                          disabled={isOwner || removeMember.isPending}
                          title={isOwner ? "Cannot remove owner" : "Remove member"}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              <Users className="h-12 w-12 mx-auto mb-3 text-zinc-300" />
              <p className="font-medium">No team members yet</p>
              <p className="text-sm mt-1">
                Invite colleagues to collaborate on your campaigns.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <InviteDialog
        open={inviteOpen}
        onOpenChange={setInviteOpen}
        onInvite={handleInvite}
        isPending={inviteMember.isPending}
      />

      {editMember && (
        <EditRoleDialog
          member={editMember}
          open={!!editMember}
          onOpenChange={(open) => !open && setEditMember(null)}
          onUpdate={handleUpdateRole}
          isPending={updateRole.isPending}
        />
      )}
    </div>
  );
}
