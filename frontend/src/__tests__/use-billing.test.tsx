/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { api } from '@/lib/api'
import {
  useBillingOverview,
  usePlans,
  useCreditPacks,
  useLSConfig,
  useUsageAnalytics,
  useLSCheckout,
} from '@/hooks/use-billing'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  Wrapper.displayName = 'TestQueryWrapper'
  return Wrapper
}

describe('useBillingOverview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches billing overview successfully', async () => {
    const mockOverview = {
      subscription: {
        tier: 'FREE',
        status: 'ACTIVE',
        current_period_start: '2024-01-01',
        current_period_end: '2024-02-01',
        cancel_at_period_end: false,
        limits: { campaigns: 5 },
      },
      usage: {
        period_start: '2024-01-01',
        credits_used: 10,
        credits_limit: 100,
        bonus_credits: 0,
      },
      credit_costs: { image: 1, video: 12 },
      usage_percentage: 10,
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockOverview })

    const { result } = renderHook(() => useBillingOverview(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockOverview)
    expect(api.get).toHaveBeenCalledWith('/billing/overview')
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useBillingOverview(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('usePlans', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches plans successfully', async () => {
    const mockPlans = {
      FREE: { name: 'Free', price_monthly: 0, price_display: '$0', credits_per_month: 50, variant_id: null, team_members: 1, api_access: false, white_label: false, competitor_research: false, priority_queue: false },
      BASIC: { name: 'Basic', price_monthly: 19, price_display: '$19', credits_per_month: 200, variant_id: 'variant_basic', team_members: 3, api_access: true, white_label: false, competitor_research: true, priority_queue: false },
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockPlans })

    const { result } = renderHook(() => usePlans(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockPlans)
    expect(api.get).toHaveBeenCalledWith('/billing/plans')
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => usePlans(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useCreditPacks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches credit packs successfully', async () => {
    const mockCreditPacks = {
      small: { id: 'small', credits: 100, price_cents: 999, price_display: '$9.99', variant_id: 'variant_small' },
      medium: { id: 'medium', credits: 500, price_cents: 3999, price_display: '$39.99', variant_id: 'variant_medium' },
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockCreditPacks })

    const { result } = renderHook(() => useCreditPacks(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockCreditPacks)
    expect(api.get).toHaveBeenCalledWith('/billing/credit-packs')
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useCreditPacks(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useLSConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches LemonSqueezy config successfully', async () => {
    const mockConfig = {
      store_id: 'store_123',
      customer_email: 'test@example.com',
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockConfig })

    const { result } = renderHook(() => useLSConfig(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockConfig)
    expect(api.get).toHaveBeenCalledWith('/billing/ls-config')
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useLSConfig(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useUsageAnalytics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches usage analytics successfully', async () => {
    const mockAnalytics = {
      period_days: 30,
      total_credits: 50,
      by_type: { image: 30, video: 20 },
      daily: [{ date: '2024-01-01', credits: 5, image: 3, video: 2 }],
      lifetime: { total_credits: 100, total_images: 60, total_videos: 40 },
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockAnalytics })

    const { result } = renderHook(() => useUsageAnalytics(30), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockAnalytics)
    expect(api.get).toHaveBeenCalledWith('/billing/analytics?days=30')
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useUsageAnalytics(30), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useLSCheckout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('LemonSqueezy', undefined)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('throws error when LemonSqueezy is not loaded', async () => {
    ;(api.post as Mock).mockResolvedValueOnce({ data: { url: 'https://checkout.test' } })

    const { result } = renderHook(() => useLSCheckout(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      variantId: 'variant_123',
      userId: 1,
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('LemonSqueezy not loaded')
  })

  it('opens LemonSqueezy checkout successfully', async () => {
    const mockOpen = vi.fn()
    ;(api.post as Mock).mockResolvedValueOnce({ data: { url: 'https://checkout.test' } })
    vi.stubGlobal('LemonSqueezy', {
      Url: {
        Open: mockOpen,
      },
    })

    const { result } = renderHook(() => useLSCheckout(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      variantId: 'variant_123',
      userId: 1,
      checkoutType: 'subscription',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.post).toHaveBeenCalledWith('/billing/create-checkout', {
      variant_id: 'variant_123',
      checkout_type: 'subscription',
      custom_data: {
        user_id: 1,
      },
    })
    expect(mockOpen).toHaveBeenCalledWith('https://checkout.test')
  })
})
