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
import {
  useRepurposeJobs,
  useRepurposeJob,
  useRepurposeContents,
  useCreateRepurposeJob,
  useDeleteRepurposeJob,
} from '@/hooks/use-repurpose'

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

describe('useRepurposeJobs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches repurpose jobs successfully', async () => {
    const mockJobs = [
      { id: 1, youtube_url: 'https://youtube.com/watch?v=123', video_title: 'Test Video', video_duration: 120, status: 'COMPLETED', tone_style: 'CASUAL', target_platforms: ['X_THREAD'], transcript: 'test', summary: 'summary', key_points: ['point1'], error: null, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { id: 2, youtube_url: 'https://youtube.com/watch?v=456', video_title: 'Another Video', video_duration: 180, status: 'PENDING', tone_style: 'FORMAL', target_platforms: ['NAVER_BLOG'], transcript: null, summary: null, key_points: null, error: null, created_at: '2024-01-02', updated_at: '2024-01-02' },
    ]

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockJobs })

    const { result } = renderHook(() => useRepurposeJobs(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockJobs)
    expect(api.get).toHaveBeenCalledWith('/repurpose/')
  })

  it('handles fetch error', async () => {
    ;(api.get as Mock).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useRepurposeJobs(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })
})

describe('useRepurposeJob', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches single repurpose job', async () => {
    const mockJob = {
      id: 1,
      youtube_url: 'https://youtube.com/watch?v=123',
      video_title: 'Test Video',
      video_duration: 120,
      status: 'COMPLETED',
      tone_style: 'CASUAL',
      target_platforms: ['X_THREAD'],
      transcript: 'test',
      summary: 'summary',
      key_points: ['point1'],
      error: null,
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    }

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockJob })

    const { result } = renderHook(() => useRepurposeJob(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockJob)
    expect(api.get).toHaveBeenCalledWith('/repurpose/1')
  })

  it('does not fetch when id is 0', () => {
    const { result } = renderHook(() => useRepurposeJob(0), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('useRepurposeContents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches repurpose contents successfully', async () => {
    const mockContents = [
      { id: 1, job_id: 1, platform: 'X_THREAD', content: 'Tweet content', content_metadata: {}, created_at: '2024-01-01' },
      { id: 2, job_id: 1, platform: 'NAVER_BLOG', content: 'Blog post content', content_metadata: {}, created_at: '2024-01-01' },
    ]

    ;(api.get as Mock).mockResolvedValueOnce({ data: mockContents })

    const { result } = renderHook(() => useRepurposeContents(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockContents)
    expect(api.get).toHaveBeenCalledWith('/repurpose/1/contents')
  })

  it('does not fetch when jobId is 0', () => {
    const { result } = renderHook(() => useRepurposeContents(0), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('useCreateRepurposeJob', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates repurpose job successfully', async () => {
    const newJob = {
      id: 3,
      youtube_url: 'https://youtube.com/watch?v=789',
      video_title: null,
      video_duration: null,
      status: 'PENDING',
      tone_style: 'FRIENDLY',
      target_platforms: ['INSTAGRAM'],
      transcript: null,
      summary: null,
      key_points: null,
      error: null,
      created_at: '2024-01-03',
      updated_at: '2024-01-03',
    }

    ;(api.post as Mock).mockResolvedValueOnce({ data: newJob })

    const { result } = renderHook(() => useCreateRepurposeJob(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      youtube_url: 'https://youtube.com/watch?v=789',
      tone_style: 'FRIENDLY',
      target_platforms: ['INSTAGRAM'],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.post).toHaveBeenCalledWith('/repurpose/', {
      youtube_url: 'https://youtube.com/watch?v=789',
      tone_style: 'FRIENDLY',
      target_platforms: ['INSTAGRAM'],
    })
  })
})

describe('useDeleteRepurposeJob', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('deletes repurpose job successfully', async () => {
    ;(api.delete as Mock).mockResolvedValueOnce({})

    const { result } = renderHook(() => useDeleteRepurposeJob(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.delete).toHaveBeenCalledWith('/repurpose/1')
  })
})
