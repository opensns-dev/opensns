import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useSettings, useUpdateSettings } from '@/hooks/use-settings'
import type { ReactNode } from 'react'

// Mock the API module
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
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

describe('useSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches settings successfully', async () => {
    const mockSettings = {
      default_llm_engine: 'openai',
      default_image_engine: 'fal',
      default_video_engine: 'fal-video',
      ollama_url: null,
      comfyui_url: null,
      has_openai_key: true,
      has_fal_key: false,
    }
    
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockSettings })

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSettings)
    expect(api.get).toHaveBeenCalledWith('/settings')
  })

  it('handles fetch error', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Unauthorized'))

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useUpdateSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('updates settings successfully', async () => {
    const updatedSettings = {
      default_llm_engine: 'ollama',
      default_image_engine: 'comfyui',
      default_video_engine: 'fal-video',
      ollama_url: 'http://localhost:11434',
      comfyui_url: 'http://localhost:8188',
      has_openai_key: true,
      has_fal_key: true,
    }
    
    vi.mocked(api.put).mockResolvedValueOnce({ data: updatedSettings })

    const { result } = renderHook(() => useUpdateSettings(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      default_llm_engine: 'ollama',
      ollama_url: 'http://localhost:11434',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.put).toHaveBeenCalledWith('/settings', {
      default_llm_engine: 'ollama',
      ollama_url: 'http://localhost:11434',
    })
  })

  it('updates API keys', async () => {
    const updatedSettings = {
      default_llm_engine: 'openai',
      default_image_engine: 'fal',
      default_video_engine: 'fal-video',
      ollama_url: null,
      comfyui_url: null,
      has_openai_key: true,
      has_fal_key: false,
    }
    
    vi.mocked(api.put).mockResolvedValueOnce({ data: updatedSettings })

    const { result } = renderHook(() => useUpdateSettings(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      openai_api_key: 'sk-test-key',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.put).toHaveBeenCalledWith('/settings', {
      openai_api_key: 'sk-test-key',
    })
  })
})
