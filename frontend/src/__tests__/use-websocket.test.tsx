import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useWebSocket } from '@/hooks/use-websocket'

// Mock the API module
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] }),
  },
}))

describe('useWebSocket', () => {
  let mockWebSocket: {
    onopen: (() => void) | null
    onclose: (() => void) | null
    onmessage: ((event: { data: string }) => void) | null
    onerror: ((event: Event) => void) | null
    send: ReturnType<typeof vi.fn>
    close: ReturnType<typeof vi.fn>
    readyState: number
  }

  beforeEach(() => {
    vi.useFakeTimers()
    
    mockWebSocket = {
      onopen: null,
      onclose: null,
      onmessage: null,
      onerror: null,
      send: vi.fn(),
      close: vi.fn(),
      readyState: 1,
    }

    vi.stubGlobal('WebSocket', vi.fn(() => mockWebSocket))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('connects to WebSocket on mount', async () => {
    renderHook(() => useWebSocket(123))

    expect(WebSocket).toHaveBeenCalledWith(expect.stringContaining('/ws/logs/123'))
  })

  it('sets isConnected to true when connection opens', async () => {
    const { result } = renderHook(() => useWebSocket(123))

    act(() => {
      mockWebSocket.onopen?.()
    })

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })
  })

  it('adds logs when receiving agent_log messages', async () => {
    const { result } = renderHook(() => useWebSocket(123))

    act(() => {
      mockWebSocket.onopen?.()
    })

    act(() => {
      mockWebSocket.onmessage?.({
        data: JSON.stringify({
          type: 'agent_log',
          agent_name: 'ResearchAgent',
          message: 'Analyzing product...',
          level: 'INFO',
        }),
      })
    })

    await waitFor(() => {
      expect(result.current.logs.length).toBeGreaterThan(0)
    })

    const lastLog = result.current.logs[result.current.logs.length - 1]
    expect(lastLog.agent_name).toBe('ResearchAgent')
    expect(lastLog.message).toBe('Analyzing product...')
  })

  it('sends ping every 30 seconds', async () => {
    renderHook(() => useWebSocket(123))

    act(() => {
      mockWebSocket.onopen?.()
    })

    // Advance time by 30 seconds
    act(() => {
      vi.advanceTimersByTime(30000)
    })

    expect(mockWebSocket.send).toHaveBeenCalledWith('ping')
  })

  it('sets error on connection error', async () => {
    const { result } = renderHook(() => useWebSocket(123))

    act(() => {
      mockWebSocket.onerror?.(new Event('error'))
    })

    await waitFor(() => {
      expect(result.current.error).toBeDefined()
    })
  })

  it('sets isConnected to false on close', async () => {
    const { result } = renderHook(() => useWebSocket(123))

    act(() => {
      mockWebSocket.onopen?.()
    })

    expect(result.current.isConnected).toBe(true)

    act(() => {
      mockWebSocket.onclose?.()
    })

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false)
    })
  })
})
