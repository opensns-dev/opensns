/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

vi.mock('@/hooks/use-settings', () => ({
  useSettings: vi.fn(),
}))

vi.mock('@/hooks/use-campaigns', () => ({
  useCampaigns: vi.fn(),
}))

import { useSettings } from '@/hooks/use-settings'
import { useCampaigns } from '@/hooks/use-campaigns'
import { useOnboarding } from '@/hooks/use-onboarding'

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

describe('useOnboarding', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns isLoading: true when settings is loading', () => {
    ;(useSettings as Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as ReturnType<typeof useSettings>)

    ;(useCampaigns as Mock).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof useCampaigns>)

    const { result } = renderHook(() => useOnboarding(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
    expect(result.current.needsOnboarding).toBe(false)
    expect(result.current.step).toBe('api-keys')
  })

  it('returns isLoading: true when campaigns is loading', () => {
    ;(useSettings as Mock).mockReturnValue({
      data: { has_openai_key: true, has_fal_key: true },
      isLoading: false,
    } as ReturnType<typeof useSettings>)

    ;(useCampaigns as Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as ReturnType<typeof useCampaigns>)

    const { result } = renderHook(() => useOnboarding(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
    expect(result.current.needsOnboarding).toBe(false)
    expect(result.current.step).toBe('api-keys')
  })

  it('returns needsOnboarding: true, step: api-keys when no API keys set', () => {
    ;(useSettings as Mock).mockReturnValue({
      data: { has_openai_key: false, has_fal_key: false },
      isLoading: false,
    } as ReturnType<typeof useSettings>)

    ;(useCampaigns as Mock).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof useCampaigns>)

    const { result } = renderHook(() => useOnboarding(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.needsOnboarding).toBe(true)
    expect(result.current.step).toBe('api-keys')
  })

  it('returns needsOnboarding: true, step: first-campaign when API keys set but no campaigns', () => {
    ;(useSettings as Mock).mockReturnValue({
      data: { has_openai_key: true, has_fal_key: false },
      isLoading: false,
    } as ReturnType<typeof useSettings>)

    ;(useCampaigns as Mock).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof useCampaigns>)

    const { result } = renderHook(() => useOnboarding(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.needsOnboarding).toBe(true)
    expect(result.current.step).toBe('first-campaign')
  })

  it('returns needsOnboarding: false, step: complete when both API keys and campaigns exist', () => {
    ;(useSettings as Mock).mockReturnValue({
      data: { has_openai_key: true, has_fal_key: true },
      isLoading: false,
    } as ReturnType<typeof useSettings>)

    ;(useCampaigns as Mock).mockReturnValue({
      data: [{ id: 1, title: 'Campaign 1', status: 'PENDING', product_url: 'https://example.com', created_at: '2024-01-01', user_id: 1 }],
      isLoading: false,
    } as ReturnType<typeof useCampaigns>)

    const { result } = renderHook(() => useOnboarding(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.needsOnboarding).toBe(false)
    expect(result.current.step).toBe('complete')
  })
})
