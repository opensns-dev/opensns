/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest'
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
import { useAssets } from '@/hooks/use-assets'

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

describe('useAssets', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches assets successfully for a campaign', async () => {
    const mockAssets = [
      { id: 1, campaign_id: 1, type: 'IMAGE', content: 'image1.jpg', asset_metadata: '{}', created_at: '2024-01-01' },
      { id: 2, campaign_id: 1, type: 'COPY', content: 'Ad copy text', asset_metadata: '{}', created_at: '2024-01-01' },
    ]

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockAssets })

    const { result } = renderHook(() => useAssets(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockAssets)
    expect(api.get).toHaveBeenCalledWith('/assets/campaign/1')
  })

  it('returns empty array for campaign with no assets', async () => {
    ;(api.get as Mock).mockResolvedValueOnce({ data: [] })

    const { result } = renderHook(() => useAssets(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual([])
    expect(api.get).toHaveBeenCalledWith('/assets/campaign/1')
  })

  it('does not fetch when campaignId is falsy', () => {
    const { result } = renderHook(() => useAssets(0), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(api.get).not.toHaveBeenCalled()
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useAssets(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})
