"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  Bot,
  CheckCircle2,
  Images,
  LayoutDashboard,
  LogOut,
  Megaphone,
  Repeat,
  ScrollText,
  Settings,
  Sparkles,
  TriangleAlert,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadNotificationCount,
} from "@/hooks/use-notifications";
import { cn } from "@/lib/utils";
import type { Notification, NotificationType } from "@/types";

const items = [
  {
    title: "Dashboard",
    url: "/dashboard/",
    icon: LayoutDashboard,
  },
  {
    title: "Campaigns",
    url: "/campaigns/",
    icon: Megaphone,
  },
  {
    title: "Assets",
    url: "/assets/",
    icon: Images,
  },
  {
    title: "Logs",
    url: "/logs/",
    icon: ScrollText,
  },
  {
    title: "Repurpose",
    url: "/repurpose/",
    icon: Repeat,
  },
  {
    title: "Autopilot",
    url: "/autopilot/",
    icon: Bot,
  },
  {
    title: "Settings",
    url: "/settings/",
    icon: Settings,
  },
];

const NOTIFICATION_ICON_MAP: Record<NotificationType, typeof Sparkles> = {
  AUTOPILOT_COMPLETE: CheckCircle2,
  AUTOPILOT_FAILED: XCircle,
  AUTOPILOT_DISABLED: TriangleAlert,
  CREDITS_LOW: TriangleAlert,
  APPROVAL_NEEDED: Bell,
  PUBLISH_COMPLETE: CheckCircle2,
  PUBLISH_FAILED: XCircle,
};

function isActiveRoute(pathname: string, url: string): boolean {
  const normalized = pathname.endsWith("/") ? pathname : pathname + "/";
  if (url === "/dashboard/") return normalized === "/dashboard/";
  return normalized.startsWith(url);
}

function formatRelativeTime(value: string) {
  const timestamp = new Date(value).getTime();
  const diffMinutes = Math.round((Date.now() - timestamp) / (1000 * 60));

  if (diffMinutes < 1) {
    return "just now";
  }

  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.round(diffHours / 24);
  return `${diffDays}d ago`;
}

function NotificationIcon({ type }: { type: NotificationType }) {
  const Icon = NOTIFICATION_ICON_MAP[type] ?? Bell;

  return (
    <span className="flex size-9 items-center justify-center rounded-full bg-muted text-muted-foreground">
      <Icon className="size-4" />
    </span>
  );
}

function NotificationPanel({
  notifications,
  unreadCount,
}: {
  notifications: Notification[];
  unreadCount: number;
}) {
  const markOneRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const handleMarkAll = async () => {
    try {
      await markAllRead.mutateAsync();
      toast.success("Notifications marked as read");
    } catch {
      toast.error("Failed to mark notifications as read");
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (notification.is_read) {
      return;
    }

    try {
      await markOneRead.mutateAsync(notification.id);
    } catch {
      toast.error("Failed to update notification");
    }
  };

  return (
    <div className="flex h-full flex-col">
      <SheetHeader className="border-b">
        <div className="flex items-start justify-between gap-4 pr-8">
          <div className="space-y-1">
            <SheetTitle>Notifications</SheetTitle>
            <SheetDescription>
              Live autopilot and publishing updates, with unread counts synced in the sidebar.
            </SheetDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkAll}
            disabled={!unreadCount || markAllRead.isPending}
          >
            Mark all as read
          </Button>
        </div>
      </SheetHeader>

      <div className="flex-1 overflow-y-auto p-4">
        {notifications.length ? (
          <div className="space-y-3">
            {notifications.map((notification) => (
              <button
                key={notification.id}
                type="button"
                onClick={() => handleNotificationClick(notification)}
                className={cn(
                  "flex w-full items-start gap-3 rounded-xl border p-3 text-left transition-colors hover:bg-accent/40",
                  !notification.is_read && "border-primary/25 bg-primary/5"
                )}
              >
                <NotificationIcon type={notification.type} />
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <p className="font-medium leading-snug">{notification.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {notification.message}
                      </p>
                    </div>
                    {!notification.is_read ? (
                      <span className="mt-1 size-2 rounded-full bg-destructive" />
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline">{notification.type.replaceAll("_", " ")}</Badge>
                    <span>{formatRelativeTime(notification.created_at)}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex h-full items-center justify-center rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
            You&apos;re all caught up. New autopilot and publish events will appear here.
          </div>
        )}
      </div>
    </div>
  );
}

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { data: unreadCount = 0 } = useUnreadNotificationCount();
  const { data: notificationsData } = useNotifications();

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login/";
  };

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="flex items-center gap-2">
            <Image src="/logo-icon.svg" alt="OpenSNS" width={20} height={20} />
            OpenSNS
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActiveRoute(pathname, item.url)}
                  >
                    <Link href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <div className="mt-auto border-t border-zinc-200 p-4 dark:border-zinc-800">
        <SidebarMenu>
          <SidebarMenuItem>
            <Sheet>
              <SheetTrigger asChild>
                <SidebarMenuButton>
                  <Bell />
                  <span>Notifications</span>
                  {unreadCount > 0 ? (
                    <SidebarMenuBadge>{unreadCount > 99 ? "99+" : unreadCount}</SidebarMenuBadge>
                  ) : null}
                </SidebarMenuButton>
              </SheetTrigger>
              <SheetContent className="w-full sm:max-w-md" side="right">
                <NotificationPanel
                  notifications={notificationsData?.notifications ?? []}
                  unreadCount={unreadCount}
                />
              </SheetContent>
            </Sheet>
          </SidebarMenuItem>
        </SidebarMenu>

        {user ? (
          <p className="mb-3 truncate px-2 pt-3 text-xs text-muted-foreground">
            {user.email}
          </p>
        ) : null}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={handleLogout}>
              <LogOut />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </div>
    </Sidebar>
  );
}
