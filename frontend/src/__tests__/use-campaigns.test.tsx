/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCampaigns, useCampaign, useCreateCampaign } from '@/hooks/use-campaigns'
import type { ReactNode } from 'react'

vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { api } from '@/lib/api'

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

describe('useCampaigns', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches campaigns successfully', async () => {
    const mockCampaigns = [
      { id: 1, title: 'Campaign 1', status: 'PENDING', product_url: 'https://example.com' },
      { id: 2, title: 'Campaign 2', status: 'COMPLETED', product_url: 'https://example.com/2' },
    ]
    
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockCampaigns })

    const { result } = renderHook(() => useCampaigns(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockCampaigns)
    expect(api.get).toHaveBeenCalledWith('/campaigns')
  })

  it('handles fetch error', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useCampaigns(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useCampaign', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches a single campaign', async () => {
    const mockCampaign = {
      id: 1,
      title: 'Test Campaign',
      status: 'GENERATING',
      product_url: 'https://example.com',
    }
    
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockCampaign })

    const { result } = renderHook(() => useCampaign(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockCampaign)
    expect(api.get).toHaveBeenCalledWith('/campaigns/1')
  })

  it('does not fetch when id is 0', () => {
    const { result } = renderHook(() => useCampaign(0), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('useCreateCampaign', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates a campaign successfully', async () => {
    const newCampaign = {
      id: 3,
      title: 'New Campaign',
      status: 'PENDING',
      product_url: 'https://new.example.com',
    }
    
    vi.mocked(api.post).mockResolvedValueOnce({ data: newCampaign })

    const { result } = renderHook(() => useCreateCampaign(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      title: 'New Campaign',
      product_url: 'https://new.example.com',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.post).toHaveBeenCalledWith('/campaigns', {
      title: 'New Campaign',
      product_url: 'https://new.example.com',
    })
  })
})
