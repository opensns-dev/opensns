# FRONTEND SOURCE

## OVERVIEW

Next.js 15 App Router with shadcn/ui components, React Query for data fetching, and Tailwind CSS v4.

## STRUCTURE

```
src/
├── app/              # App Router pages
│   ├── layout.tsx    # Root layout with providers
│   ├── page.tsx      # Landing page
│   ├── login/        # Auth pages
│   ├── register/
│   ├── dashboard/
│   ├── campaigns/    # Campaign list and [id] detail
│   ├── settings/     # User settings + billing
│   └── onboarding/
├── components/
│   ├── ui/           # shadcn/ui primitives
│   └── layout/       # App shell (sidebar, header)
├── hooks/            # React Query hooks (data layer)
├── contexts/         # AuthContext
├── providers/        # QueryProvider, ThemeProvider
├── lib/              # API client, utilities
└── types/            # TypeScript interfaces
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add page | `app/{route}/page.tsx` | App Router convention |
| Add hook | `hooks/use-{resource}.ts` | React Query pattern |
| Add component | `components/ui/` or `components/` | shadcn for primitives |
| Modify auth | `contexts/auth-context.tsx` | Login/logout/token |
| API client | `lib/api.ts` | Axios with interceptors |

## CONVENTIONS

### Page Pattern (App Router)
```tsx
// app/feature/page.tsx
export default function FeaturePage() {
  return <div>...</div>;
}

// Client components need directive:
"use client";
export default function ClientPage() { ... }
```

### Hook Pattern (React Query)
```tsx
// hooks/use-resource.ts
"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useResources() {
  return useQuery({
    queryKey: ["resources"],
    queryFn: async () => (await api.get("/resources")).data,
  });
}

export function useCreateResource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data) => (await api.post("/resources", data)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["resources"] }),
  });
}
```

### Auth Usage
```tsx
import { useAuth } from "@/contexts/auth-context";

function Component() {
  const { user, isAuthenticated, logout } = useAuth();
  ...
}
```

## KEY FILES

| File | Purpose |
|------|---------|
| `lib/api.ts` | Axios instance, token interceptors, `setToken/getToken/removeToken` |
| `contexts/auth-context.tsx` | Auth state, login/logout, Google OAuth |
| `providers/query-provider.tsx` | React Query setup |
| `types/index.ts` | Shared TypeScript interfaces |
| `app/layout.tsx` | Root providers chain |

## NOTIFICATIONS

Toast notifications use `sonner`. Already configured in `app/layout.tsx`:
```tsx
import { Toaster } from "sonner";
// In layout: <Toaster richColors position="top-right" />

// Usage in components:
import { toast } from "sonner";
toast.success("Campaign created!");
toast.error("Something went wrong");
```

## UI COMPONENTS

shadcn/ui primitives in `components/ui/`:
- Button, Card, Dialog, Input, Label, Sheet, Sidebar, Skeleton, Table, Tooltip, etc.
- All use Radix UI + Tailwind + class-variance-authority

## ANTI-PATTERNS

- **NEVER** store tokens outside `lib/api.ts` helpers
- **NEVER** fetch data in components directly (use hooks)
- **NEVER** use `any` types (define in `types/index.ts`)
- **NEVER** skip `"use client"` for interactive components

## TESTING

```bash
bun test            # Vitest unit tests
bun e2e             # Playwright E2E
```
Tests in `__tests__/` directory. Setup in `__tests__/setup.ts`.
