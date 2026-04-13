# HOOKS KNOWLEDGE BASE

**Location:** `frontend/src/hooks/`

## OVERVIEW

React Query (TanStack Query) hooks for OpenSNS frontend. All data fetching, mutations, and server state management lives here. Each domain has dedicated hooks following consistent patterns.

## STRUCTURE

```
hooks/
├── use-campaigns.ts    # Campaign CRUD + lifecycle
├── use-assets.ts       # Asset upload, list, delete
├── use-auth.ts         # Login, register, logout, token refresh
├── use-settings.ts     # User settings, API keys, preferences
├── use-billing.ts      # Subscription, credits, checkout
├── use-ugc.ts          # Avatar/voice listing for UGC videos
├── use-logs.ts         # Campaign real-time logs
├── use-repurpose.ts    # Content repurposing workflows
└── use-toast.ts        # Toast notification state
```

## WHERE TO LOOK

| Task | Hook | Notes |
|------|------|-------|
| Fetch campaigns | `useCampaigns()` | Lists all user campaigns |
| Create campaign | `useCreateCampaign()` | Invalidates campaigns list on success |
| Update settings | `useUpdateSettings()` | Encrypts API keys server-side |
| Upload asset | `useUploadAsset()` | POST to `/assets` with FormData |
| Get UGC avatars | `useUGCAvatars()` | Lists HeyGen/D-ID avatars |
| Stream logs | `useCampaignLogs(id)` | WebSocket fallback to polling |
| Check credits | `useBillingStatus()` | Real-time credit balance |

## CONVENTIONS

**React Query Patterns:**
- Query keys as arrays: `["resource"]` for lists, `["resource", id]` for single items
- Always use `queryClient.invalidateQueries()` on mutation success
- Stale time: 30s default, 0s for real-time data (logs, credits)
- Retry: 1 attempt for mutations, 3 for queries

**Hook Structure:**
```typescript
"use client";

export function useResource() {
  return useQuery({
    queryKey: ["resource"],
    queryFn: async () => {
      const response = await api.get<Resource[]>("/resource");
      return response.data;
    },
  });
}

export function useCreateResource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ResourceCreate) => {
      const response = await api.post<Resource>("/resource", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resource"] });
    },
  });
}
```

## KEY FILES

| File | Purpose |
|------|---------|
| `use-campaigns.ts` | Campaign lifecycle: create, update, delete, launch, approve |
| `use-assets.ts` | Asset management: upload, list, delete, get by campaign |
| `use-auth.ts` | JWT auth: login, register, logout, token refresh, password reset |
| `use-settings.ts` | User config: AI engines, API keys, brand settings |
| `use-billing.ts` | Paddle integration: subscription status, credit balance, checkout |
| `use-ugc.ts` | UGC engines: list avatars, list voices, generate UGC video |
| `use-logs.ts` | Campaign logs: WebSocket + polling hybrid for real-time updates |
| `use-repurpose.ts` | Content repurposing: submit, list, get results |
| `use-toast.ts` | Toast notifications: success, error, loading states |

## ANTI-PATTERNS

- **NEVER** call `api` directly in components. Always use hooks.
- **NEVER** forget `onSuccess` invalidation. Stale data causes bugs.
- **NEVER** use `useEffect` for data fetching. Use `useQuery`.
- **NEVER** store API keys in hook state. Send to backend immediately.
- **NEVER** skip error handling. All hooks must handle `error` state.
