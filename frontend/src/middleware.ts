// Server-side auth guard (active only in standalone/Docker mode, not static export)

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_ROUTES = [
  "/",
  "/login",
  "/register",
  "/forgot-password",
  "/onboarding",
  "/auth/verify",
  "/auth/google/callback",
  "/pricing",
  "/terms",
  "/privacy",
  "/refund",
  "/contact",
];

function normalizePath(pathname: string): string {
  // Strip trailing slash except for root "/"
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;

  // Always allow /docs/ paths (static docs site)
  if (pathname.startsWith("/docs/")) {
    return NextResponse.next();
  }

  const normalizedPath = normalizePath(pathname);

  // Check if this is a public route
  const isPublicRoute = PUBLIC_ROUTES.includes(normalizedPath);

  if (isPublicRoute) {
    return NextResponse.next();
  }

  // Check for access_token cookie
  const accessToken = request.cookies.get("access_token")?.value;

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|docs/|api/).*)"],
};
