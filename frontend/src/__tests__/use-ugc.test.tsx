/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
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
import { useUGCEngines, useAvatars, useVoices } from '@/hooks/use-ugc'

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

describe('useUGCEngines', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches UGC engines successfully', async () => {
    const mockEngines = {
      engines: [
        { engine: 'heygen', name: 'HeyGen', supports_ugc: true, requires_api_key: true, has_api_key: true },
        { engine: 'did', name: 'D-ID', supports_ugc: true, requires_api_key: true, has_api_key: false },
      ],
      default_engine: 'heygen',
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockEngines })

    const { result } = renderHook(() => useUGCEngines(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockEngines)
    expect(api.get).toHaveBeenCalledWith('/ugc/engines')
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useUGCEngines(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useAvatars', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches avatars with default engine "heygen"', async () => {
    const mockAvatars = {
      avatars: [
        { avatar_id: 'avatar1', name: 'Avatar 1', preview_url: 'https://example.com/avatar1.jpg', gender: 'female', style: 'professional' },
        { avatar_id: 'avatar2', name: 'Avatar 2', preview_url: 'https://example.com/avatar2.jpg', gender: 'male', style: 'casual' },
      ],
      engine: 'heygen',
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockAvatars })

    const { result } = renderHook(() => useAvatars(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockAvatars)
    expect(api.get).toHaveBeenCalledWith('/ugc/avatars', { params: { engine: 'heygen' } })
  })

  it('fetches avatars with custom engine param', async () => {
    const mockAvatars = {
      avatars: [
        { avatar_id: 'avatar3', name: 'Avatar 3', preview_url: 'https://example.com/avatar3.jpg', gender: 'female', style: 'professional' },
      ],
      engine: 'did',
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockAvatars })

    const { result } = renderHook(() => useAvatars('did'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockAvatars)
    expect(api.get).toHaveBeenCalledWith('/ugc/avatars', { params: { engine: 'did' } })
  })

  it('does not fetch when engine is empty', () => {
    const { result } = renderHook(() => useAvatars(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('useVoices', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches voices with default engine "heygen"', async () => {
    const mockVoices = {
      voices: [
        { voice_id: 'voice1', name: 'Voice 1', language: 'en', gender: 'female', preview_url: 'https://example.com/voice1.mp3' },
        { voice_id: 'voice2', name: 'Voice 2', language: 'ko', gender: 'male', preview_url: 'https://example.com/voice2.mp3' },
      ],
      engine: 'heygen',
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockVoices })

    const { result } = renderHook(() => useVoices(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockVoices)
    expect(api.get).toHaveBeenCalledWith('/ugc/voices', { params: { engine: 'heygen' } })
  })

  it('fetches voices with custom engine param', async () => {
    const mockVoices = {
      voices: [
        { voice_id: 'voice3', name: 'Voice 3', language: 'en', gender: 'female', preview_url: 'https://example.com/voice3.mp3' },
      ],
      engine: 'did',
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockVoices })

    const { result } = renderHook(() => useVoices('did'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockVoices)
    expect(api.get).toHaveBeenCalledWith('/ugc/voices', { params: { engine: 'did' } })
  })

  it('does not fetch when engine is empty', () => {
    const { result } = renderHook(() => useVoices(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(api.get).not.toHaveBeenCalled()
  })
})
