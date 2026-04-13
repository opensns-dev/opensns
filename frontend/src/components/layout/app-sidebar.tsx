"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Megaphone,
  Images,
  ScrollText,
  Settings,
  LogOut,
  Repeat,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useAuth } from "@/contexts/auth-context";

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
    title: "Settings",
    url: "/settings/",
    icon: Settings,
  },
];

function isActiveRoute(pathname: string, url: string): boolean {
  const normalized = pathname.endsWith("/") ? pathname : pathname + "/";
  if (url === "/dashboard/") return normalized === "/dashboard/";
  return normalized.startsWith(url);
}

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

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

      <div className="mt-auto border-t border-zinc-200 dark:border-zinc-800 p-4">
        {user && (
          <p className="text-xs text-muted-foreground truncate mb-3 px-2">
            {user.email}
          </p>
        )}
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
